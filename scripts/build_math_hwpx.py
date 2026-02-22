#!/usr/bin/env python3
"""Build a math worksheet HWPX document with equations in 2-column layout.

Generates math worksheets by:
1. Using the math-hwpx base template (2-column, optimized margins)
2. Generating section0.xml from problem data (JSON)
3. Embedding equations using hp:equation with Hancom equation script
4. Packaging as valid HWPX

Usage:
    # From JSON problem file
    python build_math_hwpx.py --problems problems.json --output worksheet.hwpx

    # With title and metadata
    python build_math_hwpx.py --problems problems.json \
        --title "중2 일차방정식 연습" --creator "수학교사" --output worksheet.hwpx

    # Custom section0.xml override (bypass problem generation)
    python build_math_hwpx.py --section my_section0.xml --output worksheet.hwpx

    # Custom header override
    python build_math_hwpx.py --problems p.json --header my_header.xml --output worksheet.hwpx

Problem JSON format:
    {
      "title": "중학교 2학년 일차방정식",
      "subtitle": "단원평가",
      "problems": [
        {
          "text": "다음 방정식을 풀어라.",
          "equation": "2x + 3 = 7",
          "choices": ["x = 1", "x = 2", "x = 3", "x = 4"],
          "sub_problems": [
            {"equation": "3x - 1 = 8"},
            {"text": "위 식에서 x의 값을 구하여라."}
          ]
        }
      ]
    }
"""

import argparse
import json
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape
from zipfile import ZIP_DEFLATED, ZIP_STORED, ZipFile

from lxml import etree

# Resolve paths relative to this script
SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
TEMPLATES_DIR = SKILL_DIR / "templates"
BASE_DIR = TEMPLATES_DIR / "base"

# HWPX namespaces
NS = {
    "hp": "http://www.hancom.co.kr/hwpml/2011/paragraph",
    "hs": "http://www.hancom.co.kr/hwpml/2011/section",
    "hc": "http://www.hancom.co.kr/hwpml/2011/core",
    "hh": "http://www.hancom.co.kr/hwpml/2011/head",
}

# All namespaces for section root
SEC_NAMESPACES = (
    'xmlns:ha="http://www.hancom.co.kr/hwpml/2011/app" '
    'xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph" '
    'xmlns:hp10="http://www.hancom.co.kr/hwpml/2016/paragraph" '
    'xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section" '
    'xmlns:hc="http://www.hancom.co.kr/hwpml/2011/core" '
    'xmlns:hh="http://www.hancom.co.kr/hwpml/2011/head" '
    'xmlns:hhs="http://www.hancom.co.kr/hwpml/2011/history" '
    'xmlns:hm="http://www.hancom.co.kr/hwpml/2011/master-page" '
    'xmlns:hpf="http://www.hancom.co.kr/schema/2011/hpf" '
    'xmlns:dc="http://purl.org/dc/elements/1.1/" '
    'xmlns:opf="http://www.idpf.org/2007/opf/" '
    'xmlns:ooxmlchart="http://www.hancom.co.kr/hwpml/2016/ooxmlchart" '
    'xmlns:hwpunitchar="http://www.hancom.co.kr/hwpml/2016/HwpUnitChar" '
    'xmlns:epub="http://www.idpf.org/2007/ops" '
    'xmlns:config="urn:oasis:names:tc:opendocument:xmlns:config:1.0"'
)


class IDGen:
    """Sequential ID generator for HWPX elements."""
    def __init__(self, start=1000000001):
        self._next = start

    def next(self) -> str:
        val = self._next
        self._next += 1
        return str(val)

    def next_eq(self) -> str:
        """Equation-specific IDs (separate range)."""
        val = self._next
        self._next += 1
        return str(val)


def make_empty_para(idgen: IDGen, para_pr: int = 0, char_pr: int = 0) -> str:
    """Generate an empty paragraph XML."""
    pid = idgen.next()
    return (
        f'<hp:p id="{pid}" paraPrIDRef="{para_pr}" styleIDRef="0" '
        f'pageBreak="0" columnBreak="0" merged="0">'
        f'<hp:run charPrIDRef="{char_pr}"><hp:t/></hp:run>'
        f'</hp:p>'
    )


def make_text_para(idgen: IDGen, text: str, para_pr: int = 0, char_pr: int = 0) -> str:
    """Generate a text paragraph XML."""
    pid = idgen.next()
    return (
        f'<hp:p id="{pid}" paraPrIDRef="{para_pr}" styleIDRef="0" '
        f'pageBreak="0" columnBreak="0" merged="0">'
        f'<hp:run charPrIDRef="{char_pr}"><hp:t>{escape(text)}</hp:t></hp:run>'
        f'</hp:p>'
    )


