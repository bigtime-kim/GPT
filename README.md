# PCF Mapping Prototype

핵심 목표:
- 입력 활동명을 변환/정규화해서
- 보유한 `emission_factor.xlsx`에서 가장 적합한 배출계수(DB) 후보를 찾는 것

기본 모드는 **AI 없이 deterministic 검색**입니다. (그냥 실행하면 됨)

---

## 바로 실행
```powershell
python run_demo.py --name "VMQ"
```

- 고정 파일명 `emission_factor.xlsx`를 자동 로딩
- 있으면 Excel 기반으로 후보 검색
- 없거나 로딩 실패해도 프로그램은 종료되지 않음

---

## Gemini는 선택 기능 (기본 OFF)
Gemini 호출은 unresolved 케이스 보조용입니다.
Bad Request가 나면 일단 deterministic만으로 운영 가능.

Gemini 사용 시에만:
```powershell
$env:GEMINI_API_KEY="your_key"
python run_demo.py --use-ai --name "Thermiga 80127"
```

진단:
```powershell
python run_demo.py --diag --name "VMQ"
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
