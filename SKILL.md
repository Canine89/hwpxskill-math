# math-hwpx — 수학 수식 문제지 HWPX 생성 스킬

수학 수식(`hp:equation`)을 포함한 **2열 문제지**를 HWPX 파일로 생성하는 스킬.
중학교 1학년 ~ 고등학교 3학년 범위의 수학 문제를 한컴오피스 수식 편집기 스크립트 문법으로 작성한다.
hwpx 스킬과 동일한 XML-first 워크플로우를 따르며, 기존 hwpx 스킬의 빌드/검증 도구와 호환된다.

## 환경

```
# SKILL_DIR는 이 SKILL.md가 위치한 디렉토리의 절대 경로로 설정
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"   # 스크립트 내에서

# hwpx 기본 스킬 경로 (검증/추출 도구 사용 시)
HWPX_SKILL_DIR="<hwpx 스킬 설치 경로>"

# Python 가상환경 (프로젝트에 맞게 설정)
VENV="<프로젝트>/.venv/bin/activate"
```

모든 Python 실행 시:
```bash
# 프로젝트의 .venv를 활성화 (pip install lxml 필요)
source "$VENV"
```

## 디렉토리 구조

```
.claude/skills/math-hwpx/
├── SKILL.md                              # 이 파일
├── scripts/
│   └── build_math_hwpx.py                # 핵심 — JSON 문제 → HWPX 빌드
├── templates/
│   ├── base/                             # 2단 레이아웃 기본 템플릿
│   │   ├── mimetype, META-INF/*, version.xml, settings.xml, Preview/*
│   │   └── Contents/ (header.xml, section0.xml, content.hpf)
│   └── worksheet/                        # (확장용) 오버레이 템플릿
├── examples/
│   ├── sample_middle_school.json          # 중학교 문제 예시
│   ├── sample_high_school.json            # 고등학교 문제 예시
│   ├── 01_middle_school_worksheet.sh      # 빌드 예제
│   └── 02_high_school_worksheet.sh        # 빌드 예제
└── references/                           # (확장용) 참고자료
```

---

## 핵심 워크플로우: JSON → HWPX 문제지

### 1. 문제 JSON 작성

```json
{
  "title": "중학교 2학년 수학 단원평가",
  "subtitle": "일차방정식과 부등식",
  "info": "이름:          날짜:          점수:     /     ",
  "problems": [
    {
      "text": "다음 방정식을 풀어라.",
      "equation": "2x + 3 = 7"
    },
    {
      "text": "다음을 간단히 하여라.",
      "sub_problems": [
        {"equation": "{2x+1} over 3 = {x-2} over 5"},
        {"equation": "sqrt 12 + sqrt 27"}
      ]
    },
    {
      "text": "옳은 것을 고르시오.",
      "choices": ["$sqrt 4 = 2$", "$sqrt 9 = +- 3$", "$(-2)^2 = -4$", "$sqrt {16} = 4$"]
    }
  ]
}
```

### 2. 빌드

```bash
source "$VENV"

python3 "$SKILL_DIR/scripts/build_math_hwpx.py" \
    --problems problems.json \
    --title "중2 일차방정식" \
    --creator "수학교사" \
    --output worksheet.hwpx
```

### 3. 검증 (hwpx 스킬의 validate.py 사용)

```bash
python3 "$HWPX_SKILL_DIR/scripts/validate.py" worksheet.hwpx
```

---

## 문제 JSON 형식

```json
{
  "title": "문서 제목 (상단 중앙, 16pt 볼드)",
  "subtitle": "부제목 (선택, 12pt 볼드)",
  "info": "이름/날짜/점수 라인 (선택, 기본값 자동 생성)",
  "problems": [
    {
      "text": "문제 본문 텍스트",
      "equation": "한컴 수식 스크립트 (display 모드)",
      "sub_problems": [
        {"text": "소문제 텍스트", "equation": "수식"},
        {"equation": "수식만"}
      ],
      "choices": ["선택지1", "$수식선택지$", "선택지3"]
    }
  ]
}
```

### 필드 설명

| 필드 | 필수 | 설명 |
|------|------|------|
| `title` | O | 문제지 제목 |
| `subtitle` | X | 단원명/부제 |
| `info` | X | 이름/날짜란 (미지정 시 기본값) |
| `problems` | O | 문제 배열 |
| `problems[].text` | X | 문제 텍스트 |
| `problems[].equation` | X | 독립 수식 (display 모드) |
| `problems[].sub_problems` | X | 소문제 배열 [{text, equation}] |
| `problems[].choices` | X | 객관식 선택지 (`$...$`로 감싸면 수식) |

