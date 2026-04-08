# PCF Mapping Prototype

요청사항 반영:
- 엑셀 경로 입력 제거
- 고정 파일명 `emission_factor.xlsx` 자동 로딩
- 파일 인식/로딩 실패 시 즉시 종료하지 않고 경고 후 계속 실행

---

## 실행파일이 바로 꺼지는 경우
주요 원인:
1) `emission_factor.xlsx`를 못 찾음
2) 엑셀 로딩 의존성(`openpyxl`) 없음
3) 엑셀 컬럼 불일치

현재는 위 문제가 있어도 프로그램이 바로 종료되지 않고,
경고를 출력한 뒤 기본 샘플 지식으로 계속 실행됩니다.

---

## 파일을 못 읽는 경우 먼저 확인
`emission_factor.xlsx`는 아래 순서로 탐색됩니다.
1. 현재 실행 폴더
2. 실행 파일(또는 스크립트) 폴더
3. 실행 파일(또는 스크립트) 상위 폴더

즉, exe를 `dist`에서 실행한다면
- `dist/emission_factor.xlsx` 또는
- 프로젝트 루트(`dist`의 상위 폴더)에 파일을 두면 인식됩니다.

---

## 질문 3가지 답
1. **엑셀파일은 같은 폴더에 넣으면 되나요?**  
   → **네.** 같은 폴더면 인식됩니다. 안 되면 위 3개 탐색 위치를 확인하세요.
2. **실행파일에서 API 키를 바로 입력할 수 있나요?**  
   → **네.** AI 사용 시 `y` 선택하면 키 입력창이 뜹니다.
3. **그다음 물질명을 넣으면 바로 실행되나요?**  
   → **네.** 입력 즉시 매핑 결과가 출력됩니다.

---

## 고정 Excel 파일명 규칙
- 파일명: `emission_factor.xlsx`
- 필수 컬럼:
  - `Activity Name`
  - `Geography`
  - `Reference Product Name`
  - `Reference Product Unit`

---

## 실행
```bash
python run_demo.py
```

자동화 실행:
```bash
python run_demo.py --name "VMQ" --geo KR --unit kg --use-ai
```

---

## Gemini API 키 입력 방법
### 방법 A) 실행 중 직접 입력
- `python run_demo.py`
- `Gemini AI fallback 사용? (y/N)`에서 `y`
- 키 입력

### 방법 B) 환경변수 (권장)
#### Windows PowerShell
```powershell
$env:GEMINI_API_KEY="your_gemini_api_key"
python run_demo.py --use-ai --name "Thermiga 80127"
```

#### Linux/macOS
```bash
export GEMINI_API_KEY="your_gemini_api_key"
python run_demo.py --use-ai --name "Thermiga 80127"
```

### 방법 C) 코드에 직접 작성 (가능하지만 비권장)
`run_demo.py` 상단:
```python
DEMO_GEMINI_API_KEY = "여기에_키"
```

---

## 구현 점검 문서
- `IMPLEMENTATION_CHECKLIST.md` 참조

---

## 테스트
```bash
python -m unittest discover -s tests -v
```
