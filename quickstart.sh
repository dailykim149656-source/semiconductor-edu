#!/bin/bash

# 로컬 개발 환경 빠른 시작 스크립트

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}===== AI 모의 면접 시뮬레이터 로컬 개발 환경 설정 =====${NC}\n"

# 1. Python 버전 확인
echo -e "${GREEN}1. Python 버전 확인...${NC}"
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.11"

if [[ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]]; then
    echo -e "${YELLOW}경고: Python 3.11 이상이 권장됩니다. 현재: $python_version${NC}"
else
    echo -e "Python 버전: $python_version ✓"
fi

# 2. 가상환경 생성 및 활성화
echo -e "\n${GREEN}2. 가상환경 설정...${NC}"
if [ ! -d "venv" ]; then
    echo "가상환경 생성 중..."
    python3 -m venv venv
fi

echo "가상환경 활성화..."
source venv/bin/activate

# 3. 패키지 설치
echo -e "\n${GREEN}3. 의존성 패키지 설치...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

# 4. 환경 변수 확인
echo -e "\n${GREEN}4. 환경 변수 확인...${NC}"
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}경고: .env 파일이 없습니다.${NC}"
    echo "템플릿에서 .env 파일을 생성합니다..."
    cp .env.template .env
    echo -e "${YELLOW}⚠️  .env 파일을 편집하여 실제 Azure 키를 입력하세요!${NC}"
    echo -e "${YELLOW}⚠️  편집 후 다시 이 스크립트를 실행하세요.${NC}"
    exit 1
else
    echo ".env 파일 발견 ✓"
    source .env
    
    # 필수 환경 변수 확인
    missing_vars=()
    
    [ -z "$AZURE_SPEECH_KEY" ] && missing_vars+=("AZURE_SPEECH_KEY")
    [ -z "$AZURE_OPENAI_KEY" ] && missing_vars+=("AZURE_OPENAI_KEY")
    [ -z "$AZURE_SEARCH_KEY" ] && missing_vars+=("AZURE_SEARCH_KEY")
    
    if [ ${#missing_vars[@]} -gt 0 ]; then
        echo -e "${YELLOW}경고: 다음 환경 변수가 설정되지 않았습니다:${NC}"
        printf '%s\n' "${missing_vars[@]}"
        echo -e "${YELLOW}계속하려면 .env 파일을 확인하세요.${NC}"
        exit 1
    else
        echo "필수 환경 변수 모두 설정됨 ✓"
    fi
fi

# 5. Azure AI Search 인덱스 확인
echo -e "\n${GREEN}5. Azure AI Search 인덱스 확인...${NC}"
echo "인덱스가 없다면 생성하시겠습니까? (y/n)"
read -r response

if [[ "$response" =~ ^[Yy]$ ]]; then
    echo "인덱스 생성 중..."
    python setup_search_index.py
else
    echo "인덱스 생성 건너뜀"
fi

# 6. 테스트 실행 (선택사항)
echo -e "\n${GREEN}6. 빠른 테스트 실행...${NC}"
echo "간단한 연결 테스트를 실행하시겠습니까? (y/n)"
read -r test_response

if [[ "$test_response" =~ ^[Yy]$ ]]; then
    python3 << 'EOF'
import os
from azure.cognitiveservices import speech as speechsdk

print("Azure Speech Service 연결 테스트...")
try:
    speech_key = os.getenv("AZURE_SPEECH_KEY")
    speech_region = os.getenv("AZURE_SPEECH_REGION")
    
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=speech_region)
    print("✓ Speech Service 연결 성공")
except Exception as e:
    print(f"✗ Speech Service 연결 실패: {e}")

print("\nAzure OpenAI 연결 테스트...")
try:
    from openai import AzureOpenAI
    client = AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_KEY"),
        api_version="2024-02-15-preview",
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
    )
    print("✓ OpenAI Service 연결 성공")
except Exception as e:
    print(f"✗ OpenAI Service 연결 실패: {e}")

print("\n모든 테스트 완료!")
EOF
fi

# 7. 실행 옵션
echo -e "\n${GREEN}===== 설정 완료! =====${NC}"
echo -e "\n${BLUE}다음 명령어로 애플리케이션을 실행하세요:${NC}"
echo -e "  ${GREEN}python interview_simulator.py${NC}"
echo -e "\n${BLUE}또는 Docker로 실행:${NC}"
echo -e "  ${GREEN}docker build -t interview-simulator .${NC}"
echo -e "  ${GREEN}docker run -p 7860:7860 --env-file .env interview-simulator${NC}"
echo -e "\n${BLUE}Azure에 배포:${NC}"
echo -e "  ${GREEN}./deploy.sh${NC}"

echo -e "\n${YELLOW}※ 가상환경을 활성화하려면: source venv/bin/activate${NC}"
