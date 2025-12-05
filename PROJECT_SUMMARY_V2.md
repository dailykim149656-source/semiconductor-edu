# 🎓 반도체 공정 학습 & 면접 시뮬레이터 - 프로젝트 요약

## 📋 프로젝트 개요

### 목적
재료공학/전자공학 학부생을 위한 **반도체 공정 특화 AI 학습 & 면접 시뮬레이터**

### 핵심 가치
- 🎯 **극도의 전문성**: NotebookLM을 넘어선 반도체 도메인 특화
- 🎮 **인터랙티브**: 텍스트 설명이 아닌 직접 체험
- 💼 **실전 대비**: 실제 면접 환경 시뮬레이션
- 📊 **정량 평가**: 5가지 기준 상세 점수
- 👤 **맞춤형**: 개인 이력서 기반 질문 생성

---

## 🏗️ 시스템 아키텍처

### 기술 스택

| 계층 | 기술 | 역할 |
|------|------|------|
| **AI/LLM** | OpenAI GPT-4 | 질문 생성, 답변 평가 |
| **Speech** | Azure Speech | TTS/STT (한국어 음성) |
| **RAG** | Azure AI Search | 벡터 검색 지식 베이스 |
| **Image** | DALL-E 3 | 공정 다이어그램 생성 |
| **Frontend** | Gradio | 웹 UI |
| **Backend** | Python 3.9+ | 애플리케이션 로직 |

### 시스템 구성도

```
┌─────────────────────────────────────────────────────────┐
│                    웹 브라우저 (Gradio UI)              │
│  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐               │
│  │프로필│  │수업  │  │학습  │  │면접  │               │
│  │설정  │  │자료  │  │모드  │  │모드  │               │
│  └──────┘  └──────┘  └──────┘  └──────┘               │
└─────────────────────────────────────────────────────────┘
                          ↕
┌─────────────────────────────────────────────────────────┐
│          semiconductor_simulator_v2.py (메인)           │
│  ┌───────────────────────────────────────────────────┐  │
│  │  SemiconductorSimulator 클래스                    │  │
│  │  - text_to_speech()    - search_knowledge()      │  │
│  │  - speech_to_text()    - generate_question()     │  │
│  │  - call_gpt()          - evaluate_answer()       │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
          ↕              ↕              ↕
┌────────────────┐ ┌─────────────┐ ┌──────────────┐
│ Azure OpenAI   │ │Azure Speech │ │Azure AI      │
│   GPT-4        │ │  TTS/STT    │ │   Search     │
│   DALL-E 3     │ │  ko-KR 음성 │ │  Vector DB   │
└────────────────┘ └─────────────┘ └──────────────┘

┌─────────────────────────────────────────────────────────┐
│              지원 모듈 (Supporting Modules)             │
│  ┌──────────────┐  ┌─────────────┐  ┌──────────────┐   │
│  │document_     │  │resume_      │  │process_      │   │
│  │processor.py  │  │analyzer.py  │  │simulator.py  │   │
│  │(수업자료)    │  │(이력서분석) │  │(공정시뮬)    │   │
│  └──────────────┘  └─────────────┘  └──────────────┘   │
└─────────────────────────────────────────────────────────┘
```

---

## 🎯 핵심 기능 상세

### 1. 수업자료 자동 처리 (Document Processing)

**파일:** `document_processor.py`

**프로세스:**
```
PDF/PPT/DOCX 업로드
    ↓
텍스트 추출 (PyPDF2, python-pptx, python-docx)
    ↓
GPT-4로 반도체 지식 추출
    ├─ 공정 카테고리 (증착, 식각 등)
    ├─ 핵심 개념 & 이론
    ├─ 공정 파라미터
    └─ 학습 포인트
    ↓
학습 질문 자동 생성 (5개/지식항목)
    ├─ 개념이해
    ├─ 원리설명
    ├─ 응용
    ├─ 비교
    └─ 실무
    ↓
Azure AI Search 업로드 (벡터 임베딩)
```

**지원 공정:**
- 증착: CVD, PVD, ALD, 스퍼터링
- 식각: RIE, 습식 식각, DRIE
- 리소그래피: 포토, EUV
- 이온주입, CMP, 세정, 산화, 금속화, 패키징

### 2. 이력서/자소서 분석 (Profile Analysis)

**파일:** `resume_analyzer.py`

**추출 정보:**

**이력서:**
- 학력 (대학, 학과, 학년, GPA)
- 프로젝트 경험 (주제, 공정, 성과)
- 기술 스킬
  - 증착 장비: 스퍼터링, CVD, ALD 등
  - 분석 장비: XRD, SEM, TEM, XPS 등
  - 소프트웨어: MATLAB, Python, Origin 등
