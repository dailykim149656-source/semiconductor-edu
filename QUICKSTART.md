# ⚡ 빠른 시작 가이드

## 🎯 5분 안에 시작하기

### 1️⃣ 파일 다운로드
```bash
# 모든 파일을 다운로드하고 폴더로 이동
cd semiconductor-simulator
```

### 2️⃣ 자동 설치 스크립트 실행
```bash
# 실행 권한 부여
chmod +x quickstart_v2.sh

# 스크립트 실행 (모든 설정 자동)
./quickstart_v2.sh
```

스크립트가 자동으로:
- ✅ Python 버전 확인
- ✅ 가상환경 생성
- ✅ 패키지 설치
- ✅ .env 파일 생성
- ✅ 실행 준비

### 3️⃣ API 키 설정

`.env` 파일을 열어서 다음 3가지만 입력:

```bash
# 1. OpenAI
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/

# 2. Speech
AZURE_SPEECH_KEY=your-speech-key-here

# 3. AI Search
AZURE_SEARCH_KEY=your-search-key-here
AZURE_SEARCH_ENDPOINT=https://your-search.search.windows.net
```

### 4️⃣ 실행!
```bash
python semiconductor_simulator_v2.py
```

브라우저에서 **http://localhost:7860** 접속

---

## 🔑 API 키 받는 법

### Azure OpenAI
1. [Azure Portal](https://portal.azure.com) 접속
2. "Azure OpenAI" 검색 → 리소스 생성
3. "Keys and Endpoint" 탭
4. Key 1 복사 → `.env`에 붙여넣기

### Azure Speech
1. Azure Portal에서 "Speech Services" 검색
2. 리소스 생성 (Free F0 가능)
3. "Keys and Endpoint" 탭
4. Key 1 복사

### Azure AI Search
1. "Azure AI Search" 리소스 생성
2. "Keys" 탭
3. Admin Key 복사

---

## 💡 다음 단계

### 샘플 질문 업로드 (선택)
```bash
python init_semiconductor_db.py
```

### 공정 시뮬레이터 실행 (보너스)
```bash
python process_simulator.py
# http://localhost:7861
```

### 샘플 문서 테스트
1. "프로필 설정" 탭
2. `sample_resume.docx` 업로드
3. `sample_personal_statement.docx` 업로드
4. "분석 시작" 클릭

---

## ⚠️ 문제 해결

### "Python이 설치되어 있지 않습니다"
→ https://www.python.org/downloads/ 에서 Python 3.9+ 설치

### "ModuleNotFoundError"
→ 가상환경 활성화 확인:
```bash
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows
```

### "API 키 오류"
→ `.env` 파일의 키 확인:
```bash
# 따옴표 없이 입력!
AZURE_OPENAI_API_KEY=abc123def456  ✅
AZURE_OPENAI_API_KEY="abc123def456"  ❌
```

### "지식 베이스를 찾을 수 없습니다"
→ 초기화 실행:
```bash
python init_semiconductor_db.py
```

---

## 📞 도움이 필요하신가요?

### 📖 상세 가이드
- [README.md](README.md) - 전체 설명서
- [PROJECT_SUMMARY_V2.md](PROJECT_SUMMARY_V2.md) - 프로젝트 요약
- [DIFFERENTIATION_STRATEGY.md](DIFFERENTIATION_STRATEGY.md) - NotebookLM 대비 차별점

### 🐛 버그 리포트
- GitHub Issues 또는 이메일

### 💬 커뮤니티
- Discord 서버 (추후 공개)

---

## 🎉 완료!

이제 반도체 공정을 재미있게 배울 준비가 되었습니다!

**첫 번째 질문 받아보기:**
1. "학습 모드" 탭 이동
2. 주제: "CVD 증착"
3. 난이도: "중급"
4. "학습 시작" 클릭!

**행운을 빕니다! 🚀**
