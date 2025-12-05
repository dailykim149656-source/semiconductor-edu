# Azure App Service 환경 변수 설정 체크리스트

## 🔑 필수 환경 변수

Azure Portal → Web App → 설정 → 구성 → 애플리케이션 설정

### Azure OpenAI

```
이름: AZURE_OPENAI_ENDPOINT
값: https://your-openai-resource.openai.azure.com/

이름: AZURE_OPENAI_KEY
값: your-api-key-here

이름: AZURE_OPENAI_DEPLOYMENT
값: gpt-4o-mini

이름: AZURE_OPENAI_API_VERSION
값: 2024-02-15-preview
```

### Azure AI Search

```
이름: AZURE_SEARCH_ENDPOINT
값: https://your-search-resource.search.windows.net

이름: AZURE_SEARCH_KEY
값: your-admin-key-here

이름: AZURE_SEARCH_INDEX
값: semiconductor-qa-index
```

### Azure Speech Service

```
이름: AZURE_SPEECH_KEY
값: your-speech-key-here

이름: AZURE_SPEECH_REGION
값: koreacentral

이름: AZURE_SPEECH_VOICE
값: ko-KR-SunHiNeural
```

### Gradio 서버 설정

```
이름: GRADIO_SERVER_NAME
값: 0.0.0.0

이름: GRADIO_SERVER_PORT
값: 8000

이름: ENVIRONMENT
값: production
```

### 로깅 (선택사항)

```
이름: LOG_LEVEL
값: INFO
```

---

## 📋 설정 방법

### 방법 1: Azure Portal (추천)