- 관심 분야
- 수상/자격증

**자기소개서:**
- 동기 (왜 반도체?)
- 단기/장기 목표
- 연구 관심사
- 문제 해결 사례
- 협업 경험
- 학습 태도

**맞춤형 질문 생성 비율:**
- 경험 기반 질문: 40%
- 이론 확인 질문: 30%
- 동기/태도 질문: 20%
- 문제 해결 질문: 10%

### 3. 학습 모드 (Study Mode)

**UI 흐름:**
```
주제 입력: "CVD 증착 공정"
    ↓
난이도 선택: 기초/중급/고급
    ↓
질문 유형: 개념이해, 원리설명, 응용, 비교, 실무
    ↓
[학습 시작] 클릭
    ↓
RAG 검색 (Azure AI Search)
    ↓
GPT-4 질문 생성
    ↓
Azure Speech TTS (음성 재생)
    ↓
학생 답변 입력 (텍스트 or 음성)
    ↓
STT 변환 (음성인 경우)
    ↓
GPT-4 답변 평가 (5가지 기준)
    ↓
평가 결과 표시
    ├─ 총점 (100점)
    ├─ 기준별 점수
    ├─ 강점 & 개선점
    └─ 복습 추천 주제
```

### 4. 면접 모드 (Interview Mode)

**일반 질문:**
- 공정별 무작위 질문
- 중점 분야 선택 가능
- 실전 면접 환경

**맞춤형 질문 (프로필 기반):**
```
이력서 분석 결과 활용
    ↓
"ITO 박막 프로젝트에서 RF 파워를 150W로
 선택한 이유는?"
    ↓
"MEMS 센서 제작 시 RIE 식각에서
 어떤 문제가 있었나요?"
    ↓
"저온 ALD에 관심이 많다고 했는데,
 고온 공정 대비 장단점은?"
```

### 5. 5가지 기준 평가 시스템

| 기준 | 배점 | 평가 항목 | 예시 |
|------|------|----------|------|
| **정확성** | 30점 | 기술적 정확도, 용어, 수치 | "압력 3mTorr는 정확, 하지만 온도 단위 오류" |
| **깊이** | 25점 | 원리 이해, 메커니즘 | "플라즈마 시스 전압까지 설명함 → 깊은 이해" |
| **구조** | 20점 | 논리적 흐름, 체계성 | "단계별 설명 명확, 결론 도출 우수" |
| **응용** | 15점 | 실무 연결, 문제 해결 | "실제 프로젝트 경험과 연결하여 설명" |
| **의사소통** | 10점 | 표현력, 명확성 | "전문 용어 정확히 사용, 설명 간결" |

**피드백 구성:**
```json
{
    "scores": {
        "accuracy": 27,
        "depth": 22,
        "structure": 18,
        "application": 13,
        "communication": 9
    },
    "total_score": 89,
    "strengths": [
        "공정 파라미터를 구체적 수치로 설명",
        "플라즈마 메커니즘 정확히 이해"
    ],
    "improvements": [
        "이방성과 등방성 식각의 차이 보완 필요",
        "실무 경험 사례 추가하면 더 좋음"
    ],
    "detailed_feedback": "...",
    "recommended_topics": [
        "RIE 식각 메커니즘",
        "선택비 개념"
    ]
}
```

### 6. 공정 시뮬레이터 (Process Simulator) 🎮

**파일:** `process_simulator.py`

**CVD 시뮬레이터:**
```
슬라이더 조작:
- 압력: 1-50 mTorr
- 온도: 200-800°C
- 가스 유량: 50-500 sccm
- 증착 시간: 1-60분

실시간 결과:
- 증착 속도 (nm/min)
- 박막 두께 (nm)
- 균일도 (%)
- 입자 위험도 (%)
- 결정성 (%)

3D 시각화:
- 박막 두께 프로파일
- 균일도 분포

AI 추천:
"💡 균일도 개선: 압력을 5mTorr로 조정"
"⚠️ 입자 위험: 압력을 낮추세요"
```

**RIE 시뮬레이터:**
```
파라미터:
- RF 파워: 50-300W
- 압력: 1-50 mTorr
- CF₄ 비율: 0-100%
- 식각 시간: 1-30분

결과:
- 식각 속도, 깊이
- 이방성 (%)
- 선택비
- 표면 거칠기

3D 프로파일:
- 식각 깊이 분포
- 언더컷 시각화
```

**차별점:**
```
NotebookLM: "압력을 높이면 균일도가 감소합니다"
우리 시스템: 직접 슬라이더로 확인!
           압력 10 → 50: 균일도 95% → 75%
           그래프로 실시간 확인
```

