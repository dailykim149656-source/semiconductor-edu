#!/bin/bash

# 반도체 공정 학습 & 면접 시뮬레이터 빠른 시작

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}"
cat << "EOF"
╔══════════════════════════════════════════════════════╗
║                                                      ║
║   ⚡ 반도체 공정 학습 & 면접 시뮬레이터           ║
║                                                      ║
║   학부생을 위한 맞춤형 학습 플랫폼                 ║
║                                                      ║
╚══════════════════════════════════════════════════════╝
EOF
echo -e "${NC}\n"

# 1. Python 버전 확인
echo -e "${GREEN}1. Python 환경 확인...${NC}"
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python 버전: $python_version"

# 2. 가상환경 설정
echo -e "\n${GREEN}2. 가상환경 설정...${NC}"
if [ ! -d "venv" ]; then
    echo "가상환경 생성 중..."
    python3 -m venv venv
fi

echo "가상환경 활성화..."
source venv/bin/activate

# 3. 의존성 설치
echo -e "\n${GREEN}3. 패키지 설치...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

# 4. 환경 변수 확인
echo -e "\n${GREEN}4. 환경 변수 확인...${NC}"
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  .env 파일이 없습니다.${NC}"
    echo "템플릿에서 .env 파일을 생성합니다..."
    cp .env.template .env
    echo -e "${YELLOW}"
    echo "============================================"
    echo "⚠️  중요: .env 파일을 편집하여 Azure 키를 입력하세요!"
    echo "============================================"
    echo -e "${NC}"
    echo "다음 정보가 필요합니다:"
    echo "  - Azure Speech Service 키"
    echo "  - Azure OpenAI 키"
    echo "  - Azure AI Search 키"
    echo ""
    read -p "계속하려면 Enter를 누르세요..."
    exit 1
else
    echo "✅ .env 파일 발견"
    source .env
    
    # 필수 환경 변수 확인
    missing_vars=()
    [ -z "$AZURE_SPEECH_KEY" ] && missing_vars+=("AZURE_SPEECH_KEY")
    [ -z "$AZURE_OPENAI_KEY" ] && missing_vars+=("AZURE_OPENAI_KEY")
    [ -z "$AZURE_SEARCH_KEY" ] && missing_vars+=("AZURE_SEARCH_KEY")
    
    if [ ${#missing_vars[@]} -gt 0 ]; then
        echo -e "${YELLOW}⚠️  다음 환경 변수가 설정되지 않았습니다:${NC}"
        printf '%s\n' "${missing_vars[@]}"
        echo ""
        echo "계속하시겠습니까? (y/n)"
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        echo "✅ 필수 환경 변수 모두 설정됨"
    fi
fi

# 5. 데이터베이스 초기화
echo -e "\n${GREEN}5. 반도체 질문 DB 초기화...${NC}"
echo "샘플 질문을 업로드하시겠습니까? (y/n)"
read -r db_response

if [[ "$db_response" =~ ^[Yy]$ ]]; then
    echo "DB 초기화 중..."
    python init_semiconductor_db.py
    
    if [ $? -eq 0 ]; then
        echo -e "\n${GREEN}✅ DB 초기화 완료!${NC}"
    else
        echo -e "\n${YELLOW}⚠️  DB 초기화 중 오류가 발생했습니다.${NC}"
        echo "Azure AI Search 설정을 확인하세요."
    fi
else
    echo "DB 초기화 건너뜀"
fi

# 6. 실행 안내
echo -e "\n${GREEN}══════════════════════════════════════${NC}"
echo -e "${GREEN}✅ 설정 완료!${NC}"
echo -e "${GREEN}══════════════════════════════════════${NC}\n"

echo -e "${BLUE}애플리케이션 실행 방법:${NC}\n"
echo "  1. 메인 시뮬레이터:"
echo -e "     ${GREEN}python semiconductor_simulator.py${NC}\n"

echo "  2. 문서 처리 (수업자료 업로드):"
echo -e "     ${GREEN}python document_processor.py${NC}\n"

echo "  3. 이력서 분석 테스트:"
echo -e "     ${GREEN}python resume_analyzer.py${NC}\n"

echo -e "${BLUE}웹 브라우저에서 접속:${NC}"
echo -e "     ${GREEN}http://localhost:7860${NC}\n"

echo -e "${YELLOW}※ 가상환경 활성화: source venv/bin/activate${NC}\n"

echo "지금 실행하시겠습니까? (y/n)"
read -r run_response

if [[ "$run_response" =~ ^[Yy]$ ]]; then
    echo -e "\n${GREEN}시뮬레이터를 시작합니다...${NC}\n"
    python semiconductor_simulator.py
fi
