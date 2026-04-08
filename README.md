# PCF Mapping Prototype

처음 보시면 헷갈릴 수 있어서, **다운로드부터 실행(.exe 포함)까지** 순서대로 설명합니다.

## 0) 이 프로젝트는 뭐하는 건가?
공장 활동명(예: `VMQ`, `EN AW 6005A T6`, `Thermiga 80127`)을 받아서,
LCA dataset 후보로 매핑하는 **프로토타입**입니다.

- 먼저 규칙 기반(deterministic)으로 찾고
- 못 찾는 애매한 입력만 AI 보조를 쓰는 구조입니다.

---

## 1) 뭘 다운받아야 해?
이 저장소 코드 전체를 받으면 됩니다.

```bash
git clone <REPO_URL>
cd GPT
```

> `<REPO_URL>`은 이 저장소 주소로 바꿔서 사용하세요.

Python 3.10+가 필요합니다.

---

## 2) 먼저 Python으로 실행 확인 (필수)
실행 파일(.exe) 만들기 전에 이 단계가 먼저 정상이어야 합니다.

### 2-1) 인터랙티브 실행
```bash
python run_demo.py
```

실행되면 `활동명 입력:`이 뜹니다.
예: `VMQ` 입력 → 결과 출력.

### 2-2) 한 줄 실행
```bash
python run_demo.py --name "VMQ"
```

### 2-3) AI fallback 테스트
```bash
python run_demo.py --name "Thermiga 80127" --use-ai
```

---

## 3) AI API 키는 어디에 넣어?
권장 방식은 **환경변수**입니다.

### Linux / macOS
```bash
export OPENAI_API_KEY="your_api_key_here"
python run_demo.py --use-ai
```

### Windows PowerShell
```powershell
$env:OPENAI_API_KEY="your_api_key_here"
python run_demo.py --use-ai
```

또는 임시로 `--api-key` 인자를 줄 수 있습니다(권장 X).

```bash
python run_demo.py --use-ai --api-key "your_api_key_here"
```

> 실제 API 호출 로직은 `run_demo.py`의 `ai_assist_from_api_key()` 함수 위치에 연결하면 됩니다.

---

## 4) exe 만들기 (Windows)
`run_demo.py`는 실행 시작 파일(main)입니다. 이 파일을 exe로 패키징하면 됩니다.

### 4-1) PyInstaller 설치
```bash
pip install pyinstaller
pyinstaller --version
```

### 4-2) exe 빌드
```bash
pyinstaller --onefile run_demo.py
```

빌드 후:
- `build/`
- `dist/`

실행 파일:
- `dist/run_demo.exe`

### 4-3) 실행
PowerShell:
```powershell
.\dist\run_demo.exe
```

또는 탐색기에서 `dist/run_demo.exe` 더블클릭.

### 4-4) 아이콘 넣기(선택)
```bash
pyinstaller --onefile --icon=icon.ico run_demo.py
```

> `input()/print()` 기반 콘솔 앱이므로 `--noconsole`은 사용하지 않는 게 맞습니다.

---

## 5) 테스트 실행
```bash
python -m unittest discover -s tests -v
```

---

## 6) 코드 직접 써서 실행하고 싶으면
```python
from mapping_engine import MappingEngine

knowledge = {
    "abbreviation": {"vmq": "silicone rubber family"},
    "synonym": {"en aw 6005a t6": "wrought aluminium extrusion family"},
    "family": {
        "silicone rubber family": "silicone rubber",
        "wrought aluminium extrusion family": "wrought aluminium extrusion family",
    },
    "proxy": {"pbt/pom": "engineering plastic"},
    "db_catalog": {
        "silicone rubber": "ecoinvent:silicone_rubber_dataset",
        "wrought aluminium extrusion family": "ecoinvent:alu_extrusion_dataset",
        "engineering plastic": "ecoinvent:eng_plastic_proxy_dataset",
    },
}

engine = MappingEngine(knowledge)
print(engine.map_activity("VMQ"))
print(engine.map_activity("EN AW 6005A T6"))
```