---

## 한컴 수식 스크립트 문법 (hp:equation)

### 기본 규칙

| 규칙 | 설명 |
|------|------|
| `{ }` | 그룹화 (여러 항을 하나로) |
| `~` | 공백 (1em) |
| `` ` `` | 1/4 공백 |
| `#` | 줄바꿈 (수식 내) |
| `&` | 열 정렬 (행렬, 연립방정식) |
| `"..."` | 텍스트 모드 (수식 해석 비활성) |

### 분수와 루트

| 수식 | 스크립트 | 예시 |
|------|----------|------|
| 분수 | `a over b` | `{x+1} over {x-1}` |
| 제곱근 | `sqrt {x}` | `sqrt {b^2 - 4ac}` |
| n제곱근 | `root n of {x}` | `root 3 of {27}` |

### 위·아래 첨자

| 수식 | 스크립트 |
|------|----------|
| 위첨자 | `x^2` 또는 `x SUP 2` |
| 아래첨자 | `x_i` 또는 `x SUB i` |
| 둘 다 | `x_i ^2` |

### 적분·합·곱

| 수식 | 스크립트 |
|------|----------|
| 정적분 | `int _{a} ^{b} f(x) dx` |
| 이중적분 | `dint f(x,y) dxdy` |
| 삼중적분 | `tint f dxdydz` |
| 급수(시그마) | `sum _{k=1} ^{n} a_k` |
| 곱(파이) | `prod _{i=1} ^{n} x_i` |

### 극한

| 수식 | 스크립트 |
|------|----------|
| 극한 | `lim _{x -> 0} f(x)` |
| 대문자 | `Lim _{n -> inf}` |

### 괄호

| 수식 | 스크립트 |
|------|----------|
| 자동 크기 소괄호 | `left ( {a over b} right )` |
| 자동 크기 대괄호 | `left [ x right ]` |
| 자동 크기 중괄호 | `left lbrace x right rbrace` |
| 절댓값 | `left | x right |` |

### 행렬

| 수식 | 스크립트 |
|------|----------|
| 기본 행렬 | `matrix {a & b # c & d}` |
| 소괄호 행렬 | `pmatrix {a & b # c & d}` |
| 대괄호 행렬 | `bmatrix {1 & 0 # 0 & 1}` |
| 행렬식 | `dmatrix {a & b # c & d}` |

### 연립방정식·조건

| 수식 | 스크립트 |
|------|----------|
| 연립방정식 | `cases {2x+y=5 # 3x-2y=4}` |
| 정렬 수식 | `eqalign {a &= b # c &= d}` |
| 수직 스택 | `pile {a # b # c}` |

### 장식(위·아래)

| 장식 | 스크립트 |
|------|----------|
| 모자(^) | `hat a` |
| 물결 | `tilde a` |
| 벡터 화살표 | `vec v` |
| 윗줄 | `bar x` |
| 밑줄 | `under x` |
| 점 1개 | `dot a` |
| 점 2개 | `ddot a` |

### 그리스 문자

소문자: `alpha`, `beta`, `gamma`, `delta`, `epsilon`, `zeta`, `eta`, `theta`, `iota`, `kappa`, `lambda`, `mu`, `nu`, `xi`, `pi`, `rho`, `sigma`, `tau`, `upsilon`, `phi`, `chi`, `psi`, `omega`

대문자: `ALPHA`, `BETA`, `GAMMA`, `DELTA` 등

변형: `vartheta`, `varphi`, `varepsilon`

### 특수 기호

| 기호 | 스크립트 |
|------|----------|
| 무한대 | `inf` |
| 편미분 | `partial` |
| 나블라 | `nabla` |
| 고로 | `therefore` |
| 왜냐하면 | `because` |
| 모든 | `forall` |
| 존재 | `exist` |
| ± | `+-` 또는 `pm` |
| ≠ | `ne` |
| ≤ | `le` 또는 `leq` |
| ≥ | `ge` 또는 `geq` |
| ≈ | `approx` |
| ≡ | `equiv` |
| ⊂ | `subset` |
| ∈ | `in` |
| → | `->` 또는 `rarrow` |
| ← | `larrow` |
| ↔ | `<->` 또는 `lrarrow` |
| ··· | `cdots` |

