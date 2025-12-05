#!/bin/bash

# Azure App Service 시작 스크립트
echo "🚀 반도체 시뮬레이터 시작..."

# Python 버전 확인
echo "Python 버전:"
python --version

# 패키지 설치
echo "📦 패키지 설치 중..."
pip install --upgrade pip
pip install -r requirements.txt

# 환경 변수 확인
echo "🔍 환경 변수 확인..."
if [ -z "$AZURE_OPENAI_KEY" ]; then
    echo "⚠️  AZURE_OPENAI_KEY 없음"
fi

if [ -z "$AZURE_SPEECH_KEY" ]; then
    echo "⚠️  AZURE_SPEECH_KEY 없음"
fi

if [ -z "$AZURE_SEARCH_KEY" ]; then
    echo "⚠️  AZURE_SEARCH_KEY 없음"
fi

# Gradio 서버 설정
export GRADIO_SERVER_NAME=${GRADIO_SERVER_NAME:-0.0.0.0}
export GRADIO_SERVER_PORT=${GRADIO_SERVER_PORT:-8000}

echo "🌐 서버 설정: $GRADIO_SERVER_NAME:$GRADIO_SERVER_PORT"

# 애플리케이션 시작
echo "✅ 애플리케이션 시작!"
python semiconductor_simulator_v2.py
