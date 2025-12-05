"""
반도체 공정 학습 & 면접 시뮬레이터 (리팩토링 버전)
로컬 환경과 Azure 환경 모두 지원

주요 기능:
1. 수업자료 자동 처리 (PDF/PPT/DOCX)
2. 이력서/자소서 기반 맞춤형 질문 생성
3. 학습 모드 (주제별, 난이도별, 유형별)
4. 면접 모드 (일반/맞춤형)
5. 5가지 기준 상세 평가
6. Azure Speech TTS/STT
"""

import os
import sys
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv

import gradio as gr

# 환경 변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================
# Azure 클라이언트 초기화
# ============================================

def initialize_azure_clients():
    """Azure 서비스 클라이언트 초기화 (환경 구분)"""
    
    clients = {}
    environment = os.getenv('ENVIRONMENT', 'local')
    
    # 1. OpenAI 클라이언트
    try:
        # Azure OpenAI 우선 시도
        azure_endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
        azure_key = os.getenv('AZURE_OPENAI_API_KEY')
        
        if azure_endpoint and azure_key:
            from openai import AzureOpenAI
            clients['openai'] = AzureOpenAI(
                api_key=azure_key,
                api_version=os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-15-preview'),
                azure_endpoint=azure_endpoint
            )
            clients['openai_type'] = 'azure'
            clients['gpt_model'] = os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME', 'gpt-4')
            logger.info("✅ Azure OpenAI 클라이언트 초기화 성공")
        
        else:
            # 일반 OpenAI API
            openai_key = os.getenv('OPENAI_API_KEY')
            if openai_key:
                from openai import OpenAI
                clients['openai'] = OpenAI(api_key=openai_key)
                clients['openai_type'] = 'openai'
                clients['gpt_model'] = 'gpt-4-turbo-preview'
                logger.info("✅ OpenAI 클라이언트 초기화 성공")
            else:
                raise ValueError("OpenAI API 키가 설정되지 않았습니다")
    
    except Exception as e:
        logger.error(f"❌ OpenAI 클라이언트 초기화 실패: {e}")
        clients['openai'] = None
    
    # 2. Speech 클라이언트
    try:
        import azure.cognitiveservices.speech as speechsdk
        
        speech_key = os.getenv('AZURE_SPEECH_KEY')
        speech_region = os.getenv('AZURE_SPEECH_REGION', 'koreacentral')
        
        if speech_key and speech_region:
            speech_config = speechsdk.SpeechConfig(
                subscription=speech_key,
                region=speech_region
            )
            
            # 기본 한국어 음성 설정
            voice_name = os.getenv('AZURE_SPEECH_VOICE_NAME', 'ko-KR-SunHiNeural')
            speech_config.speech_synthesis_voice_name = voice_name
            
            # STT 설정 (한국어)
            speech_config.speech_recognition_language = "ko-KR"
            
            clients['speech_config'] = speech_config
            clients['speech_voice'] = voice_name
            logger.info(f"✅ Azure Speech 클라이언트 초기화 성공 (음성: {voice_name})")
        else:
            raise ValueError("Azure Speech 키가 설정되지 않았습니다")
    
    except Exception as e:
        logger.error(f"❌ Azure Speech 클라이언트 초기화 실패: {e}")
        clients['speech_config'] = None
    
    # 3. AI Search 클라이언트
    try:
        from azure.search.documents import SearchClient
        from azure.core.credentials import AzureKeyCredential
        
        search_endpoint = os.getenv('AZURE_SEARCH_ENDPOINT')
        search_key = os.getenv('AZURE_SEARCH_KEY')
        index_name = os.getenv('AZURE_SEARCH_INDEX_NAME', 'semiconductor-knowledge')
        
        if search_endpoint and search_key:
            clients['search'] = SearchClient(
                endpoint=search_endpoint,
                index_name=index_name,
                credential=AzureKeyCredential(search_key)
            )
            clients['search_index'] = index_name
            logger.info(f"✅ Azure AI Search 클라이언트 초기화 성공 (인덱스: {index_name})")
        else:
            raise ValueError("Azure Search 키가 설정되지 않았습니다")
    
    except Exception as e:
        logger.error(f"❌ Azure AI Search 클라이언트 초기화 실패: {e}")
        clients['search'] = None
    
    # 4. DALL-E 클라이언트 (선택사항)
    try:
        dalle_endpoint = os.getenv('AZURE_DALLE_ENDPOINT')
        dalle_key = os.getenv('AZURE_DALLE_API_KEY')
        
        if dalle_endpoint and dalle_key:
            from openai import AzureOpenAI
            clients['dalle'] = AzureOpenAI(
                api_key=dalle_key,
                api_version="2024-02-15-preview",
                azure_endpoint=dalle_endpoint
            )
            clients['dalle_model'] = os.getenv('AZURE_DALLE_DEPLOYMENT_NAME', 'dall-e-3')
            logger.info("✅ DALL-E 클라이언트 초기화 성공")
        else:
            logger.info("ℹ️  DALL-E 설정 없음 (선택사항)")
            clients['dalle'] = None
    
    except Exception as e:
        logger.warning(f"⚠️  DALL-E 클라이언트 초기화 실패 (선택사항): {e}")
        clients['dalle'] = None
    
    return clients


# ============================================
# SemiconductorSimulator 클래스
# ============================================

