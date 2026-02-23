#!/usr/bin/env python3
"""Regression test for math-hwpx refactoring.

Builds all test JSON files and compares section0.xml output
against pre-generated reference files to ensure byte-identical output.

Usage:
    # Generate reference files first (one-time):
    python test_refactor.py --generate-refs

    # Run regression tests:
    python test_refactor.py
"""

import argparse
import sys
import tempfile
from pathlib import Path
from zipfile import ZipFile

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
REFS_DIR = SKILL_DIR / "references"

# Test cases: (json_filename, ref_xml_name, description)
TEST_CASES = [
    ("고1_다항식_문제지.json", "ref_exam_section0.xml", "exam format"),
    ("중3_겨울방학_수학총정리.json", "ref_ws_section0.xml", "worksheet format"),
    ("그래프_테스트_문제.json", "ref_graph_section0.xml", "graph+exam format"),
]


def find_problems_file(name: str) -> Path:
    """Search for a test JSON file in known locations."""
    candidates = [
        Path.cwd() / name,
        SKILL_DIR.parent.parent.parent / name,  # project root
    ]
    for p in candidates:
        if p.is_file():
            return p
    raise FileNotFoundError(f"Cannot find {name} in {[str(c) for c in candidates]}")


def generate_refs() -> None:
    """Generate reference section0.xml files."""
    from build_math_hwpx import build

    REFS_DIR.mkdir(exist_ok=True)
    for json_name, ref_name, desc in TEST_CASES:
        problems = find_problems_file(json_name)
        with tempfile.NamedTemporaryFile(suffix=".hwpx", delete=False) as f:
            out = Path(f.name)
        build(problems_file=problems, header_override=None,
              section_override=None, title=None, creator=None, output=out)
        section = ZipFile(out).read("Contents/section0.xml")
        ref_path = REFS_DIR / ref_name
        ref_path.write_bytes(section)
        out.unlink(missing_ok=True)
        print(f"  REF: {ref_path} ({len(section)} bytes) [{desc}]")
    print(f"\nReferences saved to {REFS_DIR}")


def run_tests() -> int:
    """Run regression tests, return number of failures."""
    from build_math_hwpx import build

    failures = 0
    for json_name, ref_name, desc in TEST_CASES:
        ref_path = REFS_DIR / ref_name
        if not ref_path.is_file():
            print(f"  SKIP: {ref_name} (reference not found, run --generate-refs)")
            failures += 1
            continue

        problems = find_problems_file(json_name)
        with tempfile.NamedTemporaryFile(suffix=".hwpx", delete=False) as f:
            out = Path(f.name)
        build(problems_file=problems, header_override=None,
              section_override=None, title=None, creator=None, output=out)
        section = ZipFile(out).read("Contents/section0.xml")
        ref = ref_path.read_bytes()
        out.unlink(missing_ok=True)

        if section == ref:
            print(f"  PASS: {json_name} [{desc}]")
        else:
            print(f"  FAIL: {json_name} [{desc}] — output differs from reference")
            failures += 1

    return failures


def main() -> None:
    parser = argparse.ArgumentParser(description="Regression test for math-hwpx")
    parser.add_argument("--generate-refs", action="store_true",
                        help="Generate reference files instead of testing")
    args = parser.parse_args()

    if args.generate_refs:
        generate_refs()
    else:
        print("Running regression tests...")
        failures = run_tests()
        if failures:
            print(f"\n{failures} test(s) FAILED")
            sys.exit(1)
        else:
            print(f"\nAll {len(TEST_CASES)} tests PASSED")


if __name__ == "__main__":
    main()
