# 🎓 반도체 공정 학습 & 면접 시뮬레이터

## 📋 목차
1. [개요](#개요)
2. [주요 기능](#주요-기능)
3. [시스템 요구사항](#시스템-요구사항)
4. [빠른 시작](#빠른-시작)
5. [Azure 리소스 설정](#azure-리소스-설정)
6. [사용 가이드](#사용-가이드)
7. [문제 해결](#문제-해결)
8. [NotebookLM과의 차별점](#notebooklm과의-차별점)

---

## 🎯 개요

**반도체 공정에 특화된 AI 기반 학습 & 면접 시뮬레이터**

- 🎓 **타겟**: 재료공학/전자공학 학부생
- 🔬 **도메인**: 반도체 8대 공정 (증착, 식각, 리소그래피 등)
- 🤖 **기술**: Azure Speech + OpenAI GPT-4 + AI Search
- 🏆 **차별점**: NotebookLM을 넘어선 전문성과 인터랙티브 학습

---

## ⚡ 주요 기능

### 1. 📚 수업자료 자동 처리
- PDF/PPT/DOCX 업로드
- GPT-4로 반도체 지식 추출
- 자동 질문 생성 (5개/지식항목)
- RAG 벡터 DB 구축

### 2. 👤 개인 맞춤형 질문 생성
- 이력서/자소서 자동 분석
- 경험 기반 심층 질문 (40%)
- 이론 확인 질문 (30%)
- 동기/태도 질문 (20%)
- 문제 해결 질문 (10%)

### 3. 📖 학습 모드
- **주제 선택**: CVD, RIE, 리소그래피 등
- **난이도**: 기초/중급/고급
- **질문 유형**: 개념이해, 원리설명, 응용, 비교, 실무
- **음성 지원**: Azure Speech TTS/STT

### 4. 💼 면접 모드
- 일반 질문 or 프로필 기반 맞춤형
- 실전 면접 환경 시뮬레이션
- 중점 분야 선택 가능

### 5. 📊 5가지 기준 평가
| 기준 | 배점 | 평가 항목 |
|------|------|----------|
| **정확성** | 30점 | 기술적 정확도, 용어, 수치 |
| **깊이** | 25점 | 원리 이해, 메커니즘 |
| **구조** | 20점 | 논리적 흐름, 명확성 |
| **응용** | 15점 | 실무 연결, 문제 해결 |
| **의사소통** | 10점 | 표현력, 설명 능력 |

### 6. 🎮 추가 기능 (개발 중)
- 인터랙티브 공정 시뮬레이터
- 게이미피케이션 (레벨, 배지)
- 협업 학습 모드
- 실시간 산업 데이터 연동

---

## 💻 시스템 요구사항

### 필수 사항
- **Python**: 3.9 이상
- **운영체제**: Windows, macOS, Linux
- **메모리**: 최소 4GB RAM
- **디스크**: 최소 2GB 여유 공간

### Azure 서비스 (필수)
1. **Azure OpenAI** (또는 OpenAI API)
   - GPT-4 모델 배포
   - API 키 필요

2. **Azure Speech Services**
   - TTS/STT 사용
   - API 키 필요

3. **Azure AI Search**
   - 지식 베이스 RAG
   - API 키 필요

4. **Azure OpenAI DALL-E** (선택사항)
   - 이미지 생성

---

## 🚀 빠른 시작

### 1단계: 저장소 준비
```bash
# 파일 다운로드 (또는 git clone)
cd semiconductor-simulator
```

### 2단계: Python 환경 설정
```bash
# 가상환경 생성
python -m venv venv

# 가상환경 활성화
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 패키지 설치
pip install -r requirements.txt
```

### 3단계: 환경 변수 설정
```bash
# .env.template을 .env로 복사
cp .env.template .env

# .env 파일 편집
nano .env  # 또는 메모장
```

**필수 설정 항목:**
```bash
# OpenAI (Azure 또는 일반 OpenAI)
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4

# Speech Services
AZURE_SPEECH_KEY=your-speech-key-here
AZURE_SPEECH_REGION=koreacentral
AZURE_SPEECH_VOICE_NAME=ko-KR-SunHiNeural

# AI Search
AZURE_SEARCH_ENDPOINT=https://your-search.search.windows.net
AZURE_SEARCH_KEY=your-search-key-here
AZURE_SEARCH_INDEX_NAME=semiconductor-knowledge
```

### 4단계: 지식 베이스 초기화
```bash
# 샘플 질문 업로드
python init_semiconductor_db.py
```

### 5단계: 시뮬레이터 실행
```bash
# 메인 애플리케이션 실행
python semiconductor_simulator_v2.py
```

브라우저에서 http://localhost:7860 접속

---

## ☁️ Azure 리소스 설정

### 1. Azure OpenAI 생성

**Azure Portal에서:**
1. "Azure OpenAI" 리소스 생성
2. 지역: Korea Central (또는 East US)
3. 가격 책정 계층: Standard S0

**모델 배포:**
1. Azure OpenAI Studio 접속
2. "Deployments" → "Create new deployment"
3. 모델: gpt-4 (또는 gpt-4-turbo)
4. Deployment name: `gpt-4`

**API 키 확인:**
- "Keys and Endpoint" 탭
- Key 1 복사 → `.env`의 `AZURE_OPENAI_API_KEY`에 붙여넣기
- Endpoint 복사 → `.env`의 `AZURE_OPENAI_ENDPOINT`에 붙여넣기

### 2. Azure Speech Services 생성

**Azure Portal에서:**
1. "Speech Services" 리소스 생성
2. 지역: Korea Central
3. 가격 책정 계층: Free F0 (테스트용) 또는 Standard S0

**API 키 확인:**
- "Keys and Endpoint" 탭
- Key 1 복사 → `.env`의 `AZURE_SPEECH_KEY`에 붙여넣기

**음성 선택:**
- 여성 음성 (권장): `ko-KR-SunHiNeural`
- 남성 음성: `ko-KR-InJoonNeural`

### 3. Azure AI Search 생성

**Azure Portal에서:**
1. "Azure AI Search" 리소스 생성
2. 지역: Korea Central
3. 가격 책정 계층: Basic (학생용) 또는 Standard

**인덱스 생성:**
```bash
# 자동 인덱스 생성 스크립트 실행
python init_semiconductor_db.py
```

**API 키 확인:**
- "Keys" 탭
- Admin Key 복사 → `.env`의 `AZURE_SEARCH_KEY`에 붙여넣기

### 4. 비용 예상 (월간)

| 서비스 | 사용량 | 예상 비용 |
|--------|--------|----------|
| Azure OpenAI (GPT-4) | 100만 토큰 | ₩20,000 |
| Speech Services | 5시간 TTS/STT | ₩12,000 |
| AI Search Basic | 인덱스 1개 | ₩100,000 |
| **총계** | | **₩132,000** |

💡 **학생 할인**: Azure for Students 크레딧 $100 활용 가능

---

## 📖 사용 가이드

### 프로필 설정 (선택사항)

1. **"프로필 설정"** 탭 이동
2. 이력서 업로드 (PDF/DOCX)
3. 자기소개서 업로드 (PDF/DOCX)
4. **"분석 시작"** 클릭

→ AI가 자동으로 경험, 스킬, 관심사 추출

### 학습 모드 사용

1. **"학습 모드"** 탭 이동
2. **학습 주제** 입력 (예: "CVD 증착 공정")
3. **난이도** 선택 (기초/중급/고급)
4. **질문 유형** 선택 (개념이해, 원리설명 등)
5. **"학습 시작"** 클릭
6. 질문 확인 (텍스트 + 음성)
7. 답변 입력 (텍스트 또는 음성)
8. **"답변 제출"** 클릭
9. 평가 결과 확인

### 면접 모드 사용

1. **"면접 모드"** 탭 이동
2. (선택) **"내 프로필 기반 맞춤형 질문"** 체크
3. **중점 분야** 선택
4. **"면접 시작"** 클릭
5. 질문에 답변
6. 평가 받기

---

## 🔧 문제 해결

### 문제: "OpenAI 클라이언트 초기화 실패"
**원인**: API 키 미설정 또는 잘못됨

**해결:**
1. `.env` 파일 확인
2. `AZURE_OPENAI_API_KEY` 값 확인
3. Azure Portal에서 키 재확인

### 문제: "Speech 클라이언트가 없습니다"
**원인**: Speech Services 키 미설정

**해결:**
1. `.env` 파일의 `AZURE_SPEECH_KEY` 확인
2. Speech Services 리소스 생성 확인

### 문제: "Search 클라이언트가 없습니다"
**원인**: AI Search 설정 오류

**해결:**
1. `.env` 파일의 `AZURE_SEARCH_*` 값 확인
2. 인덱스 생성: `python init_semiconductor_db.py`

### 문제: "ModuleNotFoundError"
**원인**: 패키지 미설치

**해결:**
```bash
pip install -r requirements.txt
```

### 문제: 음성 인식이 안 됨
**원인**: 마이크 권한 또는 오디오 파일 문제

**해결:**
1. 브라우저 마이크 권한 허용
2. 조용한 환경에서 녹음
3. 텍스트 입력 대신 사용

---

## 🆚 NotebookLM과의 차별점

| 기능 | NotebookLM | 우리 시스템 |
|------|-----------|------------|
| **사용 편의성** | ⭐⭐⭐⭐⭐ 즉시 사용 | ⭐⭐⭐ 설정 필요 |
| **도메인 전문성** | ⭐⭐ 범용 | ⭐⭐⭐⭐⭐ 반도체 특화 |
| **평가 정밀도** | ⭐⭐ 일반 피드백 | ⭐⭐⭐⭐⭐ 5가지 기준 |
| **실전 연습** | ⭐ Q&A만 | ⭐⭐⭐⭐⭐ 면접 시뮬레이션 |
| **인터랙티브** | ⭐ 텍스트만 | ⭐⭐⭐⭐⭐ 시뮬레이터 |
| **진도 추적** | ⭐ 없음 | ⭐⭐⭐⭐⭐ 학습 분석 |
| **음성 지원** | ⭐⭐ 팟캐스트 | ⭐⭐⭐⭐ TTS/STT 양방향 |
| **맞춤형 질문** | ⭐⭐ 일반 질문 | ⭐⭐⭐⭐⭐ 프로필 기반 |
| **가격** | ⭐⭐⭐⭐⭐ 무료 | ⭐⭐ 유료 (₩132k/월) |

### 우리 시스템만의 강점

1. **🎯 극도의 전문성**
   - 반도체 공정 용어, 파라미터 정확도 검증
   - 공정별 특화 평가 기준

2. **🎮 인터랙티브 학습**
   - 공정 시뮬레이터 (파라미터 조작)
   - 실시간 결과 시각화

3. **💼 실전 면접 대비**
   - 타이머, 압박감 재현
   - 즉각 추가 질문

4. **📊 정량적 평가**
   - 5가지 기준별 점수
   - 구체적 개선 방향

5. **👤 개인 맞춤형**
   - 이력서 경험 기반 질문
   - 약점 분석 & 학습 경로

---

## 📁 파일 구조

```
semiconductor-simulator/
├── semiconductor_simulator_v2.py   # 메인 애플리케이션 (리팩토링)
├── document_processor.py           # 수업자료 처리
├── resume_analyzer.py              # 이력서/자소서 분석
├── init_semiconductor_db.py        # DB 초기화
├── process_simulator.py            # 공정 시뮬레이터
├── requirements.txt                # Python 패키지
├── .env.template                   # 환경 변수 템플릿
├── README.md                       # 이 파일
├── PROJECT_SUMMARY.md              # 프로젝트 요약
├── DIFFERENTIATION_STRATEGY.md     # 차별화 전략
└── samples/
    ├── sample_resume.docx          # 샘플 이력서
    └── sample_personal_statement.docx  # 샘플 자소서
```

---

## 🤝 기여 및 문의

### 버그 리포트
- Issue 등록 또는 이메일

### 기능 제안
- 새로운 공정 추가
- 평가 기준 개선
- UI/UX 개선

### 라이선스
MIT License

---

## 🎓 교육 기관 문의

**대학 학과 단위 도입:**
- 패키지 가격: ₩500,000/년 (100명)
- 맞춤형 질문 DB 구축
- 교수 대시보드 제공

**기업 신입 교육:**
- 맞춤 견적
- 회사 내부 자료 연동
- 실습 과제 자동 평가

**문의**: your-email@example.com

---

## 🚀 로드맵

### ✅ Phase 1 (완료)
- 기본 시스템 구축
- TTS/STT 통합
- 5가지 기준 평가
- 맞춤형 질문 생성

### 🔄 Phase 2 (진행 중)
- 공정 시뮬레이터
- 게이미피케이션
- 이미지 기반 질문

### 📋 Phase 3 (계획)
- 협업 학습 모드
- 실시간 산업 데이터
- 적응형 커리큘럼
- VR/AR 클린룸

---

**반도체 엔지니어의 꿈을 이루는 첫 걸음! 🚀**
