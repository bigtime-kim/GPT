# PCF Activity Mapping Engine Architecture (Hybrid Deterministic + AI)

## 1) 목표
공장/시스템별로 제각각인 activity name을 해석해 Ecoinvent/Sphera dataset으로 대량 매핑한다. 
핵심 목표는 **100% 자동확정**이 아니라, 모든 입력을 아래 5가지 상태 중 하나로 귀결시키는 것이다.

1. direct exact match
2. normalized family match
3. proxy candidate match
4. composite decomposition match
5. review required

---

## 2) 핵심 분리 원칙

### A. 뼈대 기능 (제품 내부 고정 구현)
- ingestion, preprocessing, parser/canonicalization pipeline
- standard activity object builder
- material/waste/energy/wastewater domain engines
- candidate generation, policy engine, ranking/scoring
- auto-accept/review queue, mapping registry
- IMDS/BOM granularity control

### B. AI API 적용 구간 (해석/추론 보조 전용)
- 애매한 name type 분류 보조
- long-tail canonicalization
- supplier/model/part number 해석 보조
- composite decomposition 보조
- proxy 추천 / search-result reranking 보조
- reviewer-friendly reason text 생성

### C. 지식 데이터 (Excel 업로드)
- DB catalog + enrichment metadata
- synonym/abbreviation dictionary
- material ontology/family table
- spec/alloy master
- supplier/grade/model master
- process knowledge
- waste matrix, energy table, wastewater table
- policy/geography rules
- approved mapping registry + approved proxy library

---

## 3) 전체 아키텍처 레이어

### 3.1 Deterministic Engine Layer
1. Input ingestion
2. Preprocessing
3. Name type classifier (rule-first)
4. Parser & canonicalization
5. Standard activity object builder
6. Role/category determination
7. IMDS/BOM granularity control
8. Domain mapping engines
9. Candidate generation
10. Policy filtering
11. Ranking + confidence scoring
12. Auto-accept / review queue
13. Mapping registry write-back

### 3.2 AI Assist Layer
- deterministic 결과가 불충분할 때만 호출
- 입력은 구조화 payload 사용
- 출력은 JSON schema 고정

### 3.3 Knowledge Data Layer
- 엑셀 기반 주입/수정
- 버전관리(업로드일/버전/프로젝트 적용범위) 필수

---

## 4) 표준 Activity Object (내부 공통 스키마)

```json
{
  "raw_name": "",
  "normalized_name": "",
  "canonical_form": "",
  "name_type": "",
  "category": "material|component|waste|energy|wastewater",
  "role": "input|output",
  "state": "",
  "function_hint": "",
  "hierarchy_level": "",
  "treatment_route": "",
  "geography_hint": "",
  "source_type": "",
  "mapping_mode": "functional|material|hybrid",
  "trace_log": []
}
```

---

## 5) AI API 인터페이스 권장안

### 5.1 Request
```json
{
  "raw_name": "",
  "source_type": "",
  "process_name": "",
  "unit": "",
  "treatment_hint": "",
  "hierarchy": {},
  "knowledge_hits": [],
  "search_top_n": []
}
```

### 5.2 Response
```json
{
  "name_type": "",
  "canonical_form": "",
  "category": "",
  "state": "",
  "function_hint": "",
  "decomposition_suggestion": [],
  "proxy_candidates": [],
  "confidence": 0.0,
  "review_required": true,
  "reason": ""
}
```

---

## 6) 도메인 엔진 요약

### Material/Component
- exact/family/proxy 매핑
- 가공공정 추가 (예: injection moulding, extrusion)

### Waste
- 물질군 분류 + 처리경로 분기
- market/treatment/processing policy 적용

### Energy
- electricity/heat/LNG/steam 분기
- source→technology→output/voltage→geography

### Wastewater
- average/unpolluted/process-specific/sludge/leachate 분기

---

## 7) 운영 플로우
1. Excel 지식 업로드
2. DB catalog index 생성
3. Activity batch 업로드
4. deterministic 1차 처리
5. low-confidence만 AI API 보조 호출
6. 후보 랭킹/확정
7. auto-accept vs review 분기
8. reviewer 승인
9. mapping registry 재학습(재사용)

---

## 8) 단계별 도입 로드맵

### Phase 1 (MVP)
- DB catalog, synonym/abbreviation, ontology
- exact/family/proxy 기본 엔진
- waste/energy/wastewater 기본 분기
- review queue

### Phase 2
- spec/alloy master, process addition
- IMDS/BOM granularity
- approved mapping registry 본격 활용
- AI canonicalization 보조

### Phase 3
- supplier/grade/model master
- composite decomposition 고도화
- reranking/설명 자동화

---

## 9) 업로드 트리거(사용자 액션 필요 시점)
다음 단계에서 사용자(API key, Excel 파일) 업로드가 필요하다.

1. **AI API 연결 직전**
   - 필요 항목: API key, model 선택, rate limit 정책
2. **Knowledge bootstrapping 직전**
   - 필요 항목: MVP 필수 Excel 세트
3. **정책 적용/운영 전환 직전**
   - 필요 항목: policy/geography table, approved mapping registry 최신본

---

## 10) 최종 한 줄 정리
**Deterministic 엔진을 제품 내부 뼈대로 두고, AI는 long-tail 해석/재랭킹 보조로만 제한하며, 정답의 기반은 Excel 지식 데이터(사전·규칙·매트릭스·승인이력)로 운영하는 하이브리드 구조를 채택한다.**
