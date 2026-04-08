# PCF Mapping Prototype

핵심 목표:
- 입력 활동명을 변환/정규화하고
- AI 추론 + Excel DB 검색을 결합해
- 보유한 `emission_factor.xlsx`에서 가장 적합한 배출계수 후보를 찾는 것

기본 모드는 **AI-first**입니다.
단, Gemini 키가 없으면 자동으로 로컬 AI 스텁으로 동작하며 멈추지 않습니다.

---

## 바로 실행
```powershell
python run_demo.py --name "VMQ"
```

- 고정 파일명 `emission_factor.xlsx` 자동 로딩
- deterministic 후보 생성 + AI 재랭킹
- 엑셀이 없거나 로딩 실패해도 종료되지 않음
- Gemini 키가 없어도 키 입력 프롬프트 없이 계속 진행

---

## openpyxl 경고가 뜰 때 (당신 로그 케이스)
현재 실행 Python에 openpyxl이 없는 상태입니다.
아래 **그대로 복붙**:

```powershell
"C:\Users\shk23\AppData\Local\Programs\Python\Python312\python.exe" -m pip install openpyxl
```

또는 일반형:
```powershell
python -m pip install -r requirements.txt
```

설치 확인:
```powershell
python -c "import openpyxl; print(openpyxl.__version__)"
```

---

## Gemini 설정 (선택)
```powershell
$env:GEMINI_API_KEY="your_key"
python run_demo.py --name "Thermiga 80127"
```

디버그:
```powershell
python run_demo.py --diag --name "VMQ"
```

AI 비활성화(디버그용):
```powershell
python run_demo.py --no-ai --name "VMQ"
```

---

## Excel 파일 규칙
- 파일명: `emission_factor.xlsx`
- 필수 컬럼:
  - `Activity Name`
  - `Geography`
  - `Reference Product Name`
  - `Reference Product Unit`

탐색 순서:
1. 현재 폴더
2. 실행파일/스크립트 폴더
3. 실행파일/스크립트 상위 폴더

---

## 테스트
```powershell
python -m unittest discover -s tests -v
```