def make_equation_para(idgen: IDGen, script: str, para_pr: int = 22,
                        char_pr: int = 9, base_unit: int = 1000) -> str:
    """Generate a paragraph containing an equation.

    Args:
        script: Hancom equation script (e.g., "x = {-b +- sqrt {b^2 - 4ac}} over {2a}")
        para_pr: Paragraph style ID (default: 22 = equation display)
        char_pr: Character style ID for surrounding text
        base_unit: Base font size for equation in HWPUNIT (1000 = 10pt)
    """
    pid = idgen.next()
    eqid = idgen.next_eq()
    escaped_script = escape(script)

    return (
        f'<hp:p id="{pid}" paraPrIDRef="{para_pr}" styleIDRef="0" '
        f'pageBreak="0" columnBreak="0" merged="0">'
        f'<hp:run charPrIDRef="{char_pr}">'
        f'<hp:equation id="{eqid}" type="0" textColor="#000000" '
        f'baseUnit="{base_unit}" letterSpacing="0" lineThickness="100">'
        f'<hp:sz width="0" height="0" widthRelTo="ABS" heightRelTo="ABS"/>'
        f'<hp:pos treatAsChar="1" affectLSpacing="0" flowWithText="0" '
        f'allowOverlap="0" holdAnchorAndSO="0" rgroupWithPrevCtrl="0" '
        f'vertRelTo="PARA" horzRelTo="PARA" vertAlign="TOP" horzAlign="LEFT" '
        f'vertOffset="0" horzOffset="0"/>'
        f'<hp:script>{escaped_script}</hp:script>'
        f'</hp:equation>'
        f'</hp:run>'
        f'</hp:p>'
    )


def make_text_with_equation(idgen: IDGen, text_before: str, script: str,
                             text_after: str = "", para_pr: int = 21,
                             char_pr: int = 9, base_unit: int = 1000) -> str:
    """Generate a paragraph with text and inline equation mixed."""
    pid = idgen.next()
    eqid = idgen.next_eq()
    escaped_script = escape(script)

    runs = []
    if text_before:
        runs.append(f'<hp:run charPrIDRef="{char_pr}"><hp:t>{escape(text_before)}</hp:t></hp:run>')

    runs.append(
        f'<hp:run charPrIDRef="{char_pr}">'
        f'<hp:equation id="{eqid}" type="0" textColor="#000000" '
        f'baseUnit="{base_unit}" letterSpacing="0" lineThickness="100">'
        f'<hp:sz width="0" height="0" widthRelTo="ABS" heightRelTo="ABS"/>'
        f'<hp:pos treatAsChar="1" affectLSpacing="0" flowWithText="0" '
        f'allowOverlap="0" holdAnchorAndSO="0" rgroupWithPrevCtrl="0" '
        f'vertRelTo="PARA" horzRelTo="PARA" vertAlign="TOP" horzAlign="LEFT" '
        f'vertOffset="0" horzOffset="0"/>'
        f'<hp:script>{escaped_script}</hp:script>'
        f'</hp:equation>'
        f'</hp:run>'
    )

    if text_after:
        runs.append(f'<hp:run charPrIDRef="{char_pr}"><hp:t>{escape(text_after)}</hp:t></hp:run>')

    return (
        f'<hp:p id="{pid}" paraPrIDRef="{para_pr}" styleIDRef="0" '
        f'pageBreak="0" columnBreak="0" merged="0">'
        + "".join(runs) +
        f'</hp:p>'
    )