### 폰트 스타일

| 스타일 | 명령 |
|--------|------|
| 로만(정체) | `rm` |
| 이탤릭 | `it` |
| 볼드 | `bold` |
| 볼드 로만 | `rmbold` |

### 내장 함수 (자동 로만체)

`sin`, `cos`, `tan`, `cot`, `sec`, `csc`, `arcsin`, `arccos`, `arctan`, `log`, `ln`, `lg`, `exp`, `det`, `mod`, `gcd`, `max`, `min`, `sinh`, `cosh`, `tanh`

---

## 수식 XML 구조

section0.xml에서 수식은 다음과 같이 삽입된다:

```xml
<hp:p id="고유ID" paraPrIDRef="22" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">
  <hp:run charPrIDRef="9">
    <hp:equation id="고유ID" type="0" textColor="#000000"
                 baseUnit="1000" letterSpacing="0" lineThickness="100">
      <hp:sz width="0" height="0" widthRelTo="ABS" heightRelTo="ABS"/>
      <hp:pos treatAsChar="1" affectLSpacing="0" flowWithText="0"
              allowOverlap="0" holdAnchorAndSO="0" rgroupWithPrevCtrl="0"
              vertRelTo="PARA" horzRelTo="PARA" vertAlign="TOP" horzAlign="LEFT"
              vertOffset="0" horzOffset="0"/>
      <hp:script>x = {-b +- sqrt {b^2 - 4ac}} over {2a}</hp:script>
    </hp:equation>
  </hp:run>
</hp:p>
```

### 수식 속성

| 속성 | 값 | 설명 |
|------|----|----|
| `baseUnit` | 1000 | 기본 10pt (100 HWPUNIT = 1pt) |
| `textColor` | #000000 | 수식 색상 |
| `lineThickness` | 100 | 분수선/루트선 두께 |
| `treatAsChar` | 1 | 인라인 수식 (텍스트와 같은 줄) |

### 텍스트 + 수식 혼합

한 문단에 텍스트와 수식을 함께 배치:

```xml
<hp:p id="..." paraPrIDRef="21" ...>
  <hp:run charPrIDRef="9"><hp:t>방정식 </hp:t></hp:run>
  <hp:run charPrIDRef="9">
    <hp:equation ...>
      <hp:script>2x + 3 = 7</hp:script>
    </hp:equation>
  </hp:run>
  <hp:run charPrIDRef="9"><hp:t> 의 해를 구하라.</hp:t></hp:run>
</hp:p>
```

---

## 2단 레이아웃 설정

section0.xml 첫 문단의 `hp:colPr`으로 설정:

```xml
<hp:colPr id="" type="NEWSPAPER" layout="LEFT" colCount="2" sameSz="1" sameGap="2268"/>
```

| 속성 | 값 | 설명 |
|------|----|----|
| `type` | NEWSPAPER | 좌→우 순서로 채움 |
| `colCount` | 2 | 2단 |
| `sameSz` | 1 | 동일 너비 |
| `sameGap` | 2268 | 단간격 8mm |

### 페이지 설정 (문제지 최적화)

```xml
<hp:pagePr landscape="WIDELY" width="59528" height="84186" gutterType="LEFT_ONLY">
  <hp:margin header="4252" footer="4252" gutter="0"
             left="5668" right="5668" top="4252" bottom="4252"/>
</hp:pagePr>
```

- 좌우 여백: 20mm (표준 30mm보다 좁음 → 내용 영역 확대)
- 상하 여백: 15mm
- 본문폭: 48192 HWPUNIT (170mm)
- 단 너비: (48192 - 2268) / 2 = 22962 HWPUNIT (약 81mm)

---

## 스타일 ID 맵

### charPr (글자 스타일)

| ID | 설명 | 크기 | 폰트 | 굵기 |
|----|------|------|------|------|
| 0 | 기본 본문 | 10pt | 함초롬바탕 | 보통 |
| 1 | 돋움 기본 | 10pt | 함초롬돋움 | 보통 |
| 2~6 | Skeleton 호환 | 다양 | 다양 | 보통 |
| **7** | **문제지 제목** | **16pt** | **함초롬돋움** | **볼드** |
| **8** | **문제 번호** | **11pt** | **함초롬돋움** | **볼드** |
| **9** | **문제 본문** | **10pt** | **함초롬돋움** | 보통 |
| **10** | **단원명/소제목** | **12pt** | **함초롬돋움** | **볼드** |
| **11** | **선택지/보기** | **9pt** | **함초롬돋움** | 보통 |

