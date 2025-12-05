# 🚀 Azure 웹 서비스 배포 가이드

## 📋 목차
1. [배포 옵션 비교](#배포-옵션-비교)
2. [권장 방식: Azure App Service](#권장-방식-azure-app-service)
3. [대안: Azure Container Apps](#대안-azure-container-apps)
4. [배포 단계별 가이드](#배포-단계별-가이드)
5. [비용 분석](#비용-분석)
6. [보안 설정](#보안-설정)

---

## 🎯 배포 옵션 비교

### 옵션 1: Azure App Service (웹앱) ⭐ 권장

**장점:**
- ✅ 가장 간단한 배포
- ✅ Gradio 지원 우수
- ✅ 자동 스케일링
- ✅ CI/CD 통합
- ✅ 무료 계층 있음 (F1)

**단점:**
- ⚠️ 메모리 제한 (F1: 1GB)
- ⚠️ 항상 실행 (비용)

**적합한 경우:**
- 소규모 학생 그룹 (10-50명)
- 빠른 배포 필요
- 관리 최소화

---

### 옵션 2: Azure Container Apps

**장점:**
- ✅ Docker 기반
- ✅ 유연한 스케일링
- ✅ 사용한만큼 과금
- ✅ 최신 기술

**단점:**
- ⚠️ 설정 복잡
- ⚠️ Dockerfile 필요

**적합한 경우:**
- 대규모 사용자 (100명+)
- 트래픽 변동 큰 경우
- Docker 경험 있음

---

### 옵션 3: Azure Virtual Machine

**장점:**
- ✅ 완전한 제어
- ✅ 모든 설정 가능

**단점:**
- ❌ 관리 복잡
- ❌ 보안 직접 관리
- ❌ 비용 높음

**적합한 경우:**
- 특수한 요구사항
- 인프라 경험 많음

---

## ⭐ 권장 방식: Azure App Service

### 왜 App Service인가?

```
간단함 ███████████████████████ 95%
비용   ████████████████░░░░░░░ 70%
성능   ████████████████░░░░░░░ 75%
확장성 ███████████████░░░░░░░░ 65%
```

**최적의 균형:** 간단하면서도 충분한 성능!

---

## 🛠️ 배포 단계별 가이드

### Phase 1: 로컬 테스트 (완료 ✅)

```bash
# 현재 상태
python semiconductor_simulator_v2.py
# → http://127.0.0.1:7860
```

---

### Phase 2: Azure 리소스 생성

#### 2.1 Azure App Service 생성

**Azure Portal에서:**

1. **리소스 그룹 생성**
   ```
   이름: rg-semiconductor-simulator
   지역: Korea Central
   ```

2. **App Service Plan 생성**
   ```
   이름: plan-semiconductor-sim
   운영체제: Linux
   가격 책정 계층: B1 (기본) - ₩21,000/월
   또는: F1 (무료) - 테스트용
   ```

3. **Web App 생성**
   ```
   이름: semiconductor-simulator-[고유번호]
   게시: 코드
   런타임 스택: Python 3.11
   지역: Korea Central
   ```

#### 2.2 필수 서비스 확인

이미 생성되어 있어야 함:
- ✅ Azure OpenAI Service
- ✅ Azure AI Search
- ✅ Azure Speech Service

---

### Phase 3: 코드 준비

#### 3.1 필요한 파일 생성

**파일 구조:**
```
semiconductor-simulator/
├── semiconductor_simulator_v2.py
├── document_processor.py
├── resume_analyzer.py
├── question_generator.py
├── storage_manager.py
├── requirements.txt
├── .env.template
├── startup.sh
├── .deployment (새로 생성)
└── README.md
```

#### 3.2 startup.sh 생성 (이미 있음)

```bash
#!/bin/bash
pip install -r requirements.txt
python semiconductor_simulator_v2.py --server-name 0.0.0.0 --server-port 8000
```

#### 3.3 .deployment 파일 생성

```ini
[config]
SCM_DO_BUILD_DURING_DEPLOYMENT=true
```

---

### Phase 4: 환경 변수 설정

**Azure Portal → Web App → 설정 → 구성:**

```bash
# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com/
AZURE_OPENAI_KEY=your-key
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini

# Azure AI Search
AZURE_SEARCH_ENDPOINT=https://your-search.search.windows.net
AZURE_SEARCH_KEY=your-key
AZURE_SEARCH_INDEX=semiconductor-qa-index

# Azure Speech
AZURE_SPEECH_KEY=your-key
AZURE_SPEECH_REGION=koreacentral

# Gradio 설정
GRADIO_SERVER_PORT=8000
GRADIO_SERVER_NAME=0.0.0.0
```

---

### Phase 5: 배포 방법

#### 방법 A: GitHub Actions (권장)

**1. GitHub 저장소 생성**

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/your-username/semiconductor-simulator.git
git push -u origin main
```

**2. .github/workflows/azure-deploy.yml 생성**

```yaml
name: Deploy to Azure App Service

on:
  push:
    branches:
      - main

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Deploy to Azure Web App
      uses: azure/webapps-deploy@v2
      with:
        app-name: semiconductor-simulator-[고유번호]
        publish-profile: ${{ secrets.AZURE_WEBAPP_PUBLISH_PROFILE }}
```

**3. Publish Profile 다운로드**

```
Azure Portal → Web App → 배포 센터 → 게시 프로필 다운로드
→ GitHub Settings → Secrets → AZURE_WEBAPP_PUBLISH_PROFILE
```

**4. Push → 자동 배포**

```bash
git push origin main
# → GitHub Actions 자동 실행
# → 5-10분 후 배포 완료
```

---

#### 방법 B: VS Code 확장 (빠른 테스트)

**1. Azure App Service 확장 설치**

```
VS Code → Extensions → "Azure App Service"
```

**2. 로그인**

```
왼쪽 Azure 아이콘 → Sign in to Azure
```

**3. 배포**

```
우클릭 → Deploy to Web App
→ semiconductor-simulator 선택
→ 배포 완료!
```

---

#### 방법 C: Azure CLI

**1. Azure CLI 설치 및 로그인**

```bash
# Azure CLI 로그인
az login

# Web App 생성
az webapp create \
  --resource-group rg-semiconductor-simulator \
  --plan plan-semiconductor-sim \
  --name semiconductor-simulator-[고유번호] \
  --runtime "PYTHON:3.11"
```

**2. 코드 배포**

```bash
# ZIP으로 압축
zip -r deploy.zip . -x "*.git*" -x "venv/*" -x "__pycache__/*"

# 배포
az webapp deployment source config-zip \
  --resource-group rg-semiconductor-simulator \
  --name semiconductor-simulator-[고유번호] \
  --src deploy.zip
```

---

### Phase 6: Gradio 설정 수정

#### semiconductor_simulator_v2.py 마지막 부분 수정

**기존:**
```python
if __name__ == "__main__":
    simulator = SemiconductorSimulator()
    demo = create_gradio_interface(simulator)
    demo.launch(
        share=False,
        inbrowser=True
    )
```

**배포용:**
```python
if __name__ == "__main__":
    import os
    
    simulator = SemiconductorSimulator()
    demo = create_gradio_interface(simulator)
    
    # Azure App Service 설정
    server_name = os.getenv("GRADIO_SERVER_NAME", "0.0.0.0")
    server_port = int(os.getenv("GRADIO_SERVER_PORT", "8000"))
    
    demo.launch(
        server_name=server_name,
        server_port=server_port,
        share=False,
        show_error=True,
        auth=None  # 또는 ("admin", "password123") - 인증 추가
    )
```

---

### Phase 7: 접속 및 테스트

**배포 완료 후:**

```
URL: https://semiconductor-simulator-[고유번호].azurewebsites.net
```

**테스트 체크리스트:**
- [ ] 페이지 로딩
- [ ] 질문 생성
- [ ] 음성 재생 (TTS)
- [ ] 음성 녹음 (STT)
- [ ] 답변 평가
- [ ] PDF/HTML 리포트 생성

---

## 💰 비용 분석

### 시나리오 1: 소규모 (학생 20명)

**App Service:**
- F1 (무료) 또는 B1 (₩21,000/월)

**Azure 서비스:**
- OpenAI: ₩20,000/월 (500 요청/일)
- Speech: ₩12,000/월 (400분/월)
- AI Search: ₩100,000/월

**총 비용: ₩132,000 - ₩153,000/월**

---

### 시나리오 2: 중규모 (학생 100명)

**App Service:**
- S1 (₩98,000/월) - 더 나은 성능

**Azure 서비스:**
- OpenAI: ₩100,000/월
- Speech: ₩60,000/월
- AI Search: ₩100,000/월

**총 비용: ₩358,000/월**

---

### 시나리오 3: 대규모 (학생 500명)

**Container Apps:**
- 사용량 기반 (₩150,000-300,000/월)

**Azure 서비스:**
- OpenAI: ₩500,000/월
- Speech: ₩300,000/월
- AI Search: ₩200,000/월 (더 큰 인덱스)

**총 비용: ₩1,150,000 - ₩1,300,000/월**

---

## 🔒 보안 설정

### 1. 인증 추가

**방법 A: Gradio 기본 인증**

```python
demo.launch(
    auth=("admin", "your-strong-password"),
    auth_message="반도체 시뮬레이터에 로그인하세요"
)
```

**방법 B: Azure AD 인증**

```
Azure Portal → Web App → 인증
→ ID 공급자 추가
→ Microsoft
→ 학교/회사 계정으로만 접근
```

---

### 2. HTTPS 강제

**자동 설정됨:**
- Azure App Service는 자동으로 HTTPS 제공
- 무료 SSL 인증서 포함

**설정 확인:**
```
Azure Portal → Web App → TLS/SSL 설정
→ "HTTPS만 허용" 활성화
```

---

### 3. API 키 보호

**환경 변수 사용:**
- ✅ 코드에 하드코딩 금지
- ✅ Azure Portal 환경 변수 사용
- ✅ Key Vault 사용 (프로덕션)

**Key Vault 설정 (선택):**

```bash
# Key Vault 생성
az keyvault create \
  --name kv-semiconductor-sim \
  --resource-group rg-semiconductor-simulator

# 비밀 추가
az keyvault secret set \
  --vault-name kv-semiconductor-sim \
  --name "OpenAI-Key" \
  --value "your-key"

# Web App에 접근 권한
az webapp identity assign \
  --name semiconductor-simulator-[고유번호] \
  --resource-group rg-semiconductor-simulator
```

---

### 4. 네트워크 제한

**학교 IP만 허용:**

```
Azure Portal → Web App → 네트워킹
→ 액세스 제한
→ 규칙 추가:
  - 이름: School-Network
  - 우선순위: 100
  - IP 주소: 123.456.789.0/24
```

---

## 📊 모니터링 설정

### Application Insights 활성화

**1. 생성:**
```
Azure Portal → Application Insights
→ 새로 만들기
→ Web App에 연결
```

**2. 로깅 추가:**

```python
# semiconductor_simulator_v2.py 상단
from opencensus.ext.azure.log_exporter import AzureLogHandler
import logging

# Application Insights 연결
instrumentation_key = os.getenv('APPINSIGHTS_INSTRUMENTATIONKEY')
if instrumentation_key:
    logger.addHandler(AzureLogHandler(
        connection_string=f'InstrumentationKey={instrumentation_key}'
    ))
```

**3. 대시보드 확인:**
- 요청 수
- 응답 시간
- 오류 발생
- 사용자 수

---

## 🔄 CI/CD 파이프라인

### 완전한 GitHub Actions 워크플로우

```yaml
name: Build and Deploy

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

env:
  AZURE_WEBAPP_NAME: semiconductor-simulator-001
  PYTHON_VERSION: '3.11'

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ env.PYTHON_VERSION }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Lint with flake8
      run: |
        pip install flake8
        flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
    
    - name: Test with pytest
      run: |
        pip install pytest
        pytest tests/ || true

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ env.PYTHON_VERSION }}
    
    - name: Build package
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Deploy to Azure Web App
      uses: azure/webapps-deploy@v2
      with:
        app-name: ${{ env.AZURE_WEBAPP_NAME }}
        publish-profile: ${{ secrets.AZURE_WEBAPP_PUBLISH_PROFILE }}
    
    - name: Health check
      run: |
        sleep 30
        curl -f https://${{ env.AZURE_WEBAPP_NAME }}.azurewebsites.net || exit 1
```

---

## 🚦 배포 체크리스트

### 배포 전 확인

- [ ] 모든 환경 변수 설정 (.env → Azure Portal)
- [ ] requirements.txt 최신 버전
- [ ] Gradio 서버 설정 (0.0.0.0:8000)
- [ ] 로그 레벨 INFO
- [ ] 오류 처리 확인
- [ ] 인증 설정 (선택)

### 배포 중 확인

- [ ] GitHub Actions 성공
- [ ] 빌드 로그 확인
- [ ] 배포 완료 메시지

### 배포 후 확인

- [ ] URL 접속 테스트
- [ ] 질문 생성 테스트
- [ ] TTS/STT 테스트
- [ ] 평가 기능 테스트
- [ ] 리포트 생성 테스트
- [ ] 성능 모니터링

---

## 🐛 문제 해결

### "Application Error"

**로그 확인:**
```
Azure Portal → Web App → 로그 스트림
```

**일반적 원인:**
1. 환경 변수 누락
2. requirements.txt 오류
3. 포트 설정 문제

**해결:**
```bash
# 로컬에서 포트 테스트
python semiconductor_simulator_v2.py --server-port 8000
```

---

### "502 Bad Gateway"

**원인:** 앱 시작 실패

**확인:**
```
Azure Portal → Web App → 고급 도구 (Kudu)
→ Debug console
→ LogFiles/
```

**해결:**
- startup.sh 권한 확인
- Python 버전 확인
- 메모리 부족 → 더 큰 플랜

---

### 음성 기능 안됨

**HTTPS 필수:**
- 브라우저 마이크 접근은 HTTPS만 가능
- Azure App Service는 자동 HTTPS ✅

**확인:**
```
브라우저 콘솔 (F12)
→ 에러 메시지 확인
→ 마이크 권한 확인
```

---

## 📚 다음 단계

### 배포 완료 후

1. **사용자 테스트**
   - 베타 테스터 초대
   - 피드백 수집

2. **성능 최적화**
   - 응답 시간 모니터링
   - 병목 지점 개선

3. **기능 추가**
   - 사용자 관리
   - 진행률 추적
   - 리더보드

4. **문서화**
   - 사용자 가이드
   - FAQ
   - 비디오 튜토리얼

---

## 🎓 추천 배포 순서

### Week 1: 테스트 배포
```
1. F1 (무료) 플랜으로 배포
2. 기본 기능 테스트
3. 친구/동료와 베타 테스트
```

### Week 2: 소규모 운영
```
1. B1 플랜으로 업그레이드
2. 학급/동아리 단위 사용 (20-50명)
3. 피드백 수집 및 개선
```

### Week 3+: 확장
```
1. 사용량 모니터링
2. 필요시 S1 또는 Container Apps로 확장
3. 더 많은 기능 추가
```

---

## ✅ 최종 요약

### 권장 배포 방식

**초보자/빠른 테스트:**
```
Azure App Service + VS Code 확장
→ 10분 안에 배포
```

**정석/프로덕션:**
```
Azure App Service + GitHub Actions
→ CI/CD 자동화
→ 지속적인 개선
```

**대규모:**
```
Azure Container Apps
→ 자동 스케일링
→ 비용 최적화
```

---

**시작하세요!** 🚀

다음 파일이 필요하면 요청하세요:
- startup.sh
- .github/workflows/azure-deploy.yml
- 배포용 수정 코드
- 환경 변수 체크리스트