class SemiconductorSimulator:
    """반도체 공정 학습 & 면접 시뮬레이터"""
    
    def __init__(self):
        """초기화"""
        logger.info("🚀 반도체 시뮬레이터 초기화 시작...")
        
        # Azure 클라이언트 초기화
        self.clients = initialize_azure_clients()
        
        # 필수 클라이언트 확인
        if not self.clients.get('openai'):
            raise RuntimeError("OpenAI 클라이언트 초기화 실패 - API 키를 확인하세요")
        
        # 학생 프로필
        self.student_profile = None
        
        # 세션 데이터 (메모리)
        self.current_session_qa = []  # 현재 세션의 Q&A 리스트
        
        logger.info("✅ 반도체 시뮬레이터 초기화 완료")
    
    # ========================================
    # TTS/STT 기능
    # ========================================
    
    def text_to_speech(self, text: str) -> Optional[str]:
        """텍스트를 음성으로 변환 (Azure Speech TTS)"""
        
        if not self.clients.get('speech_config'):
            logger.warning("Speech 클라이언트가 없습니다")
            return None
        
        try:
            import azure.cognitiveservices.speech as speechsdk
            import tempfile
            
            # 오디오 설정
            audio_filename = tempfile.mktemp(suffix=".wav")
            audio_config = speechsdk.audio.AudioOutputConfig(filename=audio_filename)
            
            # Speech Synthesizer 생성
            synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=self.clients['speech_config'],
                audio_config=audio_config
            )
            
            # 음성 합성
            result = synthesizer.speak_text_async(text).get()
            
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                logger.info(f"✅ TTS 성공 (음성: {self.clients.get('speech_voice', 'default')})")
                return audio_filename
            else:
                logger.error(f"❌ TTS 실패: {result.reason}")
                return None
        
        except Exception as e:
            logger.error(f"❌ TTS 오류: {e}")
            return None
    
    def speech_to_text(self, audio_file: str) -> Optional[str]:
        """음성을 텍스트로 변환 (Azure Speech STT)"""
        
        if not self.clients.get('speech_config'):
            logger.warning("⚠️  Speech 클라이언트가 없습니다")
            return None
        
        if not audio_file:
            logger.warning("⚠️  음성 파일이 없습니다")
            return None
        
        try:
            import azure.cognitiveservices.speech as speechsdk
            import os
            
            # 파일 존재 확인
            if not os.path.exists(audio_file):
                logger.error(f"❌ 음성 파일을 찾을 수 없음: {audio_file}")
                return None
            
            file_size = os.path.getsize(audio_file)
            logger.info(f"🎤 STT 시작: {audio_file} ({file_size} bytes)")
            
            # 파일이 너무 작으면 (1KB 미만) 녹음 실패로 간주
            if file_size < 1000:
                logger.warning(f"⚠️  음성 파일이 너무 작음 ({file_size} bytes), 녹음이 제대로 안 된 것 같습니다")
                return None
            
            # 오디오 설정
            audio_config = speechsdk.audio.AudioConfig(filename=audio_file)
            
            # Speech Recognizer 생성
            recognizer = speechsdk.SpeechRecognizer(
                speech_config=self.clients['speech_config'],
                audio_config=audio_config
            )
            
            logger.info("🔄 음성 인식 중...")
            
            # 음성 인식 (타임아웃 10초)
            result = recognizer.recognize_once_async().get()
            
            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                recognized_text = result.text
                logger.info(f"✅ STT 성공: '{recognized_text[:100]}...'")
                return recognized_text
            
            elif result.reason == speechsdk.ResultReason.NoMatch:
                logger.warning(f"⚠️  STT 실패: 음성을 인식할 수 없음 (NoMatch)")
                logger.debug(f"NoMatch 상세: {result.no_match_details}")
                return None
            
            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation = result.cancellation_details
                logger.error(f"❌ STT 취소: {cancellation.reason}")
                if cancellation.reason == speechsdk.CancellationReason.Error:
                    logger.error(f"   오류 코드: {cancellation.error_code}")
                    logger.error(f"   오류 메시지: {cancellation.error_details}")
                return None
            
            else:
                logger.error(f"❌ STT 실패: {result.reason}")
                return None
        
        except Exception as e:
            logger.error(f"❌ STT 예외 발생: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return None
    
    # ========================================
    # RAG 검색 기능
    # ========================================
    
    def search_knowledge(
        self,
        query: str,
        process_filter: Optional[str] = None,
        difficulty_filter: Optional[str] = None,
        top_k: int = 5
    ) -> List[Dict]:
        """지식 베이스에서 관련 정보 검색"""
        
        if not self.clients.get('search'):
            logger.warning("⚠️  Search 클라이언트가 없습니다")
            return []
        
        try:
            # 검색 필터 구성
            filters = []
            if process_filter and process_filter != "전체":
                filters.append(f"process_category eq '{process_filter}'")
            if difficulty_filter and difficulty_filter != "전체":
                filters.append(f"difficulty eq '{difficulty_filter}'")
            
            filter_expression = " and ".join(filters) if filters else None
            
            logger.info(f"🔍 검색 시작: query='{query}', filter={filter_expression}, top={top_k}")
            
            # 검색 실행 (필터 없이 먼저 시도)
            if filter_expression:
                try:
                    results = list(self.clients['search'].search(
                        search_text=query,
                        filter=filter_expression,
                        top=top_k
                    ))
                except Exception as filter_error:
                    logger.warning(f"⚠️  필터 검색 실패, 필터 없이 재시도: {filter_error}")
                    results = list(self.clients['search'].search(
                        search_text=query,
                        top=top_k
                    ))
            else:
                results = list(self.clients['search'].search(
                    search_text=query,
                    top=top_k
                ))
            
            # 결과 변환 (유연한 필드 처리)
            knowledge_items = []
            for result in results:
                # 결과를 딕셔너리로 변환
                if hasattr(result, '__dict__'):
                    result_dict = result.__dict__
                else:
                    result_dict = dict(result)
                
                # 필드 이름 매핑 (다양한 필드명 지원)
                item = {
                    'question': result_dict.get('question') or result_dict.get('Question') or result_dict.get('title') or '',
                    'answer': result_dict.get('answer') or result_dict.get('Answer') or result_dict.get('content') or '',
                    'process': result_dict.get('process_category') or result_dict.get('category') or result_dict.get('process') or '일반',
                    'difficulty': result_dict.get('difficulty') or result_dict.get('level') or '중급',
                    'type': result_dict.get('question_type') or result_dict.get('type') or '개념이해',
                    'score': result_dict.get('@search.score', 1.0)
                }
                
                knowledge_items.append(item)
            
            if knowledge_items:
                logger.info(f"✅ 검색 성공: {len(knowledge_items)}개 결과 발견")
                logger.debug(f"첫 번째 결과: {knowledge_items[0]['question'][:50]}...")
            else:
                logger.warning(f"⚠️  검색 결과 없음: '{query}'")
            
            return knowledge_items
        
        except Exception as e:
            logger.error(f"❌ 검색 오류: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return []
    
    # ========================================
    # GPT 호출 기능
    # ========================================
    
    def call_gpt(self, messages: List[Dict[str, str]], temperature: float = 0.7) -> Optional[str]:
        """GPT API 호출 (Azure/OpenAI 자동 구분)"""
        
        if not self.clients.get('openai'):
            logger.error("OpenAI 클라이언트가 없습니다")
            return None
        
        try:
            model = self.clients['gpt_model']
            
            response = self.clients['openai'].chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=2000
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            logger.error(f"❌ GPT 호출 오류: {e}")
            return None
    
    # ========================================
    # 학습 모드 - 질문 생성
    # ========================================
    
    def generate_study_question(
        self,
        topic: str,
        difficulty: str,
        question_type: str
    ) -> Tuple[str, str]:
        """학습 모드 질문 생성"""
        
        logger.info(f"📖 학습 질문 생성 시작: {topic} ({difficulty}, {question_type})")
        
        # RAG 검색
        knowledge = self.search_knowledge(
            query=topic,
            difficulty_filter=difficulty,
            top_k=3
        )
        
        # 컨텍스트 구성
        if knowledge:
            context = "\n\n".join([
                f"Q: {k['question']}\nA: {k['answer']}"
                for k in knowledge if k.get('question') and k.get('answer')
            ])
            logger.info(f"✅ RAG 컨텍스트 생성 완료 ({len(knowledge)}개 참조)")
        else:
            # RAG 결과가 없어도 GPT가 직접 질문 생성
            context = f"주제: {topic}에 대한 질문을 생성합니다."
            logger.warning(f"⚠️  RAG 결과 없음, GPT가 직접 생성")
        
        # GPT 프롬프트
        difficulty_guide = {
            '기초': '기본 개념과 정의를 확인하는',
            '중급': '원리와 메커니즘을 설명할 수 있는',
            '고급': '실무 적용과 문제 해결 능력을 평가하는'
        }
        
        type_guide = {
            '개념이해': '핵심 개념과 용어의 정의를 설명하도록',
            '원리설명': '물리/화학적 원리와 메커니즘을 설명하도록',
            '응용': '실제 공정에서의 응용 사례와 효과를 설명하도록',
            '비교': '다른 공정/기술과 비교 분석하도록',
            '실무': '실무에서 발생하는 문제와 해결 방법을 다루도록'
        }
        
        messages = [
            {
                "role": "system",
                "content": f"""당신은 반도체 공정 전문가입니다.
학생의 학습을 돕기 위해 {difficulty_guide.get(difficulty, '')} {type_guide.get(question_type, '')} 질문을 생성하세요.

주제: {topic}
난이도: {difficulty}
질문 유형: {question_type}

{'참고 자료:' if knowledge else '주제에 대한 일반적인 지식을 바탕으로'}
{context}

질문은 구체적이고 명확하게 작성하세요. 반도체 공정에 대한 전문적인 질문을 만들어주세요."""
            },
            {
                "role": "user",
                "content": f"{topic}에 대한 {difficulty} 난이도의 {question_type} 질문을 1개 생성해주세요."
            }
        ]
        
        question = self.call_gpt(messages, temperature=0.8)
        
        if question:
            logger.info(f"✅ 학습 질문 생성 완료")
            return question, context
        else:
            logger.error(f"❌ 질문 생성 실패")
            return "질문 생성에 실패했습니다. GPT API를 확인하세요.", context
    
    # ========================================
    # 면접 모드 - 질문 생성
    # ========================================
    
    def generate_interview_question(
        self,
        use_profile: bool = False,
        focus_area: Optional[str] = None
    ) -> Tuple[str, str]:
        """면접 모드 질문 생성"""
        
        logger.info(f"💼 면접 질문 생성 시작 (프로필 사용: {use_profile}, 중점: {focus_area})")
        
        if use_profile and not self.student_profile:
            logger.warning("⚠️  프로필이 없습니다")
            return "먼저 '프로필 설정' 탭에서 이력서와 자기소개서를 분석해주세요.", ""
        
        # RAG 검색
        if focus_area and focus_area != "전체":
            knowledge = self.search_knowledge(query=focus_area, top_k=3)
        else:
            # 기본 반도체 공정 질문
            knowledge = self.search_knowledge(query="반도체 공정", top_k=3)
        
        context = "\n\n".join([
            f"Q: {k['question']}\nA: {k['answer']}"
            for k in knowledge if k.get('question') and k.get('answer')
        ]) if knowledge else "반도체 공정에 대한 일반적인 지식"
        
        # 프롬프트 구성
        if use_profile and self.student_profile:
            # 프로필 정보 추출 (다양한 필드 시도)
            education = self.student_profile.get('education') or self.student_profile.get('학력') or 'N/A'
            experiences = self.student_profile.get('experiences') or self.student_profile.get('경험') or []
            interests = self.student_profile.get('interests') or self.student_profile.get('관심분야') or self.student_profile.get('interest') or []
            skills = self.student_profile.get('skills') or self.student_profile.get('기술') or self.student_profile.get('스킬') or []
            projects = self.student_profile.get('projects') or self.student_profile.get('프로젝트') or []
            
            # 프로필 요약 생성
            profile_summary = f"""
학생 프로필:
- 학력: {education}
- 주요 경험: {', '.join(str(e) for e in experiences[:3]) if experiences else '경험 정보 없음'}
- 프로젝트: {', '.join(str(p) for p in projects[:2]) if projects else '프로젝트 정보 없음'}
- 관심 분야: {', '.join(str(i) for i in interests[:3]) if interests else '관심 분야 정보 없음'}
- 기술 스킬: {', '.join(str(s) for s in skills[:5]) if skills else '스킬 정보 없음'}

프로필 전체 데이터:
{str(self.student_profile)[:500]}
"""
            
            logger.info(f"📊 프로필 요약: {len(experiences)}개 경험, {len(interests)}개 관심사, {len(skills)}개 스킬")
            
            messages = [
                {
                    "role": "system",
                    "content": f"""당신은 반도체 기업의 면접관입니다.
다음 학생의 프로필을 바탕으로 맞춤형 면접 질문을 생성하세요.

{profile_summary}

질문 생성 가이드:
1. 학생의 구체적인 경험(프로젝트, 인턴 등)을 언급하며 질문
2. 관심 분야와 기술 스킬을 연결하여 심화 질문
3. 실제 경험에서 배운 점을 확인하는 질문
4. 이론과 실무를 연결하는 질문

예시:
- "ITO 박막 프로젝트에서 RF 파워를 어떻게 최적화했나요?"
- "MEMS 센서 제작 시 RIE 식각에서 어떤 어려움이 있었나요?"
- "ALD 공정에 관심이 많다고 했는데, CVD와 비교하여 장단점을 설명해주세요."

질문은 구체적이고 학생의 경험을 직접 언급해야 합니다."""
                },
                {
                    "role": "user",
                    "content": "이 학생의 프로필을 바탕으로 맞춤형 면접 질문 1개를 생성해주세요. 학생의 구체적인 경험이나 프로젝트를 언급하세요."
                }
            ]
        
        else:
            messages = [
                {
                    "role": "system",
                    "content": f"""당신은 반도체 기업의 면접관입니다.
학부 수준의 지원자에게 적합한 기술 면접 질문을 생성하세요.

{'참고 자료:' if knowledge else '주제:'}
{context}

질문은 다음을 평가할 수 있어야 합니다:
- 반도체 공정에 대한 이론적 지식
- 문제 해결 능력
- 실무 적용 가능성
- 학습 태도

구체적인 공정 파라미터나 메커니즘을 포함한 질문을 만드세요."""
                },
                {
                    "role": "user",
                    "content": "반도체 공정 관련 면접 질문 1개를 생성해주세요. 구체적이고 기술적인 질문이어야 합니다."
                }
            ]
        
        question = self.call_gpt(messages, temperature=0.8)
        
        if question:
            logger.info(f"✅ 면접 질문 생성 완료")
            return question, context
        else:
            logger.error(f"❌ 질문 생성 실패")
            return "질문 생성에 실패했습니다. GPT API를 확인하세요.", context
    
    # ========================================
    # 답변 평가
    # ========================================
    
    def evaluate_answer(
        self,
        question: str,
        answer: str,
        context: str
    ) -> Dict:
        """답변 평가 (5가지 기준)"""
        
        messages = [
            {
                "role": "system",
                "content": f"""당신은 반도체 공정 전문가이자 교육자입니다.
학생의 답변을 다음 5가지 기준으로 평가하세요:

1. 정확성 (30점): 기술적 정확도, 용어 사용, 수치 정확성
2. 깊이 (25점): 원리 이해도, 메커니즘 설명, 이론적 배경
3. 구조 (20점): 논리적 흐름, 체계적 설명, 명확성
4. 응용 (15점): 실무/실습 연결, 문제 해결 접근
5. 의사소통 (10점): 표현력, 용어 정리, 설명 명확성

참고 자료:
{context}

질문: {question}
답변: {answer}

다음 형식으로 JSON 응답하세요:
{{
    "scores": {{
        "accuracy": <0-30>,
        "depth": <0-25>,
        "structure": <0-20>,
        "application": <0-15>,
        "communication": <0-10>
    }},
    "total_score": <총점>,
    "strengths": ["강점1", "강점2"],
    "improvements": ["개선점1", "개선점2"],
    "detailed_feedback": "상세 피드백",
    "recommended_topics": ["복습 추천 주제1", "추천 주제2"]
}}"""
            },
            {
                "role": "user",
                "content": f"다음 답변을 평가해주세요:\n\n{answer}"
            }
        ]
        
        result = self.call_gpt(messages, temperature=0.3)
        
        if result:
            try:
                import json
                # JSON 추출 (마크다운 코드 블록 제거)
                if "```json" in result:
                    result = result.split("```json")[1].split("```")[0]
                elif "```" in result:
                    result = result.split("```")[1].split("```")[0]
                
                evaluation = json.loads(result.strip())
                logger.info(f"✅ 답변 평가 완료 (총점: {evaluation.get('total_score', 0)})")
                
                # 세션에 Q&A 추가 (메모리만)
                self.current_session_qa.append({
                    "question": question,
                    "answer": answer,
                    "evaluation": evaluation,
                    "timestamp": datetime.now().isoformat()
                })
                logger.info(f"💾 세션에 저장 완료 (총 {len(self.current_session_qa)}개)")
                
                return evaluation
            
            except Exception as e:
                logger.error(f"❌ 평가 결과 파싱 오류: {e}")
                return {"error": "평가 결과 파싱 실패"}
        
        else:
            return {"error": "평가 실패"}
    
    # ========================================
    # 프로필 분석
    # ========================================
    
    def generate_pdf_report(self, user_name: str = "학생") -> Optional[str]:
        """PDF 면접 리포트 생성 (HTML 대체 가능)"""
        
        if not self.current_session_qa:
            logger.warning("⚠️  저장된 Q&A가 없습니다")
            return None
        
        try:
            # reportlab 사용 시도
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import cm
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib import colors
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            
            use_reportlab = True
            logger.info("✅ reportlab 사용 가능")
            
        except ImportError:
            use_reportlab = False
            logger.warning("⚠️  reportlab 없음 - HTML로 대체")
        
        # 파일명
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if use_reportlab:
            # PDF로 생성
            output_path = f"interview_report_{timestamp}.pdf"
            return self._generate_pdf_with_reportlab(user_name, output_path)
        else:
            # HTML로 생성
            output_path = f"interview_report_{timestamp}.html"
            return self._generate_html_report(user_name, output_path)
    
    def _generate_html_report(self, user_name: str, output_path: str) -> Optional[str]:
        """HTML 리포트 생성 (reportlab 없을 때)"""
        
        try:
            # 평균 점수 계산
            total_scores = []
            accuracy_scores = []
            depth_scores = []
            structure_scores = []
            application_scores = []
            communication_scores = []
            
            for qa in self.current_session_qa:
                eval_data = qa.get('evaluation', {})
                if 'total_score' in eval_data:
                    total_scores.append(eval_data['total_score'])
                    scores = eval_data.get('scores', {})
                    accuracy_scores.append(scores.get('accuracy', 0))
                    depth_scores.append(scores.get('depth', 0))
                    structure_scores.append(scores.get('structure', 0))
                    application_scores.append(scores.get('application', 0))
                    communication_scores.append(scores.get('communication', 0))
            
            avg_total = sum(total_scores) / len(total_scores) if total_scores else 0
            avg_accuracy = sum(accuracy_scores) / len(accuracy_scores) if accuracy_scores else 0
            avg_depth = sum(depth_scores) / len(depth_scores) if depth_scores else 0
            avg_structure = sum(structure_scores) / len(structure_scores) if structure_scores else 0
            avg_application = sum(application_scores) / len(application_scores) if application_scores else 0
            avg_communication = sum(communication_scores) / len(communication_scores) if communication_scores else 0
            
            # HTML 생성
            html_content = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>면접 분석 리포트 - {user_name}</title>
    <style>
        body {{
            font-family: 'Malgun Gothic', sans-serif;
            max-width: 900px;
            margin: 40px auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #1a237e;
            text-align: center;
            border-bottom: 3px solid #1a237e;
            padding-bottom: 20px;
        }}
        h2 {{
            color: #283593;
            margin-top: 30px;
            border-left: 4px solid #3f51b5;
            padding-left: 15px;
        }}
        .info-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        .info-table td {{
            padding: 12px;
            border: 1px solid #ddd;
        }}
        .info-table td:first-child {{
            background: #e8eaf6;
            width: 150px;
            font-weight: bold;
        }}
        .score-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        .score-table th {{
            background: #3f51b5;
            color: white;
            padding: 12px;
            text-align: center;
        }}
        .score-table td {{
            padding: 12px;
            text-align: center;
            border: 1px solid #ddd;
        }}
        .score-table tr:nth-child(2) {{
            background: #fffde7;
            font-weight: bold;
        }}
        .qa-section {{
            background: #fafafa;
            padding: 20px;
            margin: 20px 0;
            border-radius: 5px;
            border-left: 4px solid #3f51b5;
        }}
        .question {{
            font-weight: bold;
            color: #1a237e;
            margin-bottom: 10px;
        }}
        .answer {{
            margin: 10px 0;
            padding: 10px;
            background: white;
            border-radius: 3px;
        }}
        .score {{
            color: #2e7d32;
            font-weight: bold;
            font-size: 1.2em;
        }}
        .strengths {{
            color: #2e7d32;
        }}
        .improvements {{
            color: #d32f2f;
        }}
        ul {{
            margin: 10px 0;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #666;
        }}
        @media print {{
            body {{
                background: white;
            }}
            .container {{
                box-shadow: none;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🎓 반도체 공정 면접 분석 리포트</h1>
        
        <h2>📋 기본 정보</h2>
        <table class="info-table">
            <tr>
                <td>이름</td>
                <td>{user_name}</td>
            </tr>
            <tr>
                <td>분석 일시</td>
                <td>{datetime.now().strftime("%Y년 %m월 %d일 %H:%M")}</td>
            </tr>
            <tr>
                <td>총 질문 수</td>
                <td>{len(self.current_session_qa)}개</td>
            </tr>
            {'<tr><td>학력</td><td>' + self.student_profile.get('education', 'N/A') + '</td></tr>' if self.student_profile else ''}
        </table>
        
        <h2>📊 종합 평가</h2>
        <table class="score-table">
            <tr>
                <th>평가 항목</th>
                <th>평균 점수</th>
                <th>만점</th>
                <th>달성률</th>
            </tr>
            <tr>
                <td>총점</td>
                <td>{avg_total:.1f}</td>
                <td>100</td>
                <td>{avg_total:.0f}%</td>
            </tr>
            <tr>
                <td>정확성</td>
                <td>{avg_accuracy:.1f}</td>
                <td>30</td>
                <td>{avg_accuracy/30*100:.0f}%</td>
            </tr>
            <tr>
                <td>깊이</td>
                <td>{avg_depth:.1f}</td>
                <td>25</td>
                <td>{avg_depth/25*100:.0f}%</td>
            </tr>
            <tr>
                <td>구조</td>
                <td>{avg_structure:.1f}</td>
                <td>20</td>
                <td>{avg_structure/20*100:.0f}%</td>
            </tr>
            <tr>
                <td>응용</td>
                <td>{avg_application:.1f}</td>
                <td>15</td>
                <td>{avg_application/15*100:.0f}%</td>
            </tr>
            <tr>
                <td>의사소통</td>
                <td>{avg_communication:.1f}</td>
                <td>10</td>
                <td>{avg_communication/10*100:.0f}%</td>
            </tr>
        </table>
        
        <h2>📝 질문별 상세 분석</h2>
"""
            
            # 질문별 분석
            for idx, qa in enumerate(self.current_session_qa, 1):
                eval_data = qa.get('evaluation', {})
                html_content += f"""
        <div class="qa-section">
            <div class="question">질문 {idx}</div>
            <p>{qa.get('question', 'N/A')}</p>
            
            <div class="question">답변</div>
            <div class="answer">{qa.get('answer', 'N/A')[:500]}...</div>
            
            <div class="score">점수: {eval_data.get('total_score', 0):.0f}/100</div>
            
            <div class="strengths">
                <strong>💪 강점:</strong>
                <ul>
"""
                for strength in eval_data.get('strengths', [])[:3]:
                    html_content += f"                    <li>{strength}</li>\n"
                
                html_content += """
                </ul>
            </div>
            
            <div class="improvements">
                <strong>📈 개선점:</strong>
                <ul>
"""
                for improvement in eval_data.get('improvements', [])[:3]:
                    html_content += f"                    <li>{improvement}</li>\n"
                
                html_content += """
                </ul>
            </div>
        </div>
"""
            
            # 종합 피드백
            all_strengths = []
            all_improvements = []
            all_recommendations = []
            
            for qa in self.current_session_qa:
                eval_data = qa.get('evaluation', {})
                all_strengths.extend(eval_data.get('strengths', []))
                all_improvements.extend(eval_data.get('improvements', []))
                all_recommendations.extend(eval_data.get('recommended_topics', []))
            
            unique_strengths = list(set(all_strengths))[:5]
            unique_improvements = list(set(all_improvements))[:5]
            unique_recommendations = list(set(all_recommendations))[:5]
            
            html_content += """
        <h2>💡 종합 피드백 및 학습 가이드</h2>
        
        <div class="strengths">
            <strong>✅ 주요 강점:</strong>
            <ul>
"""
            for strength in unique_strengths:
                html_content += f"                <li>{strength}</li>\n"
            
            html_content += """
            </ul>
        </div>
        
        <div class="improvements">
            <strong>🎯 중점 개선 사항:</strong>
            <ul>
"""
            for improvement in unique_improvements:
                html_content += f"                <li>{improvement}</li>\n"
            
            html_content += """
            </ul>
        </div>
        
        <div>
            <strong>📚 복습 추천 주제:</strong>
            <ul>
"""
            for topic in unique_recommendations:
                html_content += f"                <li>{topic}</li>\n"
            
            html_content += f"""
            </ul>
        </div>
        
        <div class="footer">
            <p>생성 일시: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            <p>반도체 공정 학습 & 면접 시뮬레이터</p>
        </div>
    </div>
</body>
</html>
"""
            
            # 파일 저장
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"✅ HTML 리포트 생성 완료: {output_path}")
            return output_path
        
        except Exception as e:
            logger.error(f"❌ HTML 리포트 생성 실패: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return None
    
    def _generate_pdf_with_reportlab(self, user_name: str, output_path: str) -> Optional[str]:
        """reportlab으로 PDF 생성"""
        # 기존 storage_manager의 PDF 생성 로직 사용
        try:
            from storage_manager import PDFReportGenerator
            pdf_gen = PDFReportGenerator()
            return pdf_gen.generate_interview_report(
                user_name=user_name,
                profile=self.student_profile,
                qa_list=self.current_session_qa,
                output_path=output_path
            )
        except Exception as e:
            logger.error(f"❌ PDF 생성 실패: {e}")
            # HTML로 폴백
            return self._generate_html_report(user_name, output_path.replace('.pdf', '.html'))
    
    def clear_session(self):
        """현재 세션 초기화"""
        self.current_session_qa = []
        logger.info("🔄 세션 초기화 완료")
    
    # ========================================
    # 프로필 분석
    # ========================================
    
    def analyze_profile(self, resume_text: str, ps_text: str) -> Dict:
        """이력서/자소서 분석"""
        
        logger.info("👤 프로필 분석 시작...")
        
        messages = [
            {
                "role": "system",
                "content": """당신은 반도체 분야 채용 전문가입니다.
이력서와 자기소개서를 분석하여 다음 정보를 **매우 상세하게** 추출하세요:

1. education: 대학, 학과, 학년, GPA (문자열)
2. experiences: 프로젝트/인턴/실습 경험 목록 (리스트, 각 항목에 제목과 간단한 설명)
3. projects: 구체적인 프로젝트 목록 (리스트, 프로젝트명과 사용 기술)
4. skills: 기술 스킬 목록 (리스트)
   - 증착 장비: 스퍼터링, CVD, ALD 등
   - 식각 장비: RIE, 습식 식각 등
   - 분석 장비: XRD, SEM, TEM, XPS 등
   - 소프트웨어: MATLAB, Python 등
5. interests: 관심 분야 목록 (리스트, 증착/식각/리소그래피 등)
6. career_goal: 단기/장기 커리어 목표 (문자열)
7. strengths: 강점 목록 (리스트)
8. weaknesses: 보완이 필요한 부분 (리스트)

**매우 중요**: 
- 모든 리스트 항목은 구체적으로 작성
- 프로젝트 경험은 반드시 포함 (예: "ITO 박막 증착 프로젝트")
- 기술 스킬은 장비 이름까지 구체적으로 (예: "RF 스퍼터링", "RIE 식각")

반드시 다음 형식의 JSON으로 응답하세요:
{
    "education": "서울대학교 재료공학부 3학년, GPA 3.82/4.3",
    "experiences": [
        "ITO 박막 증착 최적화 프로젝트 (RF 스퍼터링)",
        "MEMS 압력센서 제작 실습",
        "저온 ALD 공정 연구 (인턴)"
    ],
    "projects": [
        "ITO 박막 증착 프로젝트",
        "MEMS 센서 제작"
    ],
    "skills": [
        "RF 스퍼터링",
        "RIE 식각",
        "XRD 분석",
        "Python"
    ],
    "interests": [
        "박막 증착",
        "CVD 공정",
        "공정 최적화"
    ],
    "career_goal": "대기업 공정 엔지니어 목표",
    "strengths": ["끈기", "실험 설계"],
    "weaknesses": ["영어 커뮤니케이션"]
}"""
            },
            {
                "role": "user",
                "content": f"다음 이력서와 자기소개서를 분석하여 위 형식의 JSON으로 추출해주세요:\n\n이력서:\n{resume_text[:2000]}\n\n자기소개서:\n{ps_text[:2000]}"
            }
        ]
        
        result = self.call_gpt(messages, temperature=0.3)
        
        if result:
            try:
                import json
                # JSON 추출
                if "```json" in result:
                    result = result.split("```json")[1].split("```")[0]
                elif "```" in result:
                    result = result.split("```")[1].split("```")[0]
                
                profile = json.loads(result.strip())
                
                # 프로필 검증 및 기본값 설정
                if not profile.get('experiences'):
                    profile['experiences'] = []
                if not profile.get('skills'):
                    profile['skills'] = []
                if not profile.get('interests'):
                    profile['interests'] = []
                
                # 프로필 저장
                self.student_profile = profile
                
                logger.info(f"✅ 프로필 분석 완료:")
                logger.info(f"   - 경험: {len(profile.get('experiences', []))}개")
                logger.info(f"   - 스킬: {len(profile.get('skills', []))}개")
                logger.info(f"   - 관심사: {len(profile.get('interests', []))}개")
                logger.debug(f"   - 프로필 데이터: {str(profile)[:200]}...")
                
                return profile
            
            except json.JSONDecodeError as e:
                logger.error(f"❌ JSON 파싱 오류: {e}")
                logger.debug(f"GPT 응답: {result[:500]}")
                
                # 원본 텍스트 기반 간단 분석
                fallback_profile = {
                    "education": "분석 중",
                    "experiences": ["이력서 내용 참조"],
                    "skills": ["분석 실패"],
                    "interests": ["반도체 공정"],
                    "career_goal": "분석 중",
                    "strengths": [],
                    "weaknesses": []
                }
                self.student_profile = fallback_profile
                return {"error": f"JSON 파싱 실패: {str(e)}", "partial_data": fallback_profile}
            
            except Exception as e:
                logger.error(f"❌ 프로필 분석 오류: {e}")
                return {"error": f"프로필 분석 실패: {str(e)}"}
        
        else:
            logger.error("❌ GPT 응답 없음")
            return {"error": "GPT API 호출 실패"}


# ============================================
# Gradio UI 구성
# ============================================

def create_gradio_interface(simulator: SemiconductorSimulator):
    """Gradio 인터페이스 생성"""
    
    # Gradio 버전 호환성 처리
    try:
        demo = gr.Blocks(
            theme=gr.themes.Soft(),
            title="반도체 공정 학습 & 면접 시뮬레이터"
        )
    except TypeError:
        # 구버전 Gradio (theme 미지원)
        demo = gr.Blocks(title="반도체 공정 학습 & 면접 시뮬레이터")
    
    with demo:
        
        gr.Markdown("""
        # 🎓 반도체 공정 학습 & 면접 시뮬레이터
        
        ### Azure Speech + OpenAI GPT-4 + AI Search 기반
        
        **주요 기능:**
        - 📚 수업자료 자동 처리 (PDF/PPT/DOCX)
        - 👤 이력서/자소서 기반 맞춤형 질문
        - 📖 학습 모드 (주제별, 난이도별, 유형별)
        - 💼 면접 모드 (일반/맞춤형)
        - 📊 5가지 기준 상세 평가
        """)
        
        # 상태 변수
        current_question = gr.State("")
        current_context = gr.State("")
        
        with gr.Tabs():
            # ===== 프로필 설정 탭 =====
            with gr.Tab("👤 프로필 설정"):
                gr.Markdown("### 이력서와 자기소개서를 업로드하면 맞춤형 질문을 생성합니다")
                
                with gr.Row():
                    resume_file = gr.File(label="이력서 (PDF/DOCX)", file_types=[".pdf", ".docx"])
                    ps_file = gr.File(label="자기소개서 (PDF/DOCX)", file_types=[".pdf", ".docx"])
                
                analyze_btn = gr.Button("📊 분석 시작", variant="primary")
                profile_output = gr.JSON(label="분석 결과")
                
                def analyze_profile_handler(resume, ps):
                    if not resume or not ps:
                        return {"❌ 오류": "이력서와 자기소개서를 모두 업로드해주세요"}
                    
                    # 파일에서 텍스트 추출
                    try:
                        from resume_analyzer import ResumeAnalyzer
                        analyzer = ResumeAnalyzer()
                        
                        logger.info(f"📄 파일 처리 시작: {resume.name}, {ps.name}")
                        
                        resume_text = analyzer.extract_text_from_pdf(resume.name) if resume.name.endswith('.pdf') else analyzer.extract_text_from_docx(resume.name)
                        ps_text = analyzer.extract_text_from_pdf(ps.name) if ps.name.endswith('.pdf') else analyzer.extract_text_from_docx(ps.name)
                        
                        logger.info(f"✅ 텍스트 추출 완료: 이력서 {len(resume_text)}자, 자소서 {len(ps_text)}자")
                        
                        profile = simulator.analyze_profile(resume_text, ps_text)
                        
                        # 출력 포맷 개선
                        if profile and 'error' not in profile:
                            formatted_output = {
                                "✅ 분석 완료": "프로필이 저장되었습니다. 면접 모드에서 맞춤형 질문을 사용하세요!",
                                "📚 학력": profile.get('education', 'N/A'),
                                "💼 경험 ({0}개)".format(len(profile.get('experiences', []))): profile.get('experiences', []),
                                "🔬 프로젝트 ({0}개)".format(len(profile.get('projects', []))): profile.get('projects', []),
                                "🛠️ 기술 스킬 ({0}개)".format(len(profile.get('skills', []))): profile.get('skills', []),
                                "❤️ 관심 분야 ({0}개)".format(len(profile.get('interests', []))): profile.get('interests', []),
                                "🎯 커리어 목표": profile.get('career_goal', 'N/A'),
                                "💪 강점": profile.get('strengths', []),
                                "📈 보완 필요": profile.get('weaknesses', [])
                            }
                            return formatted_output
                        else:
                            return profile
                    
                    except ImportError:
                        logger.error("❌ resume_analyzer 모듈을 찾을 수 없습니다")
                        return {"❌ 오류": "resume_analyzer.py 파일이 필요합니다"}
                    
                    except Exception as e:
                        logger.error(f"❌ 프로필 분석 오류: {e}")
                        import traceback
                        logger.debug(traceback.format_exc())
                        return {"❌ 오류": str(e), "💡 힌트": "이력서와 자기소개서가 올바른 형식인지 확인하세요"}
                
                analyze_btn.click(
                    analyze_profile_handler,
                    inputs=[resume_file, ps_file],
                    outputs=profile_output
                )
            
            # ===== 학습 모드 탭 =====
            with gr.Tab("📖 학습 모드"):
                gr.Markdown("### 주제를 선택하고 난이도와 질문 유형을 설정하세요")
                
                with gr.Row():
                    with gr.Column():
                        study_topic = gr.Textbox(
                            label="학습 주제",
                            placeholder="예: CVD 증착 공정",
                            value="CVD 증착"
                        )
                        study_difficulty = gr.Radio(
                            ["기초", "중급", "고급"],
                            label="난이도",
                            value="중급"
                        )
                        study_type = gr.Radio(
                            ["개념이해", "원리설명", "응용", "비교", "실무"],
                            label="질문 유형",
                            value="원리설명"
                        )
                        
                        study_start_btn = gr.Button("▶️ 학습 시작", variant="primary")
                    
                    with gr.Column():
                        study_question_output = gr.Textbox(label="질문", lines=5)
                        study_audio_output = gr.Audio(
                            label="질문 음성 (자동 재생)",
                            type="filepath",
                            autoplay=True
                        )
                
                with gr.Row():
                    with gr.Column():
                        study_answer_text = gr.Textbox(
                            label="텍스트 답변", 
                            lines=5, 
                            placeholder="답변을 입력하세요"
                        )
                    with gr.Column():
                        study_answer_audio = gr.Audio(
                            label="🎤 음성 답변 녹음",
                            sources=["microphone"],
                            type="filepath"
                        )
                
                # 녹음된 음성 재생 섹션
                gr.Markdown("### 🔊 녹음된 답변 확인")
                study_recorded_playback = gr.Audio(
                    label="녹음된 음성 재생",
                    type="filepath",
                    interactive=False
                )
                
                study_submit_btn = gr.Button("✅ 답변 제출", variant="primary")
                study_evaluation_output = gr.JSON(label="평가 결과")
                
                # 녹음 완료 시 자동으로 재생 컴포넌트에 복사
                def on_audio_recorded(audio):
                    """녹음 완료 시 재생 컴포넌트 업데이트"""
                    if audio:
                        logger.info(f"🎤 녹음 완료: {audio}")
                        return audio
                    return None
                
                study_answer_audio.change(
                    on_audio_recorded,
                    inputs=[study_answer_audio],
                    outputs=[study_recorded_playback]
                )
                
                def start_study(topic, difficulty, q_type):
                    question, context = simulator.generate_study_question(topic, difficulty, q_type)
                    audio = simulator.text_to_speech(question)
                    return question, audio, question, context
                
                study_start_btn.click(
                    start_study,
                    inputs=[study_topic, study_difficulty, study_type],
                    outputs=[study_question_output, study_audio_output, current_question, current_context]
                )
                
                def evaluate_study_answer(question, context, text_answer, audio_answer):
                    """답변 평가 (텍스트 또는 음성)"""
                    logger.info(f"📝 답변 평가 시작")
                    logger.info(f"   - 텍스트 답변 길이: {len(text_answer) if text_answer else 0}")
                    logger.info(f"   - 음성 데이터 타입: {type(audio_answer)}")
                    logger.info(f"   - 음성 데이터 값: {audio_answer}")
                    
                    # Gradio Audio 컴포넌트는 튜플 또는 문자열로 전달됨
                    audio_file_path = None
                    if audio_answer:
                        if isinstance(audio_answer, tuple):
                            # (sample_rate, audio_data) 형태
                            logger.info("📦 튜플 형태의 오디오 데이터")
                            if len(audio_answer) >= 2:
                                # 두 번째 요소가 파일 경로일 수 있음
                                if isinstance(audio_answer[1], str):
                                    audio_file_path = audio_answer[1]
                                else:
                                    # NumPy 배열인 경우 임시 파일로 저장
                                    import tempfile
                                    import soundfile as sf
                                    
                                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
                                    sf.write(temp_file.name, audio_answer[1], audio_answer[0])
                                    audio_file_path = temp_file.name
                                    logger.info(f"📁 임시 파일 생성: {audio_file_path}")
                        elif isinstance(audio_answer, str):
                            # 파일 경로 문자열
                            audio_file_path = audio_answer
                            logger.info(f"📁 파일 경로: {audio_file_path}")
                        else:
                            logger.warning(f"⚠️  알 수 없는 오디오 형식: {type(audio_answer)}")
                    
                    # 음성 답변이 있으면 STT
                    if audio_file_path:
                        logger.info(f"🎤 음성 답변 → STT 변환 시작: {audio_file_path}")
                        try:
                            text_from_audio = simulator.speech_to_text(audio_file_path)
                            
                            if text_from_audio:
                                logger.info(f"✅ STT 성공: {text_from_audio[:50]}...")
                                answer = text_from_audio
                            else:
                                logger.warning("⚠️  STT 실패, 텍스트 답변 사용")
                                answer = text_answer
                        except Exception as e:
                            logger.error(f"❌ STT 오류: {e}")
                            import traceback
                            logger.debug(traceback.format_exc())
                            answer = text_answer
                    else:
                        logger.info("📝 텍스트 답변 사용")
                        answer = text_answer
                    
                    if not answer or len(answer.strip()) == 0:
                        logger.warning("⚠️  답변이 비어있음")
                        return {"error": "답변을 입력하거나 녹음해주세요"}
                    
                    logger.info(f"📊 최종 답변: {answer[:100]}... (총 {len(answer)} 글자)")
                    evaluation = simulator.evaluate_answer(question, answer, context)
                    return evaluation
                
                study_submit_btn.click(
                    evaluate_study_answer,
                    inputs=[current_question, current_context, study_answer_text, study_answer_audio],
                    outputs=study_evaluation_output
                )
            
            # ===== 면접 모드 탭 =====
            with gr.Tab("💼 면접 모드"):
                gr.Markdown("### 실전 면접처럼 연습하세요")
                
                with gr.Row():
                    with gr.Column():
                        interview_use_profile = gr.Checkbox(
                            label="내 프로필 기반 맞춤형 질문",
                            value=False
                        )
                        interview_focus = gr.Dropdown(
                            ["전체", "증착", "식각", "리소그래피", "이온주입", "CMP", "분석"],
                            label="중점 분야",
                            value="전체"
                        )
                        
                        interview_start_btn = gr.Button("▶️ 면접 시작", variant="primary")
                    
                    with gr.Column():
                        interview_question_output = gr.Textbox(label="질문", lines=5)
                        interview_audio_output = gr.Audio(
                            label="질문 음성 (자동 재생)",
                            type="filepath",
                            autoplay=True
                        )
                
                with gr.Row():
                    with gr.Column():
                        interview_answer_text = gr.Textbox(
                            label="텍스트 답변", 
                            lines=5, 
                            placeholder="답변을 입력하세요"
                        )
                    with gr.Column():
                        interview_answer_audio = gr.Audio(
                            label="🎤 음성 답변 녹음",
                            sources=["microphone"],
                            type="filepath"
                        )
                
                # 녹음된 음성 재생 섹션
                gr.Markdown("### 🔊 녹음된 답변 확인")
                interview_recorded_playback = gr.Audio(
                    label="녹음된 음성 재생",
                    type="filepath",
                    interactive=False
                )
                
                interview_submit_btn = gr.Button("✅ 답변 제출", variant="primary")
                interview_evaluation_output = gr.JSON(label="평가 결과")
                
                # 녹음 완료 시 자동으로 재생 컴포넌트에 복사
                def on_interview_audio_recorded(audio):
                    """녹음 완료 시 재생 컴포넌트 업데이트"""
                    if audio:
                        logger.info(f"🎤 면접 답변 녹음 완료: {audio}")
                        return audio
                    return None
                
                interview_answer_audio.change(
                    on_interview_audio_recorded,
                    inputs=[interview_answer_audio],
                    outputs=[interview_recorded_playback]
                )
                
                # PDF 리포트 생성 섹션
                gr.Markdown("---")
                gr.Markdown("### 📄 면접 결과 리포트")
                
                with gr.Row():
                    with gr.Column():
                        gr.Markdown(f"""
                        **저장된 Q&A**: {len(simulator.current_session_qa)}개
                        
                        면접이 끝나면 PDF 리포트를 다운로드하세요:
                        - 종합 평가 점수
                        - 질문별 상세 분석
                        - 강점 및 개선점
                        - 학습 가이드
                        """)
                        
                        user_name_input = gr.Textbox(
                            label="이름 (리포트에 표시)",
                            value="학생",
                            placeholder="홍길동"
                        )
                        
                        with gr.Row():
                            generate_pdf_btn = gr.Button("📥 PDF 리포트 생성", variant="secondary")
                            clear_session_btn = gr.Button("🔄 세션 초기화", variant="secondary")
                    
                    with gr.Column():
                        pdf_output = gr.File(label="생성된 PDF 리포트")
                        pdf_status = gr.Markdown()
                
                def start_interview(use_profile, focus):
                    question, context = simulator.generate_interview_question(use_profile, focus)
                    audio = simulator.text_to_speech(question)
                    return question, audio, question, context
                
                interview_start_btn.click(
                    start_interview,
                    inputs=[interview_use_profile, interview_focus],
                    outputs=[interview_question_output, interview_audio_output, current_question, current_context]
                )
                
                def evaluate_interview_answer(question, context, text_answer, audio_answer):
                    """면접 답변 평가 (텍스트 또는 음성)"""
                    logger.info(f"💼 면접 답변 평가 시작")
                    logger.info(f"   - 텍스트 답변 길이: {len(text_answer) if text_answer else 0}")
                    logger.info(f"   - 음성 데이터 타입: {type(audio_answer)}")
                    logger.info(f"   - 음성 데이터 값: {audio_answer}")
                    
                    # Gradio Audio 컴포넌트 처리
                    audio_file_path = None
                    if audio_answer:
                        if isinstance(audio_answer, tuple):
                            logger.info("📦 튜플 형태의 오디오 데이터")
                            if len(audio_answer) >= 2:
                                if isinstance(audio_answer[1], str):
                                    audio_file_path = audio_answer[1]
                                else:
                                    # NumPy 배열인 경우 임시 파일로 저장
                                    try:
                                        import tempfile
                                        import soundfile as sf
                                        
                                        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
                                        sf.write(temp_file.name, audio_answer[1], audio_answer[0])
                                        audio_file_path = temp_file.name
                                        logger.info(f"📁 임시 파일 생성: {audio_file_path}")
                                    except ImportError:
                                        logger.error("❌ soundfile 패키지 필요: pip install soundfile")
                                    except Exception as e:
                                        logger.error(f"❌ 오디오 저장 실패: {e}")
                        elif isinstance(audio_answer, str):
                            audio_file_path = audio_answer
                            logger.info(f"📁 파일 경로: {audio_file_path}")
                        else:
                            logger.warning(f"⚠️  알 수 없는 오디오 형식: {type(audio_answer)}")
                    
                    # 음성 답변이 있으면 STT
                    if audio_file_path:
                        logger.info(f"🎤 음성 답변 → STT 변환 시작: {audio_file_path}")
                        try:
                            text_from_audio = simulator.speech_to_text(audio_file_path)
                            
                            if text_from_audio:
                                logger.info(f"✅ STT 성공: {text_from_audio[:50]}...")
                                answer = text_from_audio
                            else:
                                logger.warning("⚠️  STT 실패, 텍스트 답변 사용")
                                answer = text_answer
                        except Exception as e:
                            logger.error(f"❌ STT 오류: {e}")
                            import traceback
                            logger.debug(traceback.format_exc())
                            answer = text_answer
                    else:
                        logger.info("📝 텍스트 답변 사용")
                        answer = text_answer
                    
                    if not answer or len(answer.strip()) == 0:
                        logger.warning("⚠️  답변이 비어있음")
                        return {"error": "답변을 입력하거나 녹음해주세요"}
                    
                    logger.info(f"📊 최종 답변 길이: {len(answer)} 글자")
                    evaluation = simulator.evaluate_answer(question, answer, context)
                    return evaluation
                
                interview_submit_btn.click(
                    evaluate_interview_answer,
                    inputs=[current_question, current_context, interview_answer_text, interview_answer_audio],
                    outputs=interview_evaluation_output
                )
                
                def generate_pdf_handler(user_name):
                    if not simulator.current_session_qa:
                        return None, "❌ 저장된 면접 데이터가 없습니다. 먼저 질문에 답변하세요."
                    
                    logger.info(f"📄 리포트 생성 시작: {len(simulator.current_session_qa)}개 Q&A")
                    pdf_path = simulator.generate_pdf_report(user_name or "학생")
                    
                    if pdf_path:
                        file_format = "PDF" if pdf_path.endswith('.pdf') else "HTML"
                        return pdf_path, f"✅ {file_format} 리포트가 생성되었습니다!\n\n**포함 내용:**\n- 총 {len(simulator.current_session_qa)}개 질문 분석\n- 종합 평가 및 피드백\n- 학습 가이드\n\n💡 {file_format} 파일을 다운로드하여 확인하세요!"
                    else:
                        return None, "❌ 리포트 생성 실패. 로그를 확인하세요."
                
                generate_pdf_btn.click(
                    generate_pdf_handler,
                    inputs=[user_name_input],
                    outputs=[pdf_output, pdf_status]
                )
                
                def clear_session_handler():
                    simulator.clear_session()
                    return f"🔄 세션이 초기화되었습니다. 새로운 면접을 시작하세요."
                
                clear_session_btn.click(
                    clear_session_handler,
                    outputs=[pdf_status]
                )
        
        gr.Markdown("""
        ---
        ### 💡 사용 팁
        - **음성 인식**: 마이크 버튼을 눌러 음성으로 답변하세요
        - **평가 기준**: 정확성(30) + 깊이(25) + 구조(20) + 응용(15) + 의사소통(10) = 100점
        - **맞춤형 질문**: 프로필을 먼저 설정하면 경험 기반 질문이 생성됩니다
        
        **문의**: 시스템 오류 시 .env 파일의 API 키를 확인하세요
        """)
    
    return demo


# ============================================
# 메인 실행
# ============================================

def main():
    """메인 함수"""
    
    try:
        # 시뮬레이터 초기화
        simulator = SemiconductorSimulator()
        
        # Gradio UI 생성
        demo = create_gradio_interface(simulator)
        
        # 서버 실행
        port = int(os.getenv('GRADIO_SERVER_PORT', 7860))
        server_name = os.getenv('GRADIO_SERVER_NAME', '0.0.0.0')
        share = os.getenv('GRADIO_SHARE', 'false').lower() == 'true'
        
        logger.info(f"""
        ╔══════════════════════════════════════════════════════════╗
        ║  🎓 반도체 공정 학습 & 면접 시뮬레이터 시작            ║
        ║                                                          ║
        ║  URL: http://localhost:{port}                     ║
        ║  환경: {os.getenv('ENVIRONMENT', 'local').upper()}                                              ║
        ╚══════════════════════════════════════════════════════════╝
        """)
        
        demo.launch(
            server_name=server_name,
            server_port=port,
            share=share
        )
    
    except Exception as e:
        logger.error(f"""
        ❌ 시스템 초기화 실패
        
        오류: {e}
        
        확인사항:
        1. .env 파일이 존재하는지 확인
        2. API 키가 올바르게 설정되었는지 확인
        3. 필요한 패키지가 설치되었는지 확인 (pip install -r requirements.txt)
        """)
        sys.exit(1)


if __name__ == "__main__":
    main()
