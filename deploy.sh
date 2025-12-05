#!/bin/bash

# Azure Container Apps 배포 스크립트
# 실행 전에 Azure CLI 로그인 필요: az login

set -e

# ===== 설정 변수 =====
RESOURCE_GROUP="rg-interview-simulator"
LOCATION="koreacentral"
CONTAINER_APP_ENV="interview-env"
CONTAINER_APP_NAME="interview-simulator"
ACR_NAME="interviewsimulatoracr"  # 소문자와 숫자만 가능
IMAGE_NAME="interview-simulator"
IMAGE_TAG="latest"

# ===== 색상 출력 =====
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}===== Azure 모의 면접 시뮬레이터 배포 시작 =====${NC}\n"

# ===== 1. 리소스 그룹 생성 =====
echo -e "${GREEN}1. 리소스 그룹 생성...${NC}"
az group create \
    --name $RESOURCE_GROUP \
    --location $LOCATION

# ===== 2. Azure Container Registry 생성 =====
echo -e "\n${GREEN}2. Azure Container Registry 생성...${NC}"
az acr create \
    --resource-group $RESOURCE_GROUP \
    --name $ACR_NAME \
    --sku Basic \
    --admin-enabled true

# ACR 로그인
echo -e "\n${GREEN}ACR 로그인...${NC}"
az acr login --name $ACR_NAME

# ===== 3. Docker 이미지 빌드 및 푸시 =====
echo -e "\n${GREEN}3. Docker 이미지 빌드 및 푸시...${NC}"
ACR_LOGIN_SERVER=$(az acr show --name $ACR_NAME --query loginServer --output tsv)

docker build -t $IMAGE_NAME:$IMAGE_TAG .
docker tag $IMAGE_NAME:$IMAGE_TAG $ACR_LOGIN_SERVER/$IMAGE_NAME:$IMAGE_TAG
docker push $ACR_LOGIN_SERVER/$IMAGE_NAME:$IMAGE_TAG

# ===== 4. Container Apps Environment 생성 =====
echo -e "\n${GREEN}4. Container Apps Environment 생성...${NC}"
az containerapp env create \
    --name $CONTAINER_APP_ENV \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION

# ===== 5. 환경 변수 로드 =====
echo -e "\n${GREEN}5. 환경 변수 설정...${NC}"
if [ ! -f .env ]; then
    echo -e "${RED}오류: .env 파일이 없습니다. .env.template을 복사하여 .env를 만들고 값을 입력하세요.${NC}"
    exit 1
fi

# .env 파일 읽기
source .env

# ===== 6. Container App 생성 및 배포 =====
echo -e "\n${GREEN}6. Container App 배포...${NC}"

# ACR 자격 증명 가져오기
ACR_USERNAME=$(az acr credential show --name $ACR_NAME --query username --output tsv)
ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query passwords[0].value --output tsv)

az containerapp create \
    --name $CONTAINER_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --environment $CONTAINER_APP_ENV \
    --image $ACR_LOGIN_SERVER/$IMAGE_NAME:$IMAGE_TAG \
    --registry-server $ACR_LOGIN_SERVER \
    --registry-username $ACR_USERNAME \
    --registry-password $ACR_PASSWORD \
    --target-port 7860 \
    --ingress external \
    --min-replicas 1 \
    --max-replicas 5 \
    --cpu 2 \
    --memory 4Gi \
    --env-vars \
        AZURE_SPEECH_KEY=$AZURE_SPEECH_KEY \
        AZURE_SPEECH_REGION=$AZURE_SPEECH_REGION \
        CUSTOM_VOICE_NAME=$CUSTOM_VOICE_NAME \
        AZURE_OPENAI_KEY=$AZURE_OPENAI_KEY \
        AZURE_OPENAI_ENDPOINT=$AZURE_OPENAI_ENDPOINT \
        GPT_DEPLOYMENT_NAME=$GPT_DEPLOYMENT_NAME \
        DALLE_DEPLOYMENT_NAME=$DALLE_DEPLOYMENT_NAME \
        AZURE_SEARCH_ENDPOINT=$AZURE_SEARCH_ENDPOINT \
        AZURE_SEARCH_KEY=$AZURE_SEARCH_KEY \
        AZURE_SEARCH_INDEX=$AZURE_SEARCH_INDEX

# ===== 7. 배포 완료 및 URL 출력 =====
APP_URL=$(az containerapp show \
    --name $CONTAINER_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --query properties.configuration.ingress.fqdn \
    --output tsv)

echo -e "\n${GREEN}===== 배포 완료! =====${NC}"
echo -e "${BLUE}애플리케이션 URL: https://$APP_URL${NC}\n"

# ===== 8. 로그 스트리밍 (선택사항) =====
echo -e "${GREEN}로그를 확인하려면:${NC}"
echo -e "az containerapp logs show --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --follow\n"

# ===== 추가 명령어 안내 =====
echo -e "${GREEN}유용한 명령어:${NC}"
echo -e "- 재배포: az containerapp update --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --image $ACR_LOGIN_SERVER/$IMAGE_NAME:$IMAGE_TAG"
echo -e "- 스케일 조정: az containerapp update --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --min-replicas 2 --max-replicas 10"
echo -e "- 삭제: az group delete --name $RESOURCE_GROUP --yes\n"
