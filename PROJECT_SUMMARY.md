# 반도체 공정 전용 학습/면접 시뮬레이터 - 최종 요약

## 🎓 프로젝트 개요

**대상**: 반도체 공학 학부생
**목적**: 학습 보조 + 면접 준비
**특징**: 수업자료 기반 RAG + 개인 맞춤형 질문

---

## 📦 생성된 파일 (총 14개)

### 🔵 핵심 애플리케이션 (3개)

1. **semiconductor_simulator.py** (29KB) ⭐ 메인 앱
   - 4개 탭 UI: 프로필 설정 / 수업자료 관리 / 학습 모드 / 면접 모드
   - Custom Voice TTS/STT
   - 상세 평가 시스템 (5가지 기준)

2. **document_processor.py** (17KB) 
   - PDF, PPT, DOCX 파싱
   - 반도체 공정 지식 자동 추출 (GPT-4)
   - 학습 질문 자동 생성
   - Azure AI Search 업로드

3. **resume_analyzer.py** (13KB)
   - 이력서/자소서 텍스트 추출
   - 경험, 스킬, 관심사 분석 (GPT-4)
   - 맞춤형 질문 생성

### 🟢 보조 시스템 (4개)

4. **question_generator.py** (15KB) - 범용 대화형 질문 생성

5. **init_semiconductor_db.py** (12KB) ⭐ 초기 DB 구축
   - 샘플 반도체 질문 10개 포함
   - 공정별 분류 (증착, 식각, 리소그래피 등)

6. **setup_search_index.py** (15KB) - Azure AI Search 초기 설정

7. **interview_simulator.py** (28KB) - 범용 면접 시뮬레이터

### 🟡 실행 스크립트 (3개)

8. **quickstart_semiconductor.sh** (4.5KB) ⭐ 추천
   - 반도체 특화 빠른 시작
   - DB 초기화 포함

9. **quickstart.sh** (4.2KB) - 범용 빠른 시작

10. **deploy.sh** (4.2KB) - Azure Container Apps 배포

### 🟠 데모/테스트 (1개)

11. **demo_question_gen.py** (9.9KB) - CLI 질문 생성 데모

### 📚 문서 (3개)

12. **README_SEMICONDUCTOR.md** (9.6KB) ⭐ 반도체 특화 가이드

13. **ARCHITECTURE.md** (12KB) - 시스템 아키텍처 상세

14. **requirements.txt** (469B) - Python 패키지 목록

### ⚙️ 설정 파일 (2개)

15. **.env.template** - 환경 변수 템플릿
16. **.gitignore** - Git 제외 파일

---

## 🚀 빠른 시작 (3단계)

### 1️⃣ 환경 설정

```bash
# 파일 다운로드 후
chmod +x quickstart_semiconductor.sh
./quickstart_semiconductor.sh
```

스크립트가 자동으로:
- ✅ 가상환경 생성
- ✅ 패키지 설치
- ✅ 환경 변수 확인
- ✅ 샘플 DB 초기화

### 2️⃣ Azure 키 입력

`.env` 파일 편집:
```bash
AZURE_SPEECH_KEY=your_key
AZURE_OPENAI_KEY=your_key
AZURE_SEARCH_KEY=your_key
```

### 3️⃣ 실행

```bash
python semiconductor_simulator.py
```

http://localhost:7860 접속!

---

## 💡 주요 기능 설명

### 🎯 프로필 설정
- 이력서 업로드 → 경험/스킬 자동 추출
- 자소서 업로드 → 동기/목표 파악
- 맞춤형 질문 생성 기반 제공

### 📖 수업자료 관리
- PDF/PPT/DOCX 업로드
- GPT-4로 핵심 개념 추출
- 자동으로 학습 질문 5개씩 생성
- RAG DB에 저장

### 📚 학습 모드
- 주제 선택 (예: "CVD 증착")
- 난이도: 기초/중급/고급
- 질문 유형: 개념이해/원리설명/응용/비교/실무
- Custom Voice로 질문 재생
- 5가지 기준 평가 (정확성, 깊이, 구조, 응용, 의사소통)

