#!/usr/bin/env python
"""Inspect a PPTX template and emit lightweight JSON metadata."""

from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


NS = {
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}


def _text(node: ET.Element, path: str) -> str | None:
    found = node.find(path, NS)
    return found.text if found is not None else None


def _emu_to_inches(value: str | None) -> float | None:
    if value is None:
        return None
    return round(int(value) / 914400, 4)


def _parse_presentation(zf: zipfile.ZipFile) -> dict:
    root = ET.fromstring(zf.read("ppt/presentation.xml"))
    size = root.find("p:sldSz", NS)
    slide_ids = root.findall("p:sldIdLst/p:sldId", NS)
    return {
        "slide_count": len(slide_ids),
        "slide_size": {
            "cx_emu": int(size.attrib["cx"]) if size is not None else None,
            "cy_emu": int(size.attrib["cy"]) if size is not None else None,
            "width_in": _emu_to_inches(size.attrib.get("cx")) if size is not None else None,
            "height_in": _emu_to_inches(size.attrib.get("cy")) if size is not None else None,
            "type": size.attrib.get("type") if size is not None else None,
        },
    }


def _parse_layout(zf: zipfile.ZipFile, name: str) -> dict:
    root = ET.fromstring(zf.read(name))
    c_sld = root.find("p:cSld", NS)
    layout_name = c_sld.attrib.get("name") if c_sld is not None else Path(name).stem
    placeholders = []
    for sp in root.findall(".//p:sp", NS):
        nv = sp.find("p:nvSpPr/p:nvPr/p:ph", NS)
        c_nv = sp.find("p:nvSpPr/p:cNvPr", NS)
        if nv is None:
            continue
        xfrm = sp.find("p:spPr/a:xfrm", NS)
        off = xfrm.find("a:off", NS) if xfrm is not None else None
        ext = xfrm.find("a:ext", NS) if xfrm is not None else None
        placeholders.append(
            {
                "name": c_nv.attrib.get("name") if c_nv is not None else None,
                "type": nv.attrib.get("type", "body"),
                "idx": nv.attrib.get("idx"),
                "x_in": _emu_to_inches(off.attrib.get("x")) if off is not None else None,
                "y_in": _emu_to_inches(off.attrib.get("y")) if off is not None else None,
                "w_in": _emu_to_inches(ext.attrib.get("cx")) if ext is not None else None,
                "h_in": _emu_to_inches(ext.attrib.get("cy")) if ext is not None else None,
            }
        )
    return {"path": name, "name": layout_name, "placeholders": placeholders}


def inspect(path: Path) -> dict:
    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()
        layouts = sorted(n for n in names if n.startswith("ppt/slideLayouts/slideLayout") and n.endswith(".xml"))
        masters = sorted(n for n in names if n.startswith("ppt/slideMasters/slideMaster") and n.endswith(".xml"))
        metadata = {
            "path": str(path),
            "file_size_bytes": path.stat().st_size,
            "presentation": _parse_presentation(zf),
            "master_count": len(masters),
            "layout_count": len(layouts),
            "layouts": [_parse_layout(zf, name) for name in layouts],
        }
    return metadata


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pptx", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    data = inspect(args.pptx)
    rendered = json.dumps(data, ensure_ascii=False, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
