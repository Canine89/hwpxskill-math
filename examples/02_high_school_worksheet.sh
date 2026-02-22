#!/bin/bash
# 고등학교 수학 문제지 생성 예제
set -e

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VENV="/Users/canine89/Documents/dev/skills/.venv/bin/activate"

source "$VENV"

python3 "$SKILL_DIR/scripts/build_math_hwpx.py" \
    --problems "$SKILL_DIR/examples/sample_high_school.json" \
    --title "고등학교 수학 I" \
    --creator "수학교사" \
    --output "/tmp/high_school_worksheet.hwpx"

echo "생성 완료: /tmp/high_school_worksheet.hwpx"
