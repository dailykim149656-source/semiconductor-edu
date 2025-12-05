# ⚡ 반도체 공정 학습 & 면접 시뮬레이터

## 🎓 학부생을 위한 맞춤형 반도체 학습 플랫폼

Azure AI 기반 반도체 공정 전용 학습 및 면접 준비 시스템입니다.

---

## 🌟 특징

### 🎯 도메인 특화
- 반도체 공정 전문 지식 (증착, 식각, 리소그래피 등)
- 학부 수업자료 기반 RAG 시스템
- 실전 면접 질문 데이터베이스

### 📚 개인 맞춤형 학습
- 이력서/자소서 분석으로 개인 경험 파악
- 관심 분야 기반 맞춤형 질문 생성
- 학습 이력 추적 및 약점 분석

### 🔊 실감 나는 시뮬레이션
- Custom Voice로 교수님/면접관 음성 재현
- 음성/텍스트 답변 모두 지원
- 상세한 평가 및 피드백

### 📖 수업자료 자동 처리
- PDF, PPT, DOCX 자동 파싱
- 핵심 개념 및 이론 추출
- 학습 질문 자동 생성

---

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# 저장소 다운로드
cd semiconductor-simulator

# 환경 변수 설정
cp .env.template .env
# .env 파일 편집

# 의존성 설치
pip install -r requirements.txt
```

### 2. Azure 리소스 생성

```bash
# Speech Service (Custom Voice)
az cognitiveservices account create \
    --name semiconductor-speech \
    --resource-group semiconductor-rg \
    --kind SpeechServices \
    --sku S0 \
    --location koreacentral

# OpenAI Service
az cognitiveservices account create \
    --name semiconductor-openai \
    --resource-group semiconductor-rg \
    --kind OpenAI \
    --sku S0 \
    --location eastus

# AI Search
az search service create \
    --name semiconductor-search \
    --resource-group semiconductor-rg \
    --sku basic \
    --location koreacentral
```

### 3. 실행

```bash
python semiconductor_simulator.py
```

http://localhost:7860 접속!

---

## 📂 파일 구조

```
semiconductor-simulator/
├── semiconductor_simulator.py    # 메인 애플리케이션
├── document_processor.py         # 수업자료 처리 시스템
├── resume_analyzer.py            # 이력서/자소서 분석
├── question_generator.py         # 대화형 질문 생성 (범용)
├── setup_search_index.py         # 초기 인덱스 설정
├── requirements.txt
├── Dockerfile
├── deploy.sh
└── README.md
```

---

## 💡 사용 방법

### 1️⃣ 프로필 설정 (선택사항)

1. **"프로필 설정"** 탭 클릭
2. 이력서 업로드 (PDF/DOCX)
3. 자기소개서 업로드 (PDF/DOCX)
4. **"분석 시작"** 클릭

시스템이 자동으로:
- 학력, 경험, 기술 스킬 추출
- 관심 공정 분야 파악
- 강점 및 개선 영역 분석

### 2️⃣ 수업자료 업로드

1. **"수업자료 관리"** 탭 클릭
2. 수업 PDF, PPT, DOCX 업로드 (여러 개 가능)
3. **"자료 처리 시작"** 클릭

시스템이 자동으로:
- 문서에서 텍스트 추출
- 반도체 공정 지식 분류
- 학습 질문 생성
- RAG DB에 저장

**처리 가능한 자료:**
- 강의 슬라이드 (PPT/PPTX)
- 수업 노트 (PDF/DOCX)
- 교재 스캔본 (PDF)
- 실험 보고서 (DOCX)

### 3️⃣ 학습 모드

1. **"학습 모드"** 탭 클릭
2. 학습 주제 입력 (예: "CVD 증착 공정")
3. 난이도 선택: 기초 / 중급 / 고급
4. 질문 유형 선택:
   - 개념이해: 기본 정의 및 특성
   - 원리설명: 작동 메커니즘
   - 응용: 실무 적용
   - 비교: 다른 공정과 비교
   - 실무: 실습/문제 해결
5. **"질문 받기"** 클릭

질문이 Custom Voice로 재생되며, 음성 또는 텍스트로 답변!

### 4️⃣ 면접 모드

1. **"면접 모드"** 탭 클릭
2. 중점 분야 입력 (선택사항)
3. "내 프로필 기반 맞춤형 질문" 체크
4. **"면접 시작"** 클릭

맞춤형 면접 질문이 생성되며:
- 이력서의 프로젝트 경험 기반 질문
- 관심 공정 분야 심화 질문
- 자소서의 동기/목표 검증 질문

---

## 📊 평가 시스템

답변은 5가지 기준으로 평가됩니다:

1. **정확성 (30점)**: 기술적으로 올바른가?
2. **깊이 (25점)**: 원리를 이해하는가?
3. **구조 (20점)**: 논리적으로 설명하는가?
4. **응용 (15점)**: 실무와 연결하는가?
5. **의사소통 (10점)**: 명확하게 전달하는가?

**피드백 제공:**
- 강점 및 개선점 분석
- 상세한 설명 피드백
- 복습 추천 개념

---

## 🎓 반도체 공정 커버리지

시스템이 다루는 주요 공정:

### 박막 형성
- **증착 (Deposition)**: CVD, PVD, ALD, Sputtering
- **산화 (Oxidation)**: 열산화, 습식/건식 산화

### 패터닝
- **리소그래피 (Lithography)**: 포토레지스트, 노광, 현상
- **식각 (Etching)**: 건식 식각 (RIE, ICP), 습식 식각

### 도핑
- **이온주입 (Ion Implantation)**: 주입 에너지, 도즈, 채널링
- **확산 (Diffusion)**: 농도 프로파일, Fick's Law

### 평탄화 및 세정
- **CMP**: 화학적/기계적 연마
- **세정 (Cleaning)**: RCA, 피라냐, 초음파 세정

### 금속화 및 패키징
- **금속화 (Metallization)**: Al, Cu, 배리어 메탈
- **패키징 (Packaging)**: Wire bonding, Flip chip

---

## 🔬 사용 예시

### 예시 1: 학습 모드

```
주제: "플라즈마 식각"
난이도: 중급
유형: 원리설명

