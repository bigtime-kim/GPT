# PCF Mapping Prototype

질문 주신 3가지를 먼저 답하면:

1. **엑셀파일은 같은 폴더에 넣으면 되나요?**  
   → **네.** 실행 폴더에 `emission_factor.xlsx` 이름으로 두면 자동으로 읽습니다. (또는 `--ef-excel`로 경로 지정)  
2. **실행파일에서 API 키를 바로 입력할 수 있나요?**  
   → **네.** `Gemini AI fallback 사용?`에 `y`를 선택하면 키 입력창이 뜹니다. (또는 환경변수 `GEMINI_API_KEY`)  
3. **그다음 물질명을 넣으면 바로 실행되나요?**  
   → **네.** `물질/활동명 입력:`에 입력하면 즉시 매핑 결과가 출력됩니다.

---

## Excel 컬럼 형식(필수)
- `Activity Name`
- `Geography`
- `Reference Product Name`
- `Reference Product Unit`

---

## 가장 쉬운 실행 (대화형)
```bash
python run_demo.py
```

대화형 순서:
1) 엑셀 경로 입력 (엔터 시 기본 `emission_factor.xlsx` 자동 탐색)
2) Gemini AI fallback 사용 여부 (y/N)
3) y 선택 시 Gemini API 키 입력(마스킹)
4) 물질/활동명 입력
5) 결과 출력

---

## 자동 실행 (명령어 한 줄)
```bash
python run_demo.py --ef-excel ./emission_factor.xlsx --use-ai --name "VMQ" --geo KR --unit kg
```

---

## Gemini 키 입력 방법
### 방법 A) 실행 중 직접 입력
- `python run_demo.py` 실행
- `Gemini AI fallback 사용? (y/N)`에서 `y`
- 키 입력

### 방법 B) 환경변수 사용 (권장)
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

---

## exe 만들기 (Windows)
```bash
pip install pyinstaller
pyinstaller --onefile run_demo.py
```

실행:
```powershell
.\dist\run_demo.exe
```

`input()/print()` 콘솔 앱이라 `--noconsole`은 사용하지 않는 것이 맞습니다.

---

## 테스트
```bash
python -m unittest discover -s tests -v
```
