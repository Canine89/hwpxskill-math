#!/usr/bin/env bash
# 학력평가/수능 형식 시험지 빌드 예제
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VENV="${SKILL_DIR}/../../.venv/bin/activate"

if [ -f "$VENV" ]; then
    source "$VENV"
fi

python3 "$SKILL_DIR/scripts/build_math_hwpx.py" \
    --problems "$SKILL_DIR/examples/sample_exam_2020_march.json" \
    --creator "교육청" \
    --output /tmp/exam_2020_march.hwpx

echo "Output: /tmp/exam_2020_march.hwpx"