def generate_section_xml(data: dict) -> str:
    """Generate section0.xml from problem data dictionary.

    Args:
        data: Problem data with keys: title, subtitle (optional), problems[]
    """
    idgen = IDGen()
    paragraphs = []

    # Read the secPr block from base section0.xml template
    base_section = BASE_DIR / "Contents" / "section0.xml"
    tree = etree.parse(str(base_section))
    root = tree.getroot()
    first_p = root.find(f"{{{NS['hp']}}}p")
    secpr_para = etree.tostring(first_p, encoding="unicode")
    paragraphs.append(secpr_para)

    # Title
    title = data.get("title", "")
    if title:
        paragraphs.append(make_text_para(idgen, title, para_pr=20, char_pr=7))

    # Subtitle
    subtitle = data.get("subtitle", "")
    if subtitle:
        paragraphs.append(make_text_para(idgen, subtitle, para_pr=20, char_pr=10))

    # Info line (name/date/score)
    info = data.get("info", "")
    if info:
        paragraphs.append(make_text_para(idgen, info, para_pr=0, char_pr=9))
    else:
        paragraphs.append(
            make_text_para(idgen, "이름:                    날짜:           점수:      /      ",
                           para_pr=0, char_pr=9)
        )

    paragraphs.append(make_empty_para(idgen))

    # Problems
    problems = data.get("problems", [])
    for i, prob in enumerate(problems, 1):
        # Problem number + text
        prob_text = prob.get("text", "")
        prob_num_text = f"{i}. {prob_text}" if prob_text else f"{i}."
        paragraphs.append(make_text_para(idgen, prob_num_text, para_pr=21, char_pr=8))

        # Main equation (display mode)
        eq = prob.get("equation", "")
        if eq:
            paragraphs.append(make_equation_para(idgen, eq, para_pr=22, char_pr=9))

        # Sub-problems
        sub_problems = prob.get("sub_problems", [])
        for j, sub in enumerate(sub_problems):
            sub_label = f"({j + 1}) "
            sub_text = sub.get("text", "")
            sub_eq = sub.get("equation", "")

            if sub_text and sub_eq:
                paragraphs.append(
                    make_text_with_equation(idgen, f"{sub_label}{sub_text} ", sub_eq,
                                            para_pr=23, char_pr=9)
                )
            elif sub_eq:
                paragraphs.append(
                    make_text_with_equation(idgen, sub_label, sub_eq,
                                            para_pr=23, char_pr=9)
                )
            elif sub_text:
                paragraphs.append(
                    make_text_para(idgen, f"{sub_label}{sub_text}", para_pr=23, char_pr=9)
                )

        # Choices (multiple choice)
        choices = prob.get("choices", [])
        if choices:
            choice_labels = ["①", "②", "③", "④", "⑤"]
            for k, choice in enumerate(choices):
                label = choice_labels[k] if k < len(choice_labels) else f"({k+1})"
                # Check if choice is an equation (starts with $ or contains math operators)
                if choice.startswith("$") and choice.endswith("$"):
                    eq_script = choice[1:-1]
                    paragraphs.append(
                        make_text_with_equation(idgen, f"{label} ", eq_script,
                                                para_pr=23, char_pr=11)
                    )
                else:
                    paragraphs.append(
                        make_text_para(idgen, f"{label} {choice}", para_pr=23, char_pr=11)
                    )

        # Spacing between problems
        paragraphs.append(make_empty_para(idgen))

    # Assemble
    body = "\n  ".join(paragraphs)
    return f"""<?xml version='1.0' encoding='UTF-8'?>
<hs:sec {SEC_NAMESPACES}>
  {body}
</hs:sec>
"""


def validate_xml(filepath: Path) -> None:
    """Check that an XML file is well-formed."""
    try:
        etree.parse(str(filepath))
    except etree.XMLSyntaxError as e:
        raise SystemExit(f"Malformed XML in {filepath.name}: {e}")


def update_metadata(content_hpf: Path, title: str | None, creator: str | None) -> None:
    """Update title and/or creator in content.hpf."""
    if not title and not creator:
        return

    tree = etree.parse(str(content_hpf))
    root = tree.getroot()
    ns = {"opf": "http://www.idpf.org/2007/opf/"}

    if title:
        title_el = root.find(".//opf:title", ns)
        if title_el is not None:
            title_el.text = title

    now = datetime.now(timezone.utc)
    iso_now = now.strftime("%Y-%m-%dT%H:%M:%SZ")

    for meta in root.findall(".//opf:meta", ns):
        name = meta.get("name", "")
        if creator and name == "creator":
            meta.text = creator
        elif creator and name == "lastsaveby":
            meta.text = creator
        elif name == "CreatedDate":
            meta.text = iso_now
        elif name == "ModifiedDate":
            meta.text = iso_now
        elif name == "date":
            meta.text = now.strftime("%Y년 %m월 %d일")

    etree.indent(root, space="  ")
    tree.write(str(content_hpf), pretty_print=True, xml_declaration=True, encoding="UTF-8")


def pack_hwpx(input_dir: Path, output_path: Path) -> None:
    """Create HWPX archive with mimetype as first entry (ZIP_STORED)."""
    mimetype_file = input_dir / "mimetype"
    if not mimetype_file.is_file():
        raise SystemExit(f"Missing 'mimetype' in {input_dir}")

    all_files = sorted(
        p.relative_to(input_dir).as_posix()
        for p in input_dir.rglob("*")
        if p.is_file()
    )

    with ZipFile(output_path, "w", ZIP_DEFLATED) as zf:
        zf.write(mimetype_file, "mimetype", compress_type=ZIP_STORED)
        for rel_path in all_files:
            if rel_path == "mimetype":
                continue
            zf.write(input_dir / rel_path, rel_path, compress_type=ZIP_DEFLATED)