---

## 📊 NotebookLM 대비 차별점

### 경쟁 우위 매트릭스

| 차원 | NotebookLM | 우리 시스템 | 차이 |
|------|-----------|------------|------|
| **전문성** | 범용 학습 | 반도체 특화 | ⭐⭐⭐ |
| **평가** | 일반 피드백 | 5기준 정량 평가 | ⭐⭐⭐⭐⭐ |
| **실전** | Q&A만 | 면접 시뮬레이션 | ⭐⭐⭐⭐⭐ |
| **체험** | 텍스트 | 인터랙티브 시뮬레이터 | ⭐⭐⭐⭐⭐ |
| **맞춤** | 일반 질문 | 이력서 기반 맞춤 | ⭐⭐⭐⭐ |
| **진도** | 없음 | 학습 분석 & 추천 | ⭐⭐⭐⭐ |
| **음성** | 팟캐스트 | 양방향 TTS/STT | ⭐⭐⭐ |

### 포지셔닝

```
NotebookLM:
"편하게 공부하기"
- 문서 업로드만으로 즉시 Q&A
- 무료
- 누구나 사용 가능

우리 시스템:
"실전처럼 훈련하기"
- 반도체 면접에 특화
- 정량적 평가 & 피드백
- 인터랙티브 학습
- 맞춤형 질문
```

---

## 🗂️ 파일 구조 & 책임

### 핵심 애플리케이션

```
semiconductor_simulator_v2.py (29KB)
├─ SemiconductorSimulator 클래스
│  ├─ initialize_azure_clients()    # Azure 서비스 연결
│  ├─ text_to_speech()              # TTS
│  ├─ speech_to_text()              # STT
│  ├─ search_knowledge()            # RAG 검색
│  ├─ call_gpt()                    # GPT API 호출
│  ├─ generate_study_question()    # 학습 질문 생성
│  ├─ generate_interview_question() # 면접 질문 생성
│  ├─ evaluate_answer()             # 5기준 평가
│  └─ analyze_profile()             # 프로필 분석
└─ create_gradio_interface()        # Gradio UI
```

### 지원 모듈

```
document_processor.py (17KB)
├─ SemiconductorDocumentProcessor
│  ├─ parse_pdf/pptx/docx()
│  ├─ extract_semiconductor_knowledge()
│  ├─ generate_study_questions()
│  └─ upload_to_search()

resume_analyzer.py (13KB)
├─ ResumeAnalyzer
│  ├─ extract_text_from_pdf/docx()
│  ├─ analyze_resume()
│  ├─ analyze_personal_statement()
│  └─ generate_personalized_questions()

process_simulator.py (16KB)
├─ ProcessSimulator
│  ├─ simulate_cvd()
│  ├─ simulate_rie()
│  ├─ simulate_sputtering()
│  ├─ create_3d_profile()
│  └─ get_recommendations()

init_semiconductor_db.py (12KB)
├─ SAMPLE_SEMICONDUCTOR_QUESTIONS (10개)
└─ initialize_semiconductor_db()
```

### 설정 & 문서

```
.env.template                # 환경 변수 템플릿
requirements.txt             # Python 패키지
quickstart_v2.sh            # 빠른 시작 스크립트

README.md                    # 메인 가이드
PROJECT_SUMMARY.md          # 이 파일
DIFFERENTIATION_STRATEGY.md # NotebookLM 대비 차별화
ARCHITECTURE.md             # 시스템 아키텍처
SAMPLE_DOCUMENTS_GUIDE.md   # 샘플 문서 가이드
```

---

## 🚀 설치 & 실행

### 1. 환경 설정

```bash
# 저장소 다운로드
cd semiconductor-simulator

# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt

# 환경 변수 설정
cp .env.template .env
nano .env  # API 키 입력
```

### 2. Azure 리소스 생성

**필수:**
1. Azure OpenAI (GPT-4 배포)
2. Azure Speech Services
3. Azure AI Search

**선택:**
4. Azure OpenAI DALL-E

### 3. 지식 베이스 초기화

```bash
# 샘플 질문 업로드
python init_semiconductor_db.py
```

### 4. 시뮬레이터 실행

```bash
# 메인 애플리케이션
python semiconductor_simulator_v2.py

# 또는 빠른 시작 스크립트
chmod +x quickstart_v2.sh
./quickstart_v2.sh
```

### 5. 브라우저 접속

```
http://localhost:7860
```

---

## 💰 비용 분석

### 월간 사용량 예상 (학생 50명 기준)