1. Azure Portal (https://portal.azure.com) 로그인
2. App Service 선택
3. 왼쪽 메뉴 → **설정** → **구성**
4. **애플리케이션 설정** 탭
5. **+ 새 애플리케이션 설정** 클릭
6. 위의 환경 변수들을 하나씩 추가
7. **저장** 클릭
8. 앱 재시작

### 방법 2: Azure CLI

```bash
# 리소스 그룹과 앱 이름 설정
RESOURCE_GROUP="rg-semiconductor-simulator"
WEBAPP_NAME="semiconductor-simulator-001"

# OpenAI 설정
az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $WEBAPP_NAME \
  --settings \
    AZURE_OPENAI_ENDPOINT="https://your-openai.openai.azure.com/" \
    AZURE_OPENAI_KEY="your-key" \
    AZURE_OPENAI_DEPLOYMENT="gpt-4o-mini" \
    AZURE_OPENAI_API_VERSION="2024-02-15-preview"

# Search 설정
az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $WEBAPP_NAME \
  --settings \
    AZURE_SEARCH_ENDPOINT="https://your-search.search.windows.net" \
    AZURE_SEARCH_KEY="your-key" \
    AZURE_SEARCH_INDEX="semiconductor-qa-index"

# Speech 설정
az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $WEBAPP_NAME \
  --settings \
    AZURE_SPEECH_KEY="your-key" \
    AZURE_SPEECH_REGION="koreacentral" \
    AZURE_SPEECH_VOICE="ko-KR-SunHiNeural"

# Gradio 설정
az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $WEBAPP_NAME \
  --settings \
    GRADIO_SERVER_NAME="0.0.0.0" \
    GRADIO_SERVER_PORT="8000" \
    ENVIRONMENT="production"
```

---

## ✅ 검증 방법

### 1. Azure Portal에서 확인

```
App Service → 설정 → 구성 → 애플리케이션 설정
→ 모든 환경 변수가 표시되는지 확인
```

### 2. SSH로 확인

```
App Service → 개발 도구 → SSH → 이동

# SSH 콘솔에서
echo $AZURE_OPENAI_KEY
echo $AZURE_SPEECH_KEY
echo $AZURE_SEARCH_KEY
```

### 3. 로그에서 확인

```
App Service → 모니터링 → 로그 스트림

다음 메시지 찾기:
✅ Azure OpenAI 클라이언트 초기화 완료
✅ Azure AI Search 클라이언트 초기화 완료
✅ Azure Speech 클라이언트 초기화 완료
```

---

## ⚠️ 보안 주의사항

### 절대 하지 말 것

❌ 코드에 API 키 하드코딩
❌ GitHub에 .env 파일 커밋
❌ 로그에 API 키 출력
❌ 클라이언트에 API 키 노출

### 해야 할 것

✅ 환경 변수로만 관리
✅ .gitignore에 .env 추가
✅ Key Vault 사용 고려
✅ 정기적으로 키 교체

---

## 🔒 Key Vault 통합 (고급)

### Key Vault에 저장

```bash
# Key Vault 생성
az keyvault create \
  --name kv-semiconductor-sim \
  --resource-group $RESOURCE_GROUP \
  --location koreacentral

# 비밀 추가
az keyvault secret set \
  --vault-name kv-semiconductor-sim \
  --name "OpenAI-Key" \
  --value "your-actual-key"

az keyvault secret set \
  --vault-name kv-semiconductor-sim \
  --name "Speech-Key" \
  --value "your-actual-key"

az keyvault secret set \
  --vault-name kv-semiconductor-sim \
  --name "Search-Key" \
  --value "your-actual-key"
```

### App Service에서 참조

```bash
# Managed Identity 활성화
az webapp identity assign \
  --resource-group $RESOURCE_GROUP \
  --name $WEBAPP_NAME

# Key Vault 접근 권한 부여
PRINCIPAL_ID=$(az webapp identity show \
  --resource-group $RESOURCE_GROUP \
  --name $WEBAPP_NAME \
  --query principalId \
  --output tsv)

az keyvault set-policy \
  --name kv-semiconductor-sim \
  --object-id $PRINCIPAL_ID \
  --secret-permissions get list

# App Settings에서 참조
az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $WEBAPP_NAME \
  --settings \
    AZURE_OPENAI_KEY="@Microsoft.KeyVault(VaultName=kv-semiconductor-sim;SecretName=OpenAI-Key)" \
    AZURE_SPEECH_KEY="@Microsoft.KeyVault(VaultName=kv-semiconductor-sim;SecretName=Speech-Key)" \
    AZURE_SEARCH_KEY="@Microsoft.KeyVault(VaultName=kv-semiconductor-sim;SecretName=Search-Key)"
```

---

## 📝 환경 변수 템플릿

### .env.production (로컬 테스트용)

```bash
# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com/
AZURE_OPENAI_KEY=your-key
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# Azure AI Search
AZURE_SEARCH_ENDPOINT=https://your-search.search.windows.net
AZURE_SEARCH_KEY=your-key
AZURE_SEARCH_INDEX=semiconductor-qa-index

# Azure Speech
AZURE_SPEECH_KEY=your-key
AZURE_SPEECH_REGION=koreacentral
AZURE_SPEECH_VOICE=ko-KR-SunHiNeural

# Gradio
GRADIO_SERVER_NAME=0.0.0.0
GRADIO_SERVER_PORT=8000

# Environment
ENVIRONMENT=production
LOG_LEVEL=INFO
```

### 로컬에서 프로덕션 모드 테스트

```bash
# .env.production 파일 사용
python -c "from dotenv import load_dotenv; load_dotenv('.env.production'); import subprocess; subprocess.run(['python', 'semiconductor_simulator_v2.py'])"
```

---

## 🚨 문제 해결

### "클라이언트 초기화 실패"

**확인:**
1. 환경 변수 이름 정확한지
2. API 키에 공백 없는지
3. Endpoint URL 형식 정확한지

**해결:**
```bash
# App Service 재시작
az webapp restart \
  --resource-group $RESOURCE_GROUP \
  --name $WEBAPP_NAME
```

### "환경 변수가 보이지 않음"

**원인:**
- 저장 안 함
- 앱 재시작 안 함

**해결:**
1. 환경 변수 다시 추가
2. **저장** 클릭 필수
3. 앱 재시작

### "Key Vault 접근 실패"

**확인:**
```bash
# Managed Identity 확인
az webapp identity show \
  --resource-group $RESOURCE_GROUP \
  --name $WEBAPP_NAME

# Key Vault 정책 확인
az keyvault show \
  --name kv-semiconductor-sim \
  --query properties.accessPolicies
```

---

## ✅ 최종 체크리스트

배포 전:
- [ ] 모든 필수 환경 변수 설정
- [ ] API 키 유효성 확인
- [ ] Endpoint URL 정확성 확인
- [ ] 로컬에서 프로덕션 모드 테스트

배포 후:
- [ ] 로그 스트림에서 초기화 성공 확인
- [ ] 웹사이트 접속 테스트
- [ ] 질문 생성 테스트
- [ ] TTS/STT 테스트
- [ ] 평가 기능 테스트

---

**환경 변수 설정이 배포의 90%입니다!** 🔑✨
