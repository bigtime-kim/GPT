# PCF Mapping Prototype

핵심 목표:
- 입력 활동명을 변환/정규화하고
- AI 추론 + Excel DB 검색을 결합해
- 보유한 `emission_factor.xlsx`에서 가장 적합한 배출계수 후보를 찾는 것

기본 모드는 **AI-first**입니다. (기본적으로 Gemini 보조 추론 수행)

---

## 바로 실행
```powershell
python run_demo.py --name "VMQ"
```

- 고정 파일명 `emission_factor.xlsx`를 자동 로딩
- deterministic 후보를 만든 뒤 AI가 의미 해석/재랭킹
- 엑셀이 없거나 로딩 실패해도 프로그램은 종료되지 않음

---

## Gemini 설정
권장:
```powershell
$env:GEMINI_API_KEY="your_key"
python run_demo.py --name "Thermiga 80127"
```

진단:
```powershell
python run_demo.py --diag --name "VMQ"
```

디버그용으로만 AI 비활성화:
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

## 권장 설치
```powershell
python -m pip install -r requirements.txt
```

---

## 테스트
```powershell
python -m unittest discover -s tests -v
```