### paraPr (문단 스타일)

| ID | 정렬 | 줄간격 | 용도 |
|----|------|--------|------|
| 0 | JUSTIFY | 160% | 기본 본문 |
| 1~19 | 다양 | 다양 | Skeleton 호환 |
| **20** | **CENTER** | **160%** | **제목** |
| **21** | **LEFT** | **150%** | **문제 본문** (문단 전후 여백 포함) |
| **22** | **LEFT** | **140%** | **수식 표시** (좌측 들여쓰기) |
| **23** | **LEFT** | **140%** | **선택지/보기** (좌측 들여쓰기) |

### borderFill (테두리)

| ID | 설명 |
|----|------|
| 1 | 없음 (페이지 보더) |
| 2 | 없음 + 투명배경 |
| 3 | SOLID 4면 (표용) |
| 4 | SOLID + #E8E8E8 배경 (헤더 셀) |
| 5 | 하단 DASH 선 (문제 구분) |

---

## 학년별 수식 예시

### 중학교 (중1~중3)

```
# 일차방정식
2x + 3 = 7

# 분수 방정식
{2x+1} over 3 = {x-2} over 5

# 연립방정식
cases {2x + y = 5 # 3x - 2y = 4}

# 제곱근
sqrt 12 + sqrt 27 - sqrt 48

# 부등식
3x - 5 > 2x + 1

# 이차방정식
x^2 - 5x + 6 = 0

# 피타고라스
a^2 + b^2 = c^2

# 일차함수
y = ax + b
```

### 고등학교 수학 I (고1)

```
# 지수법칙
a^m times a^n = a^{m+n}

# 로그
log _a xy = log _a x + log _a y

# 절댓값
left | x - 3 right | < 5

# 이차함수 꼭짓점
y = a(x - p)^2 + q

# 근의 공식
x = {-b +- sqrt {b^2 - 4ac}} over {2a}
```

### 고등학교 수학 II (고2)

```
# 극한
lim _{x -> 0} {sin x} over x = 1

# 미분 정의
f'(x) = lim _{h -> 0} {f(x+h) - f(x)} over h

# 정적분
int _{0} ^{pi} sin x dx = 2

# 급수
sum _{k=1} ^{n} k = {n(n+1)} over 2

# 등차수열
a_n = a_1 + (n-1)d
```

### 고등학교 확률과 통계

```
# 조합
{_n}C{_r} = {n!} over {r!(n-r)!}

# 이항정리
(a+b)^n = sum _{k=0} ^{n} {_n}C{_k} a^{n-k} b^k

# 확률
P(A cup B) = P(A) + P(B) - P(A cap B)

# 정규분포
f(x) = {1} over {sigma sqrt {2 pi}} e^{-{(x- mu)^2} over {2 sigma ^2}}
```

### 고등학교 미적분

```
# 도함수
{d} over {dx} x^n = n x^{n-1}

# 합성함수 미분
{dy} over {dx} = {dy} over {du} times {du} over {dx}

# 부분적분
int u dv = uv - int v du

# 치환적분
int f(g(x)) g'(x) dx = int f(u) du

# 테일러 급수
e^x = sum _{n=0} ^{inf} {x^n} over {n!}
```

### 고등학교 기하

```
# 벡터 내적
vec a cdot vec b = left | vec a right | left | vec b right | cos theta

# 원의 방정식
(x-a)^2 + (y-b)^2 = r^2

# 타원
{x^2} over {a^2} + {y^2} over {b^2} = 1

# 쌍곡선
{x^2} over {a^2} - {y^2} over {b^2} = 1

# 행렬 곱
pmatrix {a & b # c & d} pmatrix {x # y} = pmatrix {ax+by # cx+dy}
```

---

## 직접 section0.xml 작성 (고급)

JSON 대신 직접 section0.xml을 작성하여 더 세밀한 제어 가능:

