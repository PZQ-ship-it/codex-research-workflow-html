"""Rebuild safe text pages as two columns through BabelDOC's IL pipeline.

This is an opt-in experimental backend. It deliberately uses BabelDOC's
internal APIs, so the selected interpreter and BabelDOC version are recorded
in the manifest and a version drift is treated as a review gate.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


EXPERIMENTAL = True
SAFE_LAYOUT_LABELS = {"plain text", "title"}
OBSTACLE_LABELS = {
    "figure",
    "figure_caption",
    "table",
    "table_caption",
    "equation",
    "formula",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def locate_babeldoc_python(explicit: str | None) -> str | None:
    candidates = [explicit, os.environ.get("BABELDOC_PYTHON"), sys.executable]
    for candidate in candidates:
        if not candidate:
            continue
        path = shutil.which(candidate) or candidate
        if not Path(path).exists():
            continue
        probe = subprocess.run(
            [path, "-c", "import babeldoc; print(babeldoc.__version__)"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if probe.returncode == 0:
            return str(Path(path).resolve())
    return None


def maybe_reexec(argv: list[str]) -> int | None:
    """Run this file in the requested BabelDOC interpreter when needed."""
    if os.environ.get("BABELDOC_REEXEC") == "1":
        return None
    explicit = None
    if "--python" in argv:
        index = argv.index("--python")
        if index + 1 < len(argv):
            explicit = argv[index + 1]
    if explicit is None and importlib.util.find_spec("babeldoc") is not None:
        return None
    selected = locate_babeldoc_python(explicit)
    if not selected or Path(selected).resolve() == Path(sys.executable).resolve():
        return None
    env = os.environ.copy()
    env["BABELDOC_REEXEC"] = "1"
    completed = subprocess.run([selected, __file__, *argv], env=env)
    return completed.returncode


def box_tuple(box: Any) -> tuple[float, float, float, float] | None:
    if not box:
        return None
    values = (box.x, box.y, box.x2, box.y2)
    if any(value is None for value in values):
        return None
    return tuple(float(value) for value in values)


def intersects(left: tuple[float, float, float, float], right: tuple[float, float, float, float]) -> bool:
    return not (left[2] <= right[0] or right[2] <= left[0] or left[3] <= right[1] or right[3] <= left[1])


def composition_count(composition: Any) -> int:
    if composition.pdf_line:
        return max(1, len(composition.pdf_line.pdf_character))
    if composition.pdf_same_style_characters:
        return max(1, len(composition.pdf_same_style_characters.pdf_character))
    if composition.pdf_same_style_unicode_characters:
        return max(1, len(composition.pdf_same_style_unicode_characters.unicode or ""))
    if composition.pdf_character:
        return 1
    if composition.pdf_formula:
        return max(4, len(composition.pdf_formula.pdf_character))
    return 0


def paragraph_count(paragraph: Any) -> int:
    return max(1, sum(composition_count(item) for item in paragraph.pdf_paragraph_composition))


def paragraph_label(paragraph: Any) -> str:
    return (paragraph.layout_label or "").strip().lower()


def layout_plan_for_page(page: Any, include_first_page: bool) -> dict[str, Any]:
    page_box = box_tuple(page.cropbox.box)
    if not page_box:
        return {"page": page.page_number + 1, "mode": "passthrough", "reason": "missing-cropbox", "_moved_objects": []}
    page_number = page.page_number + 1
    plan: dict[str, Any] = {
        "page": page_number,
        "mode": "passthrough",
        "reason": "not-selected",
        "moved_paragraphs": 0,
        "skipped_paragraphs": 0,
        "_moved_objects": [],
    }
    if page_number == 1 and not include_first_page:
        plan["reason"] = "first-page-top-matter-default"
        return plan

    obstacles = []
    for item in page.page_layout:
        if (item.class_name or "").lower() in OBSTACLE_LABELS:
            item_box = box_tuple(item.box)
            if item_box:
                obstacles.append({"label": item.class_name, "box": item_box})

    candidates = []
    for paragraph in page.pdf_paragraph:
        current = box_tuple(paragraph.box)
        if not current or paragraph_label(paragraph) not in SAFE_LAYOUT_LABELS:
            continue
        if any(intersects(current, obstacle["box"]) for obstacle in obstacles):
            continue
        candidates.append((paragraph, current))

    if len(candidates) < 2:
        plan["reason"] = "no-safe-body-paragraphs"
        return plan

    left = min(item[1][0] for item in candidates)
    right = max(item[1][2] for item in candidates)
    body_top = min(page_box[3] - 18.0, max(item[1][3] for item in candidates) + 3.0)
    body_bottom = max(page_box[1] + 24.0, min(item[1][1] for item in candidates) - 3.0)
    gutter = max(12.0, (right - left) * 0.035)
    column_width = (right - left - gutter) / 2.0
    if column_width < 120 or body_top - body_bottom < 120:
        plan["reason"] = "body-region-too-small"
        return plan

    sorted_candidates = sorted(candidates, key=lambda item: (-item[1][3], item[1][0]))
    changed = [
        {
            "layout_label": paragraph_label(paragraph),
            "source_box": original,
            "character_count": paragraph_count(paragraph),
        }
        for paragraph, original in sorted_candidates
    ]
    plan["_moved_objects"] = [paragraph for paragraph, _ in sorted_candidates]
    plan.update(
        {
            "mode": "candidate",
            "reason": "pending-page-flow",
            "moved_paragraphs": len(changed),
            "region": {"left": left, "bottom": body_bottom, "right": right, "top": body_top, "gutter": gutter},
            "paragraphs": changed,
            "obstacles": obstacles,
        }
    )
    return plan


def render_pages(pdf_path: Path, render_dir: Path, pages: list[int]) -> list[str]:
    try:
        import pymupdf
    except ImportError:
        return []
    render_dir.mkdir(parents=True, exist_ok=True)
    rendered = []
    document = pymupdf.open(pdf_path)
    try:
        for number in pages:
            if number < 1 or number > document.page_count:
                continue
            target = render_dir / f"page-{number:04d}.png"
            pixmap = document[number - 1].get_pixmap(matrix=pymupdf.Matrix(1.5, 1.5), alpha=False)
            pixmap.save(target)
            rendered.append(str(target))
    finally:
        document.close()
    return rendered


def output_qa(source: Path, output: Path, source_digest: str) -> dict[str, Any]:
    try:
        import pymupdf
    except ImportError:
        return {"passed": False, "reason": "pymupdf-unavailable"}
    source_doc = pymupdf.open(source)
    output_doc = pymupdf.open(output)
    try:
        source_rects = [tuple(round(value, 2) for value in page.rect) for page in source_doc]
        output_rects = [tuple(round(value, 2) for value in page.rect) for page in output_doc]
        output_text_counts = [len(page.get_text("words")) for page in output_doc]
        passed = (
            source_digest == sha256(source)
            and source_doc.page_count == output_doc.page_count
            and source_rects == output_rects
            and all(count > 0 for count in output_text_counts)
        )
        return {
            "passed": passed,
            "source_pages": source_doc.page_count,
            "output_pages": output_doc.page_count,
            "page_sizes_match": source_rects == output_rects,
            "output_word_counts": output_text_counts,
            "source_unchanged": source_digest == sha256(source),
        }
    finally:
        source_doc.close()
        output_doc.close()


def convert(args: argparse.Namespace) -> int:
    source = Path(args.input).expanduser().resolve()
    output_dir = Path(args.output).expanduser().resolve()
    if not source.is_file() or source.suffix.lower() != ".pdf":
        raise SystemExit(f"input must be an existing PDF: {source}")
    output_dir.mkdir(parents=True, exist_ok=True)
    destination = output_dir / f"{source.stem}_2col.pdf"
    manifest_path = output_dir / "manifest.json"
    if destination.exists() and not args.overwrite:
        raise SystemExit(f"output exists; pass --overwrite: {destination}")

    started = time.time()
    manifest: dict[str, Any] = {
        "status": "failed",
        "experimental": EXPERIMENTAL,
        "backend": "babeldoc-il-typesetting",
        "input": str(source),
        "output": str(destination),
        "source_sha256": sha256(source),
        "pages_requested": args.pages,
        "include_first_page": args.include_first_page,
        "font_scale": args.font_scale,
    }
    try:
        from babeldoc.docvision.doclayout import DocLayoutModel
        from babeldoc.format.pdf import high_level
        from babeldoc.format.pdf.document_il.midend.typesetting import Typesetting, TypesettingUnit
        from babeldoc.format.pdf.translation_config import TranslationConfig, WatermarkOutputMode

        plans: list[dict[str, Any]] = []

        class ColumnTypesetting(Typesetting):
            def _create_flow_units(self, paragraph: Any, fonts: dict[Any, Any]) -> list[Any]:
                """Mirror BabelDOC's unit creation, avoiding its stale debug_info field."""
                result = []

                def get_font(font_id: Any, xobj_id: Any):
                    if xobj_id in fonts:
                        return fonts[xobj_id][font_id]
                    return fonts[font_id]

                for composition in paragraph.pdf_paragraph_composition:
                    if composition.pdf_line:
                        result.extend(TypesettingUnit(char=char) for char in composition.pdf_line.pdf_character)
                    elif composition.pdf_character:
                        result.append(TypesettingUnit(char=composition.pdf_character, debug_info=False))
                    elif composition.pdf_same_style_characters:
                        result.extend(TypesettingUnit(char=char) for char in composition.pdf_same_style_characters.pdf_character)
                    elif composition.pdf_same_style_unicode_characters:
                        style = composition.pdf_same_style_unicode_characters.pdf_style
                        if not style or not style.font_id:
                            continue
                        font = get_font(style.font_id, paragraph.xobj_id)
                        for char_unicode in composition.pdf_same_style_unicode_characters.unicode or "":
                            if char_unicode == "\n":
                                continue
                            result.append(
                                TypesettingUnit(
                                    unicode=char_unicode,
                                    font=self.font_mapper.map(font, char_unicode),
                                    original_font=font,
                                    font_size=style.font_size,
                                    style=style,
                                    xobj_id=paragraph.xobj_id,
                                    debug_info=bool(composition.pdf_same_style_unicode_characters.debug_info),
                                )
                            )
                    elif composition.pdf_formula:
                        result.append(TypesettingUnit(formular=composition.pdf_formula))
                result = [unit for unit in result if unit.unicode is None or unit.font is not None]
                for unit in result:
                    if unit.char and unit.char.advance:
                        if float(unit.char.advance) > max(float(unit.width) * 1.18, float(unit.width) + 1.2):
                            unit._flow_break_after = True
                return result

            def _fonts_for_page(self, page: Any) -> dict[Any, Any]:
                fonts = {font.font_id: font for font in page.pdf_font if font.font_id}
                page_fonts = {font.font_id: font for font in page.pdf_font if font.font_id}
                for key, value in self.font_mapper.fontid2font.items():
                    fonts[key] = value
                for xobj in page.pdf_xobject:
                    if xobj.xobj_id is not None:
                        fonts[xobj.xobj_id] = page_fonts.copy()
                        for font in xobj.pdf_font:
                            if font.font_id:
                                fonts[xobj.xobj_id][font.font_id] = font
                return fonts

            def _tokens(self, units: list[Any]) -> list[list[Any]]:
                tokens: list[list[Any]] = []
                current: list[Any] = []
                for unit in units:
                    if unit.is_cjk_char:
                        if current:
                            tokens.append(current)
                            current = []
                        tokens.append([unit])
                    elif unit.is_space:
                        if current:
                            tokens.append(current)
                            current = []
                        tokens.append([unit])
                    else:
                        current.append(unit)
                        if getattr(unit, "_flow_break_after", False):
                            tokens.append(current)
                            current = []
                if current:
                    tokens.append(current)
                return tokens

            @staticmethod
            def _unit_advance(unit: Any, scale: float) -> float:
                if getattr(unit, "_flow_break_after", False):
                    font_size = float(unit.font_size or unit.height)
                    source_gap = 0.0
                    if unit.char and unit.char.advance:
                        source_gap = max(0.0, float(unit.char.advance) - float(unit.width))
                    return (float(unit.width) + max(font_size * 0.28, source_gap)) * scale
                if unit.char and unit.char.advance:
                    return max(float(unit.width), float(unit.char.advance)) * scale
                return float(unit.width) * scale

            def _create_flow_compositions(self, units: list[Any]) -> list[Any]:
                from babeldoc.format.pdf.document_il import il_version_1

                compositions = []
                for unit in units:
                    if unit.unicode:
                        chars, _, _ = unit.render()
                        compositions.extend(
                            il_version_1.PdfParagraphComposition(pdf_character=char)
                            for char in chars
                        )
                    elif unit.formular:
                        compositions.append(il_version_1.PdfParagraphComposition(pdf_formula=unit.formular))
                    else:
                        chars, _, _ = unit.passthrough()
                        compositions.extend(
                            il_version_1.PdfParagraphComposition(pdf_character=char)
                            for char in chars
                        )
                return compositions

            def _flow_page(self, page: Any, plan: dict[str, Any], paragraphs: list[Any], fonts: dict[Any, Any], scale: float) -> bool:
                region = plan.get("region") or {}
                left = float(region["left"])
                right = float(region["right"])
                bottom = float(region["bottom"])
                top = float(region["top"])
                gutter = float(region["gutter"])
                column_width = (right - left - gutter) / 2.0
                columns = [(left, left + column_width), (left + column_width + gutter, right)]
                column_index = 0
                current_y = top
                line_units: list[Any] = []
                line_width = 0.0
                line_indent = 0.0
                relocated_by_paragraph: dict[int, list[Any]] = {id(item): [] for item in paragraphs}

                def flush_line() -> None:
                    nonlocal column_index, current_y, line_units, line_width, line_indent
                    if not line_units:
                        return
                    heights = [max(1.0, float(unit.height) * scale) for unit in line_units]
                    font_sizes = [
                        float(unit.font_size) * scale
                        for unit in line_units
                        if unit.font_size
                    ]
                    line_height = max(max(heights), (max(font_sizes) if font_sizes else 8.0) * 0.95)
                    line_advance = max(line_height * 1.12, (max(font_sizes) if font_sizes else 8.0) * 1.05)
                    if current_y - line_advance < bottom:
                        column_index += 1
                        current_y = top
                        if column_index >= 2:
                            raise OverflowError("page text does not fit in two columns")
                    x = columns[column_index][0] + line_indent
                    y = current_y - line_height
                    for unit in line_units:
                        relocated = unit.relocate(x, y + max(0.0, line_height - unit.height * scale), scale)
                        owner = getattr(unit, "_flow_owner", None)
                        if owner is None:
                            raise RuntimeError("flow unit lost paragraph owner")
                        relocated_by_paragraph[id(owner)].append(relocated)
                        x += self._unit_advance(unit, scale)
                    current_y -= line_advance
                    line_units = []
                    line_width = 0.0
                    line_indent = 0.0

                groups: list[list[Any]] = []
                for paragraph in paragraphs:
                    if groups and paragraph_label(paragraph) == "title" and paragraph_label(groups[-1][-1]) == "title":
                        previous_box = box_tuple(groups[-1][-1].box)
                        current_box = box_tuple(paragraph.box)
                        if previous_box and current_box and not (previous_box[3] <= current_box[1] or current_box[3] <= previous_box[1]):
                            groups[-1].append(paragraph)
                            continue
                    groups.append([paragraph])

                for group in groups:
                    units = []
                    for paragraph in group:
                        paragraph_units = self._create_flow_units(paragraph, fonts)
                        for unit in paragraph_units:
                            unit._flow_owner = paragraph
                        units.extend(paragraph_units)
                    if line_units:
                        flush_line()
                    if units:
                        first_font_size = next((float(unit.font_size) * scale for unit in units if unit.font_size), 8.0 * scale)
                        current_y -= first_font_size * 0.35
                        if current_y <= bottom:
                            column_index += 1
                            current_y = top
                            if column_index >= 2:
                                raise OverflowError("paragraph gap does not fit in two columns")
                    first_line = True
                    for token in self._tokens(units):
                        token_width = sum(self._unit_advance(unit, scale) for unit in token)
                        if token and all(unit.is_space for unit in token):
                            if not line_units:
                                continue
                            if line_width + token_width > column_width:
                                flush_line()
                                continue
                            line_units.extend(token)
                            line_width += token_width
                            continue
                        if first_line and group[0].first_line_indent:
                            line_indent = first_font_size * 2.0
                        if token_width <= column_width and line_width + token_width + line_indent <= column_width:
                            line_units.extend(token)
                            line_width += token_width
                            first_line = False
                            continue
                        if line_units:
                            flush_line()
                        for unit in token:
                            unit_width = self._unit_advance(unit, scale)
                            if unit_width > column_width:
                                raise OverflowError("one glyph is wider than a column")
                            if line_units and line_width + unit_width > column_width:
                                flush_line()
                            line_units.append(unit)
                            line_width += unit_width
                            first_line = False
                    if line_units:
                        flush_line()
                    current_y -= 3.0
                if line_units:
                    flush_line()

                for paragraph in paragraphs:
                    relocated = relocated_by_paragraph[id(paragraph)]
                    if not relocated:
                        raise RuntimeError("empty relocated paragraph")
                    paragraph.pdf_paragraph_composition = self._create_flow_compositions(relocated)
                    self._update_paragraph_render_order(paragraph)
                return True

            def typesetting_document(self, document: Any):
                self.flow_pages: dict[int, tuple[dict[str, Any], list[Any]]] = {}
                self.flow_ids: set[int] = set()
                for page in document.page:
                    plan = layout_plan_for_page(page, args.include_first_page)
                    moved_objects = plan.pop("_moved_objects", [])
                    if moved_objects:
                        self.flow_pages[page.page_number + 1] = (plan, moved_objects)
                    plans.append(plan)
                return super().typesetting_document(document)

            def render_page(self, page: Any):
                flow = self.flow_pages.get(page.page_number + 1)
                if flow:
                    plan, paragraphs = flow
                    originals = {id(item): item.pdf_paragraph_composition for item in paragraphs}
                    try:
                        if self._flow_page(page, plan, paragraphs, self._fonts_for_page(page), args.font_scale):
                            self.flow_ids.update(id(item) for item in paragraphs)
                            source_boxes = [tuple(item["source_box"]) for item in plan.get("paragraphs", [])]
                            page.pdf_character = [
                                char
                                for char in page.pdf_character
                                if not any(
                                    (box_tuple(char.box) and intersects(box_tuple(char.box), source_box))
                                    for source_box in source_boxes
                                )
                            ]
                            plan.update({"mode": "two_column", "reason": "safe-page-flow", "moved_paragraphs": len(paragraphs), "font_scale": args.font_scale})
                        else:
                            raise RuntimeError("page flow returned false")
                    except Exception as exc:
                        for paragraph in paragraphs:
                            paragraph.pdf_paragraph_composition = originals[id(paragraph)]
                        self.flow_ids.difference_update(id(item) for item in paragraphs)
                        plan.update({"mode": "passthrough", "reason": f"page-flow-failed: {type(exc).__name__}", "moved_paragraphs": 0})
                        plan["flow_error"] = str(exc)
                return super().render_page(page)

            def render_paragraph(self, paragraph: Any, page: Any, fonts: Any):
                if id(paragraph) in getattr(self, "flow_ids", set()):
                    return
                return super().render_paragraph(paragraph, page, fonts)

        original_typesetting = high_level.Typesetting
        high_level.Typesetting = ColumnTypesetting
        try:
            config = TranslationConfig(
                None,
                source,
                args.lang_in,
                args.lang_in,
                DocLayoutModel.load_available(),
                pages=args.pages,
                output_dir=output_dir,
                working_dir=output_dir / "work",
                no_dual=True,
                watermark_output_mode=WatermarkOutputMode.NoWatermark,
                skip_scanned_detection=True,
                skip_translation=True,
                auto_extract_glossary=False,
                primary_font_family=args.primary_font_family,
                enable_graphic_element_process=True,
            )
            result = high_level.translate(config)
        finally:
            high_level.Typesetting = original_typesetting

        generated = getattr(result, "no_watermark_mono_pdf_path", None) or getattr(result, "mono_pdf_path", None)
        if not generated or not Path(generated).is_file():
            raise RuntimeError("BabelDOC returned no monolingual PDF")
        shutil.copy2(generated, destination)
        qa = output_qa(source, destination, manifest["source_sha256"])
        if not qa.get("passed"):
            raise RuntimeError(f"output QA failed: {qa}")
        rendered = render_pages(destination, output_dir / "render", args.render_pages)
        manifest.update(
            {
                "status": "ok",
                "babeldoc_version": getattr(__import__("babeldoc"), "__version__", "unknown"),
                "python": sys.executable,
                "output_sha256": sha256(destination),
                "qa": qa,
                "pages": plans,
                "two_column_pages": [item["page"] for item in plans if item["mode"] == "two_column"],
                "passthrough_pages": [item["page"] for item in plans if item["mode"] != "two_column"],
                "rendered_pages": rendered,
                "elapsed_seconds": round(time.time() - started, 3),
                "review_gate": "manual review required; pages with figures/tables/formulas remain passthrough",
            }
        )
    except Exception as exc:  # pragma: no cover - BabelDOC is optional and platform-specific
        manifest.update(
            {
                "error": f"{type(exc).__name__}: {exc}",
                "elapsed_seconds": round(time.time() - started, 3),
            }
        )
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(manifest, ensure_ascii=False, indent=2))
        return 1

    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


