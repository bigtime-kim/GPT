# PCF Mapping Prototype

처음 보시면 헷갈릴 수 있어서, **다운로드부터 실행까지** 딱 3단계로 설명합니다.

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

## 2) 바로 실행(가장 쉬운 방법)
아래 한 줄로 데모 실행이 됩니다.

```bash
python run_demo.py --name "VMQ"
```

AI fallback까지 보고 싶으면:

```bash
python run_demo.py --name "Thermiga 80127" --use-ai
```

---

## 3) 테스트 돌려보기
정상 동작 확인은 아래 명령으로 하면 됩니다.

```bash
python -m unittest discover -s tests -v
```

---

## 4) 코드 직접 써서 실행하고 싶으면
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

---

## 5) API key/Excel은 언제 넣어?
현재는 샘플 데이터로 동작하는 프로토타입입니다.
실서비스 연결 시 아래 순서로 넣으면 됩니다.

1. AI 연결 직전: API key, model, rate limit 정책
2. 지식 부트스트랩: DB catalog, synonym/abbreviation, ontology, spec/alloy, waste/energy/policy, mapping registry
3. 운영 전환 직전: policy/geography 최신본, approved mapping registry 최신본
