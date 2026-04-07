# PCF Mapping Prototype

간단한 deterministic-first 매핑 엔진 프로토타입입니다.

## 1) 실행 환경
- Python 3.10+

## 2) 빠른 실행
아래 명령을 저장소 루트(`/workspace/GPT`)에서 실행하세요.

```bash
python -c "from mapping_engine import MappingEngine; k={'abbreviation':{'vmq':'silicone rubber family'},'family':{'silicone rubber family':'silicone rubber'},'db_catalog':{'silicone rubber':'ecoinvent:silicone_rubber_dataset'}}; e=MappingEngine(k); r=e.map_activity('VMQ'); print(r)"
```

## 3) 테스트 실행
```bash
python -m unittest discover -s tests -v
```

## 4) 인터랙티브 예시
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

## 5) AI fallback 넣는 방법
```python
def fake_ai(payload):
    return {
        "proxy_candidates": ["ecoinvent:eng_plastic_proxy_dataset"],
        "confidence": 0.62,
        "review_required": True,
        "reason": "Long-tail trade name interpreted",
    }

engine = MappingEngine(knowledge, ai_assist=fake_ai)
print(engine.map_activity("Thermiga 80127"))
```

## 6) 업로드 시점 확인
```python
from mapping_engine import required_uploads

print(required_uploads("ai_connection"))
print(required_uploads("knowledge_bootstrap"))
print(required_uploads("go_live"))
```
