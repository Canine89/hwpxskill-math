#!/bin/bash
# 중학교 수학 문제지 생성 예제
set -e

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VENV="${VENV:-$(cd "$SKILL_DIR/../.." && pwd)/.venv/bin/activate}"

source "$VENV"

python3 "$SKILL_DIR/scripts/build_math_hwpx.py" \
    --problems "$SKILL_DIR/examples/sample_middle_school.json" \
    --title "중학교 2학년 수학 단원평가" \
    --creator "수학교사" \
    --output "/tmp/middle_school_worksheet.hwpx"

echo "생성 완료: /tmp/middle_school_worksheet.hwpx"
