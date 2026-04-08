# PCF Mapping Prototype

요청사항 반영:
- 엑셀 경로 입력 제거
- 고정 파일명 `emission_factor.xlsx` 자동 로딩
- 3분리 원칙(뼈대 기능 / AI API / 지식데이터) 체크리스트 제공

---

## 질문 3가지 답
1. **엑셀파일은 같은 폴더에 넣으면 되나요?**  
   → **네.** 실행 폴더에 `emission_factor.xlsx` 파일명으로 두면 자동 로딩됩니다.
2. **실행파일에서 API 키를 바로 입력할 수 있나요?**  
   → **네.** AI 사용 시 `y` 선택하면 키 입력창이 뜹니다.
3. **그다음 물질명을 넣으면 바로 실행되나요?**  
   → **네.** 입력 즉시 매핑 결과가 출력됩니다.

---

## 고정 Excel 파일명 규칙
- 파일명: `emission_factor.xlsx`
- 위치: `run_demo.py` 실행하는 현재 폴더
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
