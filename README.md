# PCF Mapping Prototype

핵심 목표:
- 입력 활동명을 변환/정규화하고
- AI 추론 + Excel DB 검색을 결합해
- 보유한 `emission_factor.xlsx`에서 가장 적합한 배출계수 후보를 찾는 것

이 버전은 **구현 강제 모드(Strict)** 입니다.
- Excel 파일 누락/로딩 실패 시 즉시 에러
- Gemini 키 누락 시 즉시 에러
- 다만 `openpyxl`이 없으면 **실행 중 자동 설치 1회 시도** 후 계속 진행합니다.

---

## 실행 전 권장
```powershell
python -m pip install -r requirements.txt
$env:GEMINI_API_KEY="your_key"
```

---

## 바로 실행
```powershell
python run_demo.py --name "VMQ"
```

성공 조건:
1) `emission_factor.xlsx` 존재
2) 필수 컬럼 4개 존재
3) `GEMINI_API_KEY` 설정

---

## openpyxl 관련
- 없으면 코드가 자동으로 `python -m pip install openpyxl` 1회 시도
- 네트워크/권한 문제로 실패하면 아래 수동 실행:

```powershell
"C:\Users\shk23\AppData\Local\Programs\Python\Python312\python.exe" -m pip install openpyxl
```

---

## Gemini Bad Request 대응
진단:
```powershell
python run_demo.py --diag --name "VMQ"
```

실패 시 모델/키 확인:
```powershell
python run_demo.py --name "VMQ" --gemini-model "gemini-2.0-flash"
```

디버그용으로만 AI 비활성화(운영 비권장):
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
