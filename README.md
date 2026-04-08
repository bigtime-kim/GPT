# PCF Mapping Prototype

이제 `run_demo.py`에서 **실제 Gemini API 호출**이 동작합니다.
(실패 시 안전하게 로컬 fallback 사용)

질문 주신 3가지 요약:

1. **엑셀파일은 같은 폴더에 넣으면 되나요?**  
   → **네.** 실행 폴더에 `emission_factor.xlsx`로 두면 자동 인식됩니다. (또는 `--ef-excel`)  
2. **실행파일에서 API 키를 바로 입력할 수 있나요?**  
   → **네.** 대화형에서 `y` 선택 시 키 입력창이 뜹니다.  
3. **그다음 물질명을 넣으면 바로 실행되나요?**  
   → **네.** 입력 즉시 결과가 출력됩니다.

---

## Excel 컬럼 형식(필수)
- `Activity Name`
- `Geography`
- `Reference Product Name`
- `Reference Product Unit`

---

## 1) 설치
```bash
git clone <REPO_URL>
cd GPT
pip install openpyxl
```

---

## 2) 실행
대화형:
```bash
python run_demo.py
```

자동 실행:
```bash
python run_demo.py --ef-excel ./emission_factor.xlsx --use-ai --name "VMQ" --geo KR --unit kg
```

---

## 3) Gemini API 키 넣는 방법 (3가지)

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
`run_demo.py` 상단의 아래 값에 직접 입력:
```python
DEMO_GEMINI_API_KEY = "여기에_키"
```

---

## 4) exe 만들기 (Windows)
```bash
pip install pyinstaller
pyinstaller --onefile run_demo.py
.\dist\run_demo.exe
```

---

## 5) 테스트
```bash
python -m unittest discover -s tests -v
```
