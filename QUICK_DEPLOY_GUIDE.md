# ⚡ 빠른 배포 가이드 (10분 완성)

## 🎯 목표
10분 안에 Azure App Service에 배포하기!

---

## 📋 준비물

✅ Azure 계정
✅ 이미 생성된 Azure 서비스:
  - Azure OpenAI
  - Azure AI Search
  - Azure Speech Service
✅ 코드 (이미 준비됨)

---

## 🚀 3단계 배포

### Step 1: Azure App Service 생성 (3분)

**Azure Portal (https://portal.azure.com):**

1. **"App Services" 검색 → 만들기**

2. **기본 설정:**
   ```
   리소스 그룹: [새로 만들기] rg-semiconductor-sim
   이름: semiconductor-sim-[랜덤숫자]
   게시: 코드
   런타임 스택: Python 3.11
   운영 체제: Linux
   지역: Korea Central
   ```

3. **가격 책정 계층:**
   ```
   SKU: B1 (Basic) - ₩21,000/월
   또는 F1 (무료) - 테스트용
   ```

4. **검토 + 만들기 → 만들기**

5. **배포 완료 대기 (1-2분)**

---

### Step 2: 환경 변수 설정 (4분)

**App Service → 설정 → 구성 → 애플리케이션 설정:**

**필수 8개 변수 추가:**

```bash
# 1. Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://[your-resource].openai.azure.com/
AZURE_OPENAI_KEY=[your-key]
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini

# 2. Azure AI Search
AZURE_SEARCH_ENDPOINT=https://[your-resource].search.windows.net
AZURE_SEARCH_KEY=[your-key]
AZURE_SEARCH_INDEX=semiconductor-qa-index

# 3. Azure Speech
AZURE_SPEECH_KEY=[your-key]
AZURE_SPEECH_REGION=koreacentral

# 4. Gradio
GRADIO_SERVER_PORT=8000
```

**저장 클릭! (중요)**

---

### Step 3: 코드 배포 (3분)

#### 방법 A: VS Code (가장 쉬움) ⭐

1. **VS Code에서 Azure 확장 설치**
   ```
   확장 → "Azure App Service" 검색 → 설치
   ```

2. **Azure 로그인**
   ```
   왼쪽 Azure 아이콘 → Sign in
   ```

3. **배포**
   ```
   프로젝트 폴더 우클릭 → Deploy to Web App
   → semiconductor-sim-[번호] 선택
   → 배포 시작!
   ```

4. **완료 대기 (2-3분)**

#### 방법 B: ZIP 업로드

1. **파일 압축**
   ```bash
   # Windows: 폴더 우클릭 → 압축
   # Mac/Linux:
   zip -r deploy.zip . -x "*.git*" -x "venv/*"
   ```

2. **Kudu 접속**
   ```
   https://semiconductor-sim-[번호].scm.azurewebsites.net/ZipDeployUI
   ```

3. **ZIP 파일 드래그 앤 드롭**

4. **배포 완료 대기**

---

## ✅ 접속 테스트

### URL 확인

```
https://semiconductor-sim-[번호].azurewebsites.net
```

### 테스트 체크리스트

- [ ] 페이지가 로드되는가?
- [ ] 질문 생성이 되는가?
- [ ] 음성 재생이 되는가?
- [ ] 답변 평가가 되는가?

---

## 🐛 문제 발생 시

### 1. "Application Error"

**확인:**
```
App Service → 모니터링 → 로그 스트림
```

**일반적 원인:**
- 환경 변수 누락
- API 키 오류

**해결:**
```
설정 → 구성 → 환경 변수 다시 확인
→ 저장 → 앱 재시작
```

---

### 2. "502 Bad Gateway"

**원인:** 앱 시작 실패

**해결:**
```bash
# SSH로 접속
App Service → 개발 도구 → SSH

# 로그 확인
cd /home/LogFiles
cat *.log

# 수동 실행 테스트
cd /home/site/wwwroot
python semiconductor_simulator_v2.py
```

---

### 3. 질문 생성 안됨

**확인:**
1. OpenAI 환경 변수
2. AI Search 환경 변수

**테스트:**
```python
# SSH에서
python -c "import os; print(os.getenv('AZURE_OPENAI_KEY'))"
```

---

### 4. 음성 재생/녹음 안됨

**확인:**
- HTTPS 연결 (자동으로 됨)
- Speech 환경 변수

**브라우저 콘솔 확인:**
```
F12 → Console 탭
→ 마이크 권한 확인
```

---

## 💡 추가 팁

### 배포 후 자동 재시작 설정

```
App Service → 설정 → 구성
→ "Always On" 켜기 (B1 이상)
```

### 커스텀 도메인 연결

```
App Service → 설정 → 사용자 지정 도메인
→ 도메인 추가
→ DNS 설정
```

### HTTPS 강제

```
App Service → 설정 → TLS/SSL 설정
→ "HTTPS만 허용" 켜기
```

### 인증 추가

```
App Service → 인증
→ ID 공급자 추가
→ Microsoft (학교 계정)
```

---

## 📊 배포 완료!

### 성공 화면

```
╔═══════════════════════════════════════╗
║  ✅ 배포 성공!                        ║
║                                       ║
║  URL: https://semiconductor-sim-      ║
║       [번호].azurewebsites.net        ║
║                                       ║
║  상태: Running ✅                     ║
║  환경: Azure App Service              ║
╚═══════════════════════════════════════╝
```

---

## 🎉 다음 단계

### 1주차: 테스트
- 친구들 초대
- 피드백 수집
- 버그 수정

### 2주차: 개선
- 성능 모니터링
- 기능 추가
- UI 개선

### 3주차: 확장
- 더 많은 사용자
- 스케일업 고려
- 비용 최적화

---

## 📚 참고 문서

- [AZURE_DEPLOYMENT_GUIDE.md](AZURE_DEPLOYMENT_GUIDE.md) - 전체 가이드
- [AZURE_ENV_VARIABLES.md](AZURE_ENV_VARIABLES.md) - 환경 변수 상세
- [README.md](README.md) - 프로젝트 개요

---

**10분 만에 배포 완료!** 🚀✨

다음 명령으로 로그 확인:
```bash
az webapp log tail \
  --resource-group rg-semiconductor-sim \
  --name semiconductor-sim-[번호]
```