| 서비스 | 사용량 | 단가 | 월 비용 |
|--------|--------|------|---------|
| **Azure OpenAI (GPT-4)** | 1M 토큰 | ₩20/1K | ₩20,000 |
| **Azure Speech** | 5시간 TTS/STT | ₩12,000 | ₩12,000 |
| **Azure AI Search** | Basic 티어 | ₩100,000 | ₩100,000 |
| **DALL-E 3** | 100 이미지 | ₩400/img | ₩40,000 |
| **총계** | | | **₩172,000** |

### 비용 절감 방법

1. **Azure for Students**
   - $100/월 크레딧
   - 12개월 무료

2. **개발자 구독**
   - Visual Studio Enterprise 구독
   - $150/월 Azure 크레딧

3. **학교 라이선스**
   - Microsoft Academic Alliance
   - 교육 기관 할인

### 가격 정책

**개인 (B2C):**
- ₩9,900/월
- 월 100회 질문
- 모든 기능 사용

**학과 (B2B):**
- ₩500,000/년
- 학생 100명
- 맞춤형 질문 DB
- 교수 대시보드

**기업 (B2B):**
- 맞춤 견적
- 내부 자료 연동
- 커스텀 기능

---

## 📈 로드맵

### ✅ Phase 1 (완료 - 2024.12)

- [x] 기본 시스템 구축
- [x] Azure Speech TTS/STT 통합
- [x] 5가지 기준 평가 시스템
- [x] 이력서/자소서 분석
- [x] 맞춤형 질문 생성
- [x] 수업자료 자동 처리
- [x] RAG 지식 베이스
- [x] 공정 시뮬레이터 (CVD, RIE)
- [x] 샘플 문서 (이력서/자소서)
- [x] 로컬/Azure 환경 분리
- [x] API 키 기반 인증

### 🔄 Phase 2 (진행 중 - 2025.01)

- [ ] 게이미피케이션 (레벨, 배지, XP)
- [ ] 실전 면접 모드 (타이머, 압박감)
- [ ] 이미지 기반 질문 (SEM, XRD)
- [ ] 학습 진도 대시보드
- [ ] 약점 분석 & 추천
- [ ] 추가 공정 시뮬레이터 (스퍼터링, 리소그래피)

### 📋 Phase 3 (계획 - 2025.Q1)

- [ ] 협업 학습 모드 (팀 챌린지)
- [ ] 상황극 & 롤플레이
- [ ] 실시간 산업 데이터 연동
- [ ] 데이터 해석 훈련 (XRD, SEM)
- [ ] 적응형 커리큘럼
- [ ] 교수 대시보드

### 🌟 Phase 4 (장기 - 2025.Q2+)

- [ ] VR/AR 클린룸 시뮬레이션
- [ ] 다국어 지원 (영어, 중국어)
- [ ] 산학 협력 (기업 연동)
- [ ] 모바일 앱
- [ ] 실습 장비 예약 연동

---

## 🎯 성공 지표 (KPI)

### 학습 효과
- 평균 점수 향상: 초기 60점 → 3개월 후 80점+
- 약점 개선율: 70% 이상
- 학습 완료율: 80% 이상

### 사용자 만족도
- NPS (Net Promoter Score): 50+
- 재방문율: 주 3회 이상
- 평균 세션 시간: 30분+

### 비즈니스
- 학과 계약: 10개 대학
- 기업 계약: 3개 기업
- MAU (Monthly Active Users): 500명

---

## 🤝 기여 방법

### 버그 리포트
1. GitHub Issues 등록
2. 재현 방법 상세 기술
3. 스크린샷/로그 첨부

### 기능 제안
1. 새로운 공정 추가 (예: ALE, APC)
2. 평가 기준 개선
3. UI/UX 개선

### 코드 기여
1. Fork 후 feature branch 생성
2. 코드 작성 및 테스트
3. Pull Request 제출

---

## 📞 문의

### 기술 지원
- Email: tech-support@semiconductor-sim.com
- Discord: https://discord.gg/semiconductor

### 비즈니스 문의
- Email: business@semiconductor-sim.com
- 학과/기업 도입 상담

### 개발자
- GitHub: @your-username
- LinkedIn: your-profile

---

## 📜 라이선스

MIT License

Copyright (c) 2024 Semiconductor Simulator

---

## 🙏 감사의 글

- **Azure AI**: 강력한 AI 서비스 제공
- **OpenAI**: GPT-4 & DALL-E 3
- **Gradio**: 빠른 UI 구축
- **반도체 전공 교수님들**: 도메인 자문
- **베타 테스터 학생들**: 귀중한 피드백

---

**📚 자세한 내용은 [README.md](README.md)를 참조하세요**

**🚀 지금 바로 시작: `./quickstart_v2.sh`**