def validate_hwpx(hwpx_path: Path) -> list[str]:
    """Quick structural validation of the output HWPX."""
    errors: list[str] = []
    required = [
        "mimetype",
        "Contents/content.hpf",
        "Contents/header.xml",
        "Contents/section0.xml",
    ]

    try:
        from zipfile import BadZipFile
        zf = ZipFile(hwpx_path, "r")
    except BadZipFile:
        return [f"Not a valid ZIP: {hwpx_path}"]

    with zf:
        names = zf.namelist()
        for r in required:
            if r not in names:
                errors.append(f"Missing: {r}")

        if "mimetype" in names:
            content = zf.read("mimetype").decode("utf-8").strip()
            if content != "application/hwp+zip":
                errors.append(f"Bad mimetype content: {content}")
            if names[0] != "mimetype":
                errors.append("mimetype is not the first ZIP entry")
            info = zf.getinfo("mimetype")
            if info.compress_type != ZIP_STORED:
                errors.append("mimetype is not ZIP_STORED")

        for name in names:
            if name.endswith(".xml") or name.endswith(".hpf"):
                try:
                    etree.fromstring(zf.read(name))
                except etree.XMLSyntaxError as e:
                    errors.append(f"Malformed XML: {name}: {e}")

    return errors


def build(
    problems_file: Path | None,
    header_override: Path | None,
    section_override: Path | None,
    title: str | None,
    creator: str | None,
    output: Path,
) -> None:
    """Main build logic."""
    if not BASE_DIR.is_dir():
        raise SystemExit(f"Base template not found: {BASE_DIR}")

    with tempfile.TemporaryDirectory() as tmpdir:
        work = Path(tmpdir) / "build"

        # 1. Copy base template
        shutil.copytree(BASE_DIR, work)

        # 2. Generate section0.xml from problem data
        if problems_file and not section_override:
            if not problems_file.is_file():
                raise SystemExit(f"Problems file not found: {problems_file}")
            with open(problems_file, encoding="utf-8") as f:
                data = json.load(f)
            if title and "title" not in data:
                data["title"] = title
            section_xml = generate_section_xml(data)
            (work / "Contents" / "section0.xml").write_text(section_xml, encoding="utf-8")

        # 3. Apply custom overrides
        if header_override:
            if not header_override.is_file():
                raise SystemExit(f"Header file not found: {header_override}")
            shutil.copy2(header_override, work / "Contents" / "header.xml")

        if section_override:
            if not section_override.is_file():
                raise SystemExit(f"Section file not found: {section_override}")
            shutil.copy2(section_override, work / "Contents" / "section0.xml")

        # 4. Update metadata
        update_metadata(work / "Contents" / "content.hpf", title, creator)

        # 5. Validate all XML files
        for xml_file in work.rglob("*.xml"):
            validate_xml(xml_file)
        for hpf_file in work.rglob("*.hpf"):
            validate_xml(hpf_file)

        # 6. Pack
        pack_hwpx(work, output)

    # 7. Final validation
    errors = validate_hwpx(output)
    if errors:
        print(f"WARNING: {output} has issues:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
    else:
        print(f"VALID: {output}")
        if problems_file:
            print(f"  Problems: {problems_file}")
        if header_override:
            print(f"  Header: {header_override}")
        if section_override:
            print(f"  Section: {section_override}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build math worksheet HWPX from problem data"
    )
    parser.add_argument(
        "--problems", "-p",
        type=Path,
        help="JSON file containing problem data",
    )
    parser.add_argument(
        "--header",
        type=Path,
        help="Custom header.xml to override",
    )
    parser.add_argument(
        "--section",
        type=Path,
        help="Custom section0.xml to override (bypasses problem generation)",
    )
    parser.add_argument(
        "--title",
        help="Document title",
    )
    parser.add_argument(
        "--creator",
        help="Document creator",
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        required=True,
        help="Output .hwpx file path",
    )
    args = parser.parse_args()

    if not args.problems and not args.section:
        parser.error("Either --problems or --section is required")

    build(
        problems_file=args.problems,
        header_override=args.header,
        section_override=args.section,
        title=args.title,
        creator=args.creator,
        output=args.output,
    )


if __name__ == "__main__":
    main()