### 🎯 면접 모드
- 일반 질문 or 맞춤형 질문 선택
- 이력서 경험 기반 심층 질문
- 실전 면접 시뮬레이션
- 상세 피드백 + 복습 추천

---

## 🔬 기술 스택

### Azure 서비스
- **Azure OpenAI**: GPT-4 (분석, 질문 생성, 평가), DALL-E 3 (다이어그램)
- **Azure Speech**: Custom Voice TTS, STT
- **Azure AI Search**: 벡터 검색 RAG 시스템

### 라이브러리
- **Gradio**: 웹 UI
- **PyPDF2**: PDF 파싱
- **python-pptx**: PPT 파싱
- **python-docx**: Word 파싱

---

## 📊 반도체 공정 커버리지

현재 포함된 공정 (샘플 10개 질문):
- ✅ CVD 증착 (2문제)
- ✅ 리소그래피 (2문제)
- ✅ RIE 식각 (2문제)
- ✅ 이온주입 (2문제)
- ✅ CMP (1문제)
- ✅ 분석/세정 (1문제)

확장 가능:
- 산화, 확산, 금속화
- 패키징, 검사
- 공정 통합, 수율 관리

---

## 🎓 사용 시나리오

### 시나리오 1: 수업 복습

```
1. "수업자료 관리"에서 수업 PPT 업로드
   → 시스템이 핵심 개념 추출 + 질문 생성

2. "학습 모드"에서 복습
   - 주제: "플라즈마 식각"
   - 난이도: 중급
   - 유형: 원리설명
   
3. 음성으로 답변
   → 즉시 평가 + 피드백
```

### 시나리오 2: 면접 준비

```
1. "프로필 설정"에서 이력서/자소서 업로드
   → AI가 경험 분석

2. "면접 모드" 시작
   → "MEMS 프로젝트에서 DRIE 사용 경험에 대해
      Bosch 공정 메커니즘을 설명하세요"
   
3. 답변 제출
   → 정확성 27/30, 깊이 23/25
   → "플라즈마 화학 추가 설명 필요"
```

---

## 💰 비용 예상

학부 강의 (50명 학생 기준):

| 항목 | 월 비용 |
|------|---------|
| OpenAI GPT-4 | ₩20,000 |
| Speech TTS/STT | ₩12,000 |
| AI Search | ₩100,000 |
| **합계** | **₩132,000** |

💡 Azure for Students 크레딧 활용 시 무료 가능!

---

## 🔄 확장 아이디어

### 단기 (1-2개월)
- [ ] 공정 다이어그램 자동 생성 (DALL-E)
- [ ] 학습 진도 대시보드
- [ ] 약점 분석 리포트

### 중기 (3-6개월)
- [ ] 실험실 시뮬레이션 (가상 장비)
- [ ] 팀 학습 모드 (그룹 스터디)
- [ ] 교수 대시보드 (학생 진도 관리)

### 장기 (6개월+)
- [ ] VR/AR 클린룸 체험
- [ ] 산학 협력 (기업 면접관 초청)
- [ ] 다국어 지원

---

## 📝 체크리스트

시작 전 확인:
- [ ] Azure 계정 생성
- [ ] Speech Service 생성 + Custom Voice 학습
- [ ] OpenAI Service 생성 + GPT-4 배포
- [ ] AI Search Service 생성
- [ ] `.env` 파일 작성
- [ ] `init_semiconductor_db.py` 실행
- [ ] 수업자료 준비 (PDF/PPT/DOCX)
- [ ] 이력서/자소서 준비 (테스트용)

---

## 🎉 완성!

반도체 공학 학부생을 위한 완전한 학습/면접 플랫폼이 준비되었습니다!

**핵심 차별점:**
1. ✅ 반도체 공정 전문 특화
2. ✅ 수업자료 → RAG → 자동 질문 생성
3. ✅ 이력서 분석 → 개인 맞춤형 질문
4. ✅ Custom Voice로 실감나는 시뮬레이션
5. ✅ 5가지 기준 상세 평가

**지금 바로 시작:**
```bash
./quickstart_semiconductor.sh
```

---

**개발**: Azure AI 교육 솔루션
**라이선스**: MIT (교육 목적 자유 사용)
**문의**: 이슈로 등록
