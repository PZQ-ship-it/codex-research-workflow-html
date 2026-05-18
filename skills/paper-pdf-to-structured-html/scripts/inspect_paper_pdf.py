#!/usr/bin/env python3
"""Inspect a research PDF and write extraction artifacts for an HTML digest.

Optional dependencies:
  - pymupdf (`fitz`) for metadata, outlines, text, and image extraction
  - pdfplumber for alternate text extraction

The script is intentionally conservative. It gathers evidence for Codex to use;
it does not try to write the final interpretive HTML by itself.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


CAPTION_RE = re.compile(r"(?im)^\s*((fig(?:ure)?|table)\s*\.?\s*\d+[a-z]?)\s*[:.\-]?\s+(.{8,500})")
REFERENCE_HEADER_RE = re.compile(r"(?im)^\s*(references|bibliography)\s*$")


def slugify(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip("-")
    return value.lower() or "paper"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def import_fitz():
    try:
        import fitz  # type: ignore

        return fitz
    except Exception:
        return None


def import_pdfplumber():
    try:
        import pdfplumber  # type: ignore

        return pdfplumber
    except Exception:
        return None


def extract_with_fitz(pdf_path: Path, out_dir: Path, max_images: int) -> dict[str, Any]:
    fitz = import_fitz()
    if fitz is None:
        return {"available": False, "error": "pymupdf is not installed"}

    image_dir = out_dir / "assets"
    image_dir.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(pdf_path)
    pages: list[dict[str, Any]] = []
    images: list[dict[str, Any]] = []

    for page_index in range(len(doc)):
        page = doc[page_index]
        text = page.get_text("text") or ""
        page_record: dict[str, Any] = {
            "page": page_index + 1,
            "text_path": f"pages/page-{page_index + 1:03d}.txt",
            "char_count": len(text),
            "candidate_captions": [
                {"label": m.group(1), "kind": m.group(2).lower(), "text": m.group(3).strip()}
                for m in CAPTION_RE.finditer(text)
            ],
        }
        pages.append(page_record)

        if len(images) < max_images:
            for img_index, img in enumerate(page.get_images(full=True), start=1):
                if len(images) >= max_images:
                    break
                xref = img[0]
                try:
                    extracted = doc.extract_image(xref)
                except Exception as exc:
                    images.append(
                        {
                            "page": page_index + 1,
                            "xref": xref,
                            "error": str(exc),
                        }
                    )
                    continue
                ext = extracted.get("ext", "png")
                filename = f"page-{page_index + 1:03d}-image-{img_index:02d}.{ext}"
                target = image_dir / filename
                target.write_bytes(extracted["image"])
                images.append(
                    {
                        "page": page_index + 1,
                        "file": f"assets/{filename}",
                        "width": extracted.get("width"),
                        "height": extracted.get("height"),
                        "colorspace": extracted.get("colorspace"),
                        "xref": xref,
                    }
                )

    outline = []
    try:
        outline = [
            {"level": item[0], "title": item[1], "page": item[2]}
            for item in doc.get_toc(simple=True)
        ]
    except Exception:
        outline = []

    metadata = dict(doc.metadata or {})
    page_count = len(doc)
    doc.close()
    return {
        "available": True,
        "metadata": metadata,
        "page_count": page_count,
        "outline": outline,
        "pages": pages,
        "images": images,
    }


def extract_text_pages(pdf_path: Path, out_dir: Path, fitz_result: dict[str, Any]) -> list[dict[str, Any]]:
    pages_dir = out_dir / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)

    fitz = import_fitz()
    if fitz is not None:
        doc = fitz.open(pdf_path)
        records = []
        for page_index in range(len(doc)):
            text = doc[page_index].get_text("text") or ""
            text_path = pages_dir / f"page-{page_index + 1:03d}.txt"
            text_path.write_text(text, encoding="utf-8")
            records.append({"page": page_index + 1, "text_path": str(text_path.relative_to(out_dir)), "char_count": len(text)})
        doc.close()
        return records

    pdfplumber = import_pdfplumber()
    if pdfplumber is not None:
        records = []
        with pdfplumber.open(pdf_path) as pdf:
            for page_index, page in enumerate(pdf.pages, start=1):
                text = page.extract_text() or ""
                text_path = pages_dir / f"page-{page_index:03d}.txt"
                text_path.write_text(text, encoding="utf-8")
                records.append({"page": page_index, "text_path": str(text_path.relative_to(out_dir)), "char_count": len(text)})
        return records

    return fitz_result.get("pages", [])


def collect_text(out_dir: Path, pages: list[dict[str, Any]]) -> str:
    chunks = []
    for page in pages:
        text_path = out_dir / page["text_path"]
        if text_path.exists():
            chunks.append(text_path.read_text(encoding="utf-8", errors="replace"))
    return "\n".join(chunks)


def guess_paper_type(text: str) -> dict[str, Any]:
    lowered = text[:30000].lower()
    signals = {
        "survey": [
            "survey",
            "review",
            "taxonomy",
            "comprehensive overview",
            "future directions",
            "challenges and opportunities",
        ],
        "algorithm_method": [
            "we propose",
            "our method",
            "algorithm",
            "architecture",
            "loss function",
            "training objective",
            "ablation",
        ],
        "empirical_benchmark": [
            "benchmark",
            "evaluation protocol",
            "datasets",
            "baselines",
            "leaderboard",
            "empirical study",
        ],
        "system_dataset": [
            "system",
            "toolkit",
            "dataset",
            "corpus",
            "annotation",
            "implementation",
            "deployment",
        ],
    }
    scores = {kind: sum(1 for signal in words if signal in lowered) for kind, words in signals.items()}
    best = max(scores, key=scores.get)
    confidence = "low"
    if scores[best] >= 4:
        confidence = "medium"
    if scores[best] >= 7:
        confidence = "high"
    if scores[best] == 0:
        best = "unclear"
    return {"type": best, "confidence": confidence, "scores": scores}


def extract_references(text: str, limit: int) -> list[str]:
    match = REFERENCE_HEADER_RE.search(text)
    if not match:
        return []
    ref_text = text[match.end() :]
    candidates = re.split(r"\n(?=\s*(?:\[\d+\]|\d+\.|\w.+\(\d{4}\)))", ref_text)
    cleaned = [" ".join(c.split()) for c in candidates if len(c.strip()) > 40]
    return cleaned[:limit]


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect a research PDF for structured HTML conversion.")
    parser.add_argument("pdf", type=Path, help="Path to the source PDF")
    parser.add_argument("--out", type=Path, required=True, help="Output directory for manifest, text, and images")
    parser.add_argument("--max-images", type=int, default=80, help="Maximum embedded images to extract")
    parser.add_argument("--max-references", type=int, default=80, help="Maximum reference strings to keep in manifest")
    args = parser.parse_args()

    pdf_path = args.pdf.resolve()
    if not pdf_path.exists():
        print(f"PDF not found: {pdf_path}", file=sys.stderr)
        return 2

    out_dir = args.out.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    fitz_result = extract_with_fitz(pdf_path, out_dir, args.max_images)
    pages = extract_text_pages(pdf_path, out_dir, fitz_result)
    full_text = collect_text(out_dir, pages)
    captions = [
        {"page": page["page"], "label": m.group(1), "kind": m.group(2).lower(), "text": m.group(3).strip()}
        for page in pages
        for m in CAPTION_RE.finditer((out_dir / page["text_path"]).read_text(encoding="utf-8", errors="replace"))
    ]

    manifest = {
        "source_pdf": str(pdf_path),
        "source_sha256": sha256_file(pdf_path),
        "suggested_slug": slugify(pdf_path.stem),
        "dependencies": {
            "pymupdf": bool(import_fitz()),
            "pdfplumber": bool(import_pdfplumber()),
        },
        "fitz": {k: v for k, v in fitz_result.items() if k not in {"pages"}},
        "pages": pages,
        "candidate_captions": captions,
        "paper_type_guess": guess_paper_type(full_text),
        "references": extract_references(full_text, args.max_references),
        "manual_check": [
            "Confirm paper type and section boundaries.",
            "Confirm table values against rendered PDF pages.",
            "Select only figures that help reading; embedded images may include logos or fragments.",
        ],
    }

    manifest_path = out_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {manifest_path}")
    print(f"Pages: {len(pages)}")
    print(f"Candidate captions: {len(captions)}")
    print(f"Extracted images: {len(manifest['fitz'].get('images', [])) if isinstance(manifest.get('fitz'), dict) else 0}")
    print(f"Paper type guess: {manifest['paper_type_guess']['type']} ({manifest['paper_type_guess']['confidence']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
