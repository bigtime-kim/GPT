# PCF Mapping Prototype

요청사항 반영:
- 엑셀 경로 입력 제거
- 고정 파일명 `emission_factor.xlsx` 자동 로딩
- 파일 인식/로딩 실패 시 즉시 종료하지 않고 경고 후 계속 실행
- 못 찾으면 실제 검색한 절대경로와 주변 Excel 파일 목록을 출력

---

## 당신 로그 기준 현재 상태
- `python run_demo.py --name "VMQ"` 는 정상 동작 (엑셀 로딩 성공)
- 그런데 다른 실행(주로 exe)에서 `openpyxl is required...` 경고 발생

이 경우는 보통 **실행 환경이 다르기 때문**입니다.
(예: Python 실행은 openpyxl 있음 / exe 빌드는 openpyxl 미포함)

---

## 빠른 진단
```powershell
python run_demo.py --diag --name "VMQ"
```

출력에서 확인:
- `[DIAG] python executable:`
- `[DIAG] openpyxl version:`

exe에서도 같은 진단이 필요하면 exe 실행 시 `--diag`를 붙여 실행하세요.

---

## exe에서만 실패할 때 (중요)
PyInstaller 빌드 시 openpyxl을 포함해서 다시 빌드하세요.

```powershell
pyinstaller --onefile run_demo.py --collect-all openpyxl
```

그 후 `dist\run_demo.exe --diag` 로 확인.

---

## 엑셀파일을 폴더에 넣었는데 왜 못 찾는가?
대부분 아래 중 하나입니다.
1) 파일명이 정확히 `emission_factor.xlsx`가 아님
2) exe 실행 위치와 파일 위치가 다름
3) 확장자가 숨김되어 `emission_factor.xlsx.xlsx` 상태

이제 프로그램이 못 찾으면 아래를 출력합니다.
- 검색한 경로들
- 주변에서 발견된 `*.xls*` 파일 목록

---

## 파일 탐색 순서
`emission_factor.xlsx`는 아래 순서로 탐색됩니다.
1. 현재 실행 폴더
2. 실행 파일(또는 스크립트) 폴더
3. 실행 파일(또는 스크립트) 상위 폴더

---

## 실행
```powershell
python run_demo.py
python run_demo.py --name "VMQ" --geo KR --unit kg --use-ai
```

---

## 고정 Excel 파일명 규칙
- 파일명: `emission_factor.xlsx`
- 필수 컬럼:
  - `Activity Name`
  - `Geography`
  - `Reference Product Name`
  - `Reference Product Unit`

---

## Gemini API 키 입력 방법
### 방법 A) 실행 중 직접 입력
- `python run_demo.py`
- `Gemini AI fallback 사용? (y/N)`에서 `y`
- 키 입력

### 방법 B) 환경변수 (권장)
```powershell
$env:GEMINI_API_KEY="your_gemini_api_key"
python run_demo.py --use-ai --name "Thermiga 80127"
```

### 방법 C) 코드에 직접 작성 (가능하지만 비권장)
`run_demo.py` 상단:
```python
DEMO_GEMINI_API_KEY = "여기에_키"
```

---

## 테스트
```powershell
python -m unittest discover -s tests -v
```
