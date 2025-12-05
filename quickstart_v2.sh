#!/bin/bash

# ============================================
# 반도체 공정 학습 & 면접 시뮬레이터
# 빠른 시작 스크립트 (리팩토링 버전)
# ============================================

set -e  # 오류 발생 시 중단

echo "============================================"
echo "🎓 반도체 시뮬레이터 빠른 시작"
echo "============================================"
echo ""

# 1. Python 버전 확인
echo "📌 Step 1: Python 버전 확인..."
if command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
    PIP_CMD=pip3
elif command -v python &> /dev/null; then
    PYTHON_CMD=python
    PIP_CMD=pip
else
    echo "❌ Python이 설치되어 있지 않습니다"
    echo "   https://www.python.org/downloads/ 에서 Python 3.9 이상을 설치하세요"
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
echo "✅ Python $PYTHON_VERSION 발견"

# Python 버전 체크 (3.9 이상)
REQUIRED_VERSION="3.9"
if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Python 3.9 이상이 필요합니다 (현재: $PYTHON_VERSION)"
    exit 1
fi

echo ""

# 2. 가상환경 설정
echo "📌 Step 2: 가상환경 설정..."
if [ ! -d "venv" ]; then
    echo "   가상환경 생성 중..."
    $PYTHON_CMD -m venv venv
    echo "✅ 가상환경 생성 완료"
else
    echo "✅ 기존 가상환경 발견"
fi

echo ""

# 3. 가상환경 활성화
echo "📌 Step 3: 가상환경 활성화..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows
    source venv/Scripts/activate
else
    # macOS/Linux
    source venv/bin/activate
fi
echo "✅ 가상환경 활성화 완료"

echo ""

# 4. 패키지 설치
echo "📌 Step 4: 필수 패키지 설치..."
echo "   (이 작업은 몇 분 소요될 수 있습니다)"
$PIP_CMD install --upgrade pip > /dev/null 2>&1
$PIP_CMD install -r requirements.txt
echo "✅ 패키지 설치 완료"

echo ""

# 5. .env 파일 확인
echo "📌 Step 5: 환경 변수 확인..."
if [ ! -f ".env" ]; then
    echo "⚠️  .env 파일이 없습니다"
    echo "   .env.template을 .env로 복사 중..."
    cp .env.template .env
    echo "✅ .env 파일 생성 완료"
    echo ""
    echo "🔧 다음 단계:"
    echo "   1. .env 파일을 편집하세요"
    echo "   2. Azure API 키를 입력하세요:"
    echo "      - AZURE_OPENAI_API_KEY"
    echo "      - AZURE_SPEECH_KEY"
    echo "      - AZURE_SEARCH_KEY"
    echo ""
    read -p "   .env 파일을 지금 편집하시겠습니까? (y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if command -v nano &> /dev/null; then
            nano .env
        elif command -v vim &> /dev/null; then
            vim .env
        else
            echo "   텍스트 에디터로 .env 파일을 수동으로 편집하세요"
        fi
    else
        echo "   나중에 .env 파일을 편집하세요"
    fi
else
    echo "✅ .env 파일 존재"
    
    # 필수 환경 변수 확인
    if grep -q "your-api-key-here" .env || grep -q "your-.*-key" .env; then
        echo "⚠️  일부 API 키가 설정되지 않았습니다"
        echo "   .env 파일을 확인하고 실제 API 키로 변경하세요"
    fi
fi

echo ""

# 6. 지식 베이스 초기화 옵션
echo "📌 Step 6: 지식 베이스 초기화 (선택사항)"
read -p "   샘플 반도체 질문을 AI Search에 업로드하시겠습니까? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "   초기화 중... (Azure 연결 필요)"
    $PYTHON_CMD init_semiconductor_db.py
    if [ $? -eq 0 ]; then
        echo "✅ 지식 베이스 초기화 완료"
    else
        echo "⚠️  초기화 실패 - API 키를 확인하세요"
        echo "   나중에 다시 실행: python init_semiconductor_db.py"
    fi
else
    echo "   나중에 실행하려면: python init_semiconductor_db.py"
fi

echo ""

# 7. 시뮬레이터 실행
echo "============================================"
echo "✅ 설정 완료!"
echo "============================================"
echo ""
echo "🚀 시뮬레이터를 실행하려면:"
echo ""
echo "   python semiconductor_simulator_v2.py"
echo ""
echo "   브라우저에서 http://localhost:7860 접속"
echo ""
echo "💡 추가 기능:"
echo "   - 공정 시뮬레이터: python process_simulator.py"
echo "   - 수업자료 처리: python document_processor.py"
echo ""
echo "📖 상세 가이드: README.md 참조"
echo ""

read -p "지금 시뮬레이터를 실행하시겠습니까? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "🚀 시뮬레이터 시작 중..."
    echo "   (종료하려면 Ctrl+C를 누르세요)"
    echo ""
    $PYTHON_CMD semiconductor_simulator_v2.py
else
    echo ""
    echo "준비 완료! 언제든지 다음 명령으로 실행하세요:"
    echo "   python semiconductor_simulator_v2.py"
    echo ""
fi
