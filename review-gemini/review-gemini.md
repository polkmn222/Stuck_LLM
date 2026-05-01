# Stuck LLM Project Review

이 보고서는 Codex가 작성한 현재 코드베이스의 구조와 구현 상태를 분석하고, 개선 사항 및 향후 진행 방향을 제안합니다.

## 1. 현재 폴더 구성 및 구조 분석

### 백엔드 (src/backend)
*   **기능 기반 구조 (Feature-based Structure):** `app/features/` 아래에 각 도메인(analysis, backtest, market_data 등)별로 router, schemas, service가 분리되어 있어 확장성이 매우 뛰어납니다.
*   **공통 로직 분리:** `app/shared/`에 암호화, 상태 저장, 런타임 설정 등 공통 모듈이 잘 관리되고 있습니다.
*   **방대한 테스트 케이스:** `tests/` 폴더에 90개가 넘는 단계별(phase) 테스트가 존재하며, 이는 매우 견고한 TDD 또는 체계적인 개발 프로세스를 따랐음을 보여줍니다.

### 프론트엔드 (src/frontend)
*   **현대적인 스택:** React 19, Vite, TypeScript, Vitest를 사용하고 있습니다.
*   **백엔드와 일관된 구조:** 백엔드와 마찬가지로 `src/features/` 구조를 사용하여 일관성을 유지하고 있습니다.

### 문서화 및 설정
*   **명확한 디자인 가이드:** `DESIGN.md`에 색상, 타이포그래피, 레이아웃 등 명확한 디자인 시스템이 정의되어 있어 일관된 UI 구현이 가능합니다.
*   **실행 스크립트:** `run-all.sh` 등을 통해 백엔드와 프론트엔드를 한 번에 실행할 수 있는 편의성을 제공합니다.

---

## 2. 문제점 및 개선 사항

### 백엔드 (Backend)
1.  **방대한 서비스 파일 (Monolithic Service):** `market_data/service.py` 파일이 1,000 라인을 넘어가고 있습니다. 다양한 데이터 소스나 처리 로직이 섞여 있어 유지보수가 어려울 수 있습니다.
    *   *개선:* 데이터 제공자(Provider) 패턴을 도입하여 여러 파일로 분리하는 것이 좋습니다.
2.  **상태 저장 방식 (State Store):** 현재 `.local/stuck_llm_state.json` 파일에 상태를 저장합니다. MVP로는 적합하지만, 동시성(Concurrency)이나 데이터 무결성 측면에서 한계가 있습니다.
    *   *개선:* SQLite와 SQLAlchemy(또는 Tortoise ORM)를 도입하여 실제 데이터베이스 구조로 전환하는 것을 권장합니다.
3.  **테스트 구조:** `tests/` 폴더에 모든 테스트가 평면적으로 나열되어 있습니다.
    *   *개선:* 기능별로 서브디렉토리를 만들거나, 각 기능(feature) 폴더 내부에 `tests/`를 두어 응집도를 높일 수 있습니다.

### 프론트엔드 (Frontend)
1.  **미니멀한 종속성:** 현재 상태 관리 라이브러리나 UI 컴포넌트 라이브러리가 없습니다.
    *   *개선:* 복잡해지는 상태 관리를 위해 `Zustand`나 `TanStack Query` 도입을 고려하고, `DESIGN.md`에 맞춘 공통 컴포넌트 구축이 필요합니다.

---

## 3. 향후 진행 제안 (Next Steps)

### 단기적 목표 (Short-term)
1.  **UI/UX 구현:** `DESIGN.md`의 디자인 가이드를 바탕으로 기본적인 차트와 채팅 인터페이스를 실제 React 컴포넌트로 구현합니다.
2.  **데이터베이스 전환:** JSON 파일 저장 방식을 SQLite로 전환하여 데이터 영속성과 안정성을 확보합니다.
3.  **Market Data 리팩토링:** `market_data/service.py`를 리팩토링하여 모듈성을 강화합니다.

### 중장기적 목표 (Long-term)
1.  **통계 모델링 강화:** 이미 `statsmodels`를 활용한 기본적인 가격 추세 분석 유틸리티(`src/backend/app/shared/stats_utils.py`)를 추가했습니다. 이를 확장하여 ARIMA 모델 등을 통한 가격 예측이나 변동성 분석 기능을 강화할 수 있습니다.
2.  **실시간성 강화:** WebSockets을 도입하여 시장 데이터의 실시간 업데이트를 구현합니다.
3.  **고급 에이전트 오케스트레이션:** 단순한 챗봇을 넘어, 복합적인 시장 분석이나 뉴스 요약을 수행하는 멀티 스텝 에이전트 로직을 강화합니다.
3.  **성능 최적화:** 백엔드 응답 속도 개선을 위해 `news_cache_processing_store` 등 현재 스캐폴드에 있는 캐싱 로직을 본격적으로 활성화합니다.

---
**작성자:** Gemini CLI (Senior Software Engineer Role)
**날짜:** 2026-05-01
