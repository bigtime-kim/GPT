# Implementation Checklist (3-Layer Separation)

## 결론
현재 프로토타입은 요청한 3분리 원칙(뼈대 기능 / AI API / 지식데이터)을 코드 레벨에서 분리해 구현했다.

## 1) 뼈대 기능 (Deterministic)
- 위치: `mapping_engine.py`
- 포함 기능:
  - preprocessing (`preprocess`)
  - name type 분류 (`classify_name_type`)
  - canonicalization (`canonicalize`)
  - deterministic 후보 생성 (`generate_candidates`)
  - 최종 매핑/신뢰도/리뷰분기 (`map_activity`)
  - 고정 파일명 Excel 로딩 연계는 `run_demo.py`에서 주입

판정: ✅ 구현됨

## 2) AI API 적용 부분 (보조 추론)
- 위치: `run_demo.py`
- 포함 기능:
  - Gemini 호출 함수 (`_call_gemini_structured`)
  - 실패 시 deterministic-safe fallback (`gemini_assist_from_api_key`)
  - AI 사용 여부는 옵션/입력으로 제어 (`resolve_ai_mode`)

판정: ✅ 구현됨 (보조 역할로 제한)

## 3) 지식 데이터 적용 부분 (직접 주입)
- 위치:
  - 엑셀 스키마 강제 로더: `mapping_engine.py`의 `load_ef_excel`
  - 고정 파일명 로딩 정책: `run_demo.py`의 `DEFAULT_EF_FILENAME = emission_factor.xlsx`
- 요구 칼럼:
  - Activity Name
  - Geography
  - Reference Product Name
  - Reference Product Unit

판정: ✅ 구현됨

## 운영 확인 포인트
1. 실행 폴더에 `emission_factor.xlsx` 파일 배치
2. `python run_demo.py` 실행
3. AI 사용 시 Gemini key 입력 또는 `GEMINI_API_KEY` 환경변수 설정
4. 물질명 입력 후 결과 확인