def doctor(args: argparse.Namespace) -> int:
    selected = locate_babeldoc_python(args.python)
    report: dict[str, Any] = {
        "backend": "babeldoc-il-typesetting",
        "available": bool(selected),
        "python": selected,
        "importable_in_current_process": importlib.util.find_spec("babeldoc") is not None,
    }
    if selected:
        probe = subprocess.run(
            [selected, "-c", "import babeldoc; print(babeldoc.__version__)"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        report["version"] = probe.stdout.strip()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if selected else 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    doctor_parser = subparsers.add_parser("doctor")
    doctor_parser.add_argument("--python", help="包含 babeldoc 的 Python 解释器")
    convert_parser = subparsers.add_parser("convert")
    convert_parser.add_argument("--input", required=True)
    convert_parser.add_argument("--output", required=True)
    convert_parser.add_argument("--python", help="包含 babeldoc 的 Python 解释器")
    convert_parser.add_argument("--pages", help="BabelDOC 页码表达式，例如 1-3")
    convert_parser.add_argument("--lang-in", default="en")
    convert_parser.add_argument("--font-scale", type=float, default=0.90, help="安全页正文缩放，范围 0.70-1.00")
    convert_parser.add_argument("--primary-font-family", choices=["serif", "sans-serif", "script"])
    convert_parser.add_argument("--include-first-page", action="store_true")
    convert_parser.add_argument("--render-pages", default="1,2,3", help="逗号分隔的代表页码")
    convert_parser.add_argument("--overwrite", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    reexec_result = maybe_reexec(argv)
    if reexec_result is not None:
        return reexec_result
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "doctor":
        return doctor(args)
    if not 0.70 <= args.font_scale <= 1.00:
        parser.error("--font-scale must be between 0.70 and 1.00")
    args.render_pages = [int(item.strip()) for item in args.render_pages.split(",") if item.strip()]
    return convert(args)


if __name__ == "__main__":
    raise SystemExit(main())