```bash
SECTION=$(mktemp /tmp/section0_XXXX.xml)
cat > "$SECTION" << 'XMLEOF'
<?xml version='1.0' encoding='UTF-8'?>
<hs:sec xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph"
        xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section"
        xmlns:hc="http://www.hancom.co.kr/hwpml/2011/core">
  <!-- base/section0.xml의 첫 문단(secPr+colPr) 그대로 복사 -->
  <!-- ... -->

  <!-- 제목 -->
  <hp:p id="1000000002" paraPrIDRef="20" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">
    <hp:run charPrIDRef="7"><hp:t>수학 문제지</hp:t></hp:run>
  </hp:p>

  <!-- 수식 문단 -->
  <hp:p id="1000000003" paraPrIDRef="22" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">
    <hp:run charPrIDRef="9">
      <hp:equation id="1000000099" type="0" textColor="#000000"
                   baseUnit="1000" letterSpacing="0" lineThickness="100">
        <hp:sz width="0" height="0" widthRelTo="ABS" heightRelTo="ABS"/>
        <hp:pos treatAsChar="1" affectLSpacing="0" flowWithText="0"
                allowOverlap="0" holdAnchorAndSO="0" rgroupWithPrevCtrl="0"
                vertRelTo="PARA" horzRelTo="PARA" vertAlign="TOP" horzAlign="LEFT"
                vertOffset="0" horzOffset="0"/>
        <hp:script>x = {-b +- sqrt {b^2 - 4ac}} over {2a}</hp:script>
      </hp:equation>
    </hp:run>
  </hp:p>
</hs:sec>
XMLEOF

python3 "$SKILL_DIR/scripts/build_math_hwpx.py" --section "$SECTION" --output result.hwpx
rm -f "$SECTION"
```

---

## hwpx 스킬과의 연동

math-hwpx는 hwpx 스킬의 도구를 재사용할 수 있다:

| 도구 | 경로 | 용도 |
|------|------|------|
| validate.py | `$HWPX_SKILL_DIR/scripts/validate.py` | HWPX 구조 검증 |
| unpack.py | `$HWPX_SKILL_DIR/scripts/office/unpack.py` | HWPX → 디렉토리 |
| pack.py | `$HWPX_SKILL_DIR/scripts/office/pack.py` | 디렉토리 → HWPX |
| text_extract.py | `$HWPX_SKILL_DIR/scripts/text_extract.py` | 텍스트 추출 |

```bash
# 생성된 문제지 구조 확인
python3 "$HWPX_SKILL_DIR/scripts/office/unpack.py" worksheet.hwpx ./unpacked/
# → ./unpacked/Contents/section0.xml 편집 후
python3 "$HWPX_SKILL_DIR/scripts/office/pack.py" ./unpacked/ edited.hwpx
```

---

## 단위 변환 (hwpx 스킬과 동일)

| 값 | HWPUNIT | 의미 |
|----|---------|------|
| 1pt | 100 | 기본 단위 |
| 10pt | 1000 | 기본 글자크기 |
| 1mm | 283.5 | 밀리미터 |
| A4 폭 | 59528 | 210mm |
| A4 높이 | 84186 | 297mm |
| 문제지 좌우여백 | 5668 | 20mm |
| 문제지 본문폭 | 48192 | 170mm |
| 단간격 | 2268 | 8mm |
| 단 너비 | 22962 | 약 81mm |

---

## Critical Rules

1. **수식 스크립트는 `<hp:script>` 안에**: LaTeX가 아닌 한컴 수식 문법 사용
2. **secPr 필수**: section0.xml 첫 문단에 secPr + colPr(2단) 반드시 포함
3. **2단 설정**: `colCount="2"` + `sameGap="2268"` (기본 8mm 단간격)
4. **mimetype 순서**: ZIP 패키징 시 mimetype은 첫 번째 엔트리, ZIP_STORED
5. **ID 고유성**: 문단 ID, 수식 ID 모두 문서 내 유일해야 함
6. **charPrIDRef 정합성**: section0.xml에서 참조하는 charPr ID가 header.xml에 존재해야 함
7. **venv 사용**: 프로젝트의 `.venv/bin/activate` (lxml 패키지 필요)
8. **검증 필수**: 생성 후 validate.py로 무결성 확인
9. **수식 크기**: `baseUnit="1000"` = 10pt (본문과 동일), 필요시 `1200`(12pt) 등 조절
10. **선택지 수식**: JSON에서 `$...$`로 감싸면 수식으로 처리
11. **hp:sz width/height 0**: 한컴오피스가 렌더링 시 자동 계산하므로 0으로 설정 가능
