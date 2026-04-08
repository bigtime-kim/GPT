# PCF Mapping Prototype

Gemini API + Excel 배출계수 테이블(아래 4개 칼럼) 기준으로 바로 실행할 수 있는 프로토타입입니다.

필수 Excel 칼럼:
- `Activity Name`
- `Geography`
- `Reference Product Name`
- `Reference Product Unit`

---

## 1) 실행 전 준비
```bash
git clone <REPO_URL>
cd GPT
python --version
```

권장: Python 3.10+

Excel 로딩을 위해 `openpyxl` 설치:
```bash
pip install openpyxl
```

---

## 2) 가장 쉬운 실행
인터랙티브:
```bash
python run_demo.py
```

한 줄 실행:
```bash
python run_demo.py --name "VMQ"
```

Excel 배출계수 파일을 적용해서 실행:
```bash
python run_demo.py --ef-excel ./emission_factor.xlsx --name "electricity, medium voltage" --geo KR --unit kWh
```

---

## 3) Gemini API 키 넣는 위치
권장: 환경변수 `GEMINI_API_KEY`

### Windows PowerShell
```powershell
$env:GEMINI_API_KEY="your_gemini_api_key"
python run_demo.py --use-ai --name "Thermiga 80127"
```

### Linux/macOS
```bash
export GEMINI_API_KEY="your_gemini_api_key"
python run_demo.py --use-ai --name "Thermiga 80127"
```

직접 인자 전달(권장X):
```bash
python run_demo.py --use-ai --gemini-api-key "your_gemini_api_key"
```

> 현재는 Gemini 호출 스텁입니다. 실제 API 요청은 `run_demo.py`의 `gemini_assist_from_api_key()` 함수에 연결하면 됩니다.

---

## 4) exe 만들기 (Windows)
```bash
pip install pyinstaller
pyinstaller --onefile run_demo.py
```

실행 파일:
```powershell
.\dist\run_demo.exe
```

아이콘:
```bash
pyinstaller --onefile --icon=icon.ico run_demo.py
```

`input()/print()` 콘솔 앱이라 `--noconsole`은 사용하지 않는 것이 맞습니다.

---

## 5) 테스트
```bash
python -m unittest discover -s tests -v
```