생성된 질문:
"RIE(Reactive Ion Etching)에서 이온의 수직 입사가 
 이방성 식각에 어떻게 기여하는지 설명하세요."

학생 답변 후:
✅ 평가: 82/100
- 정확성: 25/30
- 깊이: 20/25
- 개선점: 플라즈마 시스 전압의 역할 추가 설명 필요
- 복습 추천: 플라즈마 물리학, 이온 충돌 메커니즘
```

### 예시 2: 맞춤형 면접

```
[이력서 분석 결과]
- 전공: 전자공학과 3학년
- 경험: MEMS 센서 제작 프로젝트 (DRIE 사용)
- 관심: 식각 공정

생성된 질문:
"MEMS 프로젝트에서 DRIE를 사용하셨다고 했는데,
 Bosch 공정의 단계적 식각-패시베이션 메커니즘에 대해
 설명하고, 프로젝트에서 겪은 어려움은 무엇이었나요?"

→ 학생의 실제 경험과 연결된 구체적 질문!
```

---

## 🏗️ 시스템 아키텍처

```
┌─────────────────────────────────────────────┐
│         Gradio Web Interface                 │
│  [프로필] [자료관리] [학습] [면접]           │
└──────────────┬──────────────────────────────┘
               │
    ┌──────────┼──────────┐
    │          │          │
    ▼          ▼          ▼
[Document  [Resume   [Simulator]
Processor] Analyzer]
    │          │          │
    └──────────┴──────────┘
               │
    ┌──────────┴──────────┐
    │                     │
    ▼                     ▼
[Azure AI Search]   [Azure OpenAI]
- Semiconductor     - GPT-4
  Knowledge DB      - DALL-E 3
- Vector Search     - Embeddings
               │
               ▼
    [Azure Speech Service]
    - Custom Voice TTS
    - STT
```

---

## 🎯 로드맵

### Phase 1 (현재)
- ✅ 수업자료 자동 처리
- ✅ 개인 맞춤형 질문 생성
- ✅ 학습/면접 모드 분리
- ✅ 상세 평가 시스템

### Phase 2 (진행 중)
- 🔄 공정별 시각화 (다이어그램 자동 생성)
- 🔄 학습 진도 추적 대시보드
- 🔄 약점 분석 및 추천 학습 경로

### Phase 3 (계획)
- 📋 실시간 공동 학습 (멀티플레이어)
- 📋 실험실 시뮬레이션 (VR/AR)
- 📋 산학 협력 프로그램 연동

---

## 💰 비용 예상 (월간)

학부 과정 기준 (학생 50명):

| 항목 | 사용량 | 비용 |
|------|--------|------|
| OpenAI GPT-4 | 50만 토큰 | ₩20,000 |
| Speech TTS | 100만 자 | ₩12,000 |
| AI Search Basic | - | ₩100,000 |
| Container Apps | - | ₩30,000 |
| **총 예상** | | **₩162,000** |

💡 **학술 할인 가능** - Azure for Students 활용 시 크레딧 제공

---

## 🐛 트러블슈팅

### Q: 수업자료가 제대로 처리되지 않아요

**A**: 다음을 확인하세요:
- PDF가 이미지 스캔본인 경우 → OCR 전처리 필요
- 파일 크기가 너무 큰 경우 → 50MB 이하로 분할
- 한글 인코딩 문제 → UTF-8로 재저장

### Q: 맞춤형 질문이 생성되지 않아요

**A**: 이력서/자소서 분석이 완료되었는지 확인:
- "프로필 설정" 탭에서 분석 결과 확인
- "✅ 맞춤형 질문 준비 완료" 메시지 확인

### Q: Custom Voice가 작동하지 않아요

**A**: Speech Studio에서 확인:
```bash
# 음성 이름 확인
az cognitiveservices account list-usages \
    --name semiconductor-speech
```

---

## 📚 참고 자료

### 반도체 공정 학습
- [반도체 8대 공정 개요](https://www.samsungsemiconstory.com/kr/)
- [MIT OpenCourseWare - 반도체 제조](https://ocw.mit.edu/)

### Azure 문서
- [Azure OpenAI](https://learn.microsoft.com/azure/cognitive-services/openai/)
- [Azure AI Search](https://learn.microsoft.com/azure/search/)
- [Azure Speech](https://learn.microsoft.com/azure/cognitive-services/speech-service/)

---

## 🤝 기여

반도체 공학 전공 학생 및 교수님들의 피드백을 환영합니다!

**기여 방법:**
- 수업자료 샘플 제공
- 면접 질문 데이터 기여
- 버그 리포트 및 기능 제안

---

## 📄 라이선스

MIT License - 교육 목적 자유 사용

---

## ✉️ 문의

질문이나 제안사항은 이슈로 등록해주세요.

**개발**: Azure AI 기반 교육 솔루션 팀
