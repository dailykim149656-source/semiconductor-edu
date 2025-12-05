"""
반도체 공정 학습 & 면접 시뮬레이터
학부생을 위한 맞춤형 학습 및 면접 준비 플랫폼
"""

import os
import json
from typing import List, Dict, Optional
import gradio as gr
import azure.cognitiveservices.speech as speechsdk
from openai import AzureOpenAI
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from azure.core.credentials import AzureKeyCredential

from document_processor import SemiconductorDocumentProcessor
from resume_analyzer import ResumeAnalyzer


class SemiconductorSimulator:
    """반도체 공정 학습/면접 시뮬레이터"""
    
    def __init__(self):
        # Azure Speech Service
        self.speech_key = os.getenv("AZURE_SPEECH_KEY")
        self.speech_region = os.getenv("AZURE_SPEECH_REGION")
        self.custom_voice_name = os.getenv("CUSTOM_VOICE_NAME")
        
        # Azure OpenAI
        self.openai_client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_KEY"),
            api_version="2024-02-15-preview",
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        self.gpt_deployment = os.getenv("GPT_DEPLOYMENT_NAME", "gpt-4")
        self.dalle_deployment = os.getenv("DALLE_DEPLOYMENT_NAME", "dall-e-3")
        
        # Azure AI Search
        self.search_client = SearchClient(
            endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
            index_name="semiconductor-knowledge",
            credential=AzureKeyCredential(os.getenv("AZURE_SEARCH_KEY"))
        )
        
        # 보조 도구
        self.doc_processor = SemiconductorDocumentProcessor()
        self.resume_analyzer = ResumeAnalyzer()
        
        # 세션 데이터
        self.student_profile = None
        self.conversation_history = []
        self.current_question = None
        self.score_history = []
    
    def text_to_speech(self, text: str, output_file: str = "output.wav"):
        """Custom Voice TTS"""
        speech_config = speechsdk.SpeechConfig(
            subscription=self.speech_key,
            region=self.speech_region
        )
        speech_config.speech_synthesis_voice_name = self.custom_voice_name
        
        audio_config = speechsdk.audio.AudioOutputConfig(filename=output_file)
        synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=speech_config,
            audio_config=audio_config
        )
        
        ssml = f"""
        <speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='ko-KR'>
            <voice name='{self.custom_voice_name}'>
                <prosody rate='0.9' pitch='0%'>
                    {text}
                </prosody>
            </voice>
        </speak>
        """
        
        result = synthesizer.speak_ssml_async(ssml).get()
        
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            return output_file
        return None
    
    def speech_to_text(self, audio_file: str) -> str:
        """음성을 텍스트로 변환"""
        speech_config = speechsdk.SpeechConfig(
            subscription=self.speech_key,
            region=self.speech_region
        )
        speech_config.speech_recognition_language = "ko-KR"
        
        audio_config = speechsdk.audio.AudioConfig(filename=audio_file)
        recognizer = speechsdk.SpeechRecognizer(
            speech_config=speech_config,
            audio_config=audio_config
        )
        
        result = recognizer.recognize_once_async().get()
        
        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            return result.text
        return "음성 인식 실패"
    
    def get_embedding(self, text: str) -> List[float]:
        """텍스트 임베딩 생성"""
        response = self.openai_client.embeddings.create(
            model="text-embedding-ada-002",
            input=text
        )
        return response.data[0].embedding
    
    def search_knowledge(
        self, 
        query: str, 
        process_filter: Optional[str] = None,
        difficulty_filter: Optional[str] = None,
        top_k: int = 5
    ) -> List[Dict]:
        """반도체 지식 검색"""
        try:
            query_vector = self.get_embedding(query)
            vector_query = VectorizedQuery(
                vector=query_vector,
                k_nearest_neighbors=top_k,
                fields="contentVector"
            )
            
            # 필터 구성
            filter_expr = []
            if process_filter:
                filter_expr.append(f"process_category eq '{process_filter}'")
            if difficulty_filter:
                filter_expr.append(f"difficulty eq '{difficulty_filter}'")
            
            filter_str = " and ".join(filter_expr) if filter_expr else None
            
            results = self.search_client.search(
                search_text=query,
                vector_queries=[vector_query],
                filter=filter_str,
                select=["question", "answer", "process_category", "difficulty", "theory", "keywords"],
                top=top_k
            )
            
            return [
                {
                    "question": doc["question"],
                    "answer": doc.get("answer", ""),
                    "process_category": doc.get("process_category", ""),
                    "difficulty": doc.get("difficulty", ""),
                    "theory": doc.get("theory", ""),
                    "keywords": doc.get("keywords", [])
                }
                for doc in results
            ]
        except Exception as e:
            print(f"검색 오류: {e}")
            return []
    
    def generate_study_question(
        self,
        topic: str,
        difficulty: str = "중급",
        question_type: str = "개념이해"
    ) -> Dict:
        """학습 모드 - 주제 기반 질문 생성"""
        # RAG 검색
        search_results = self.search_knowledge(
            query=topic,
            difficulty_filter=difficulty,
            top_k=3
        )
        
        context = "\n\n".join([
            f"참고 질문 {i+1}:\n{q['question']}\n답변: {q['answer']}"
            for i, q in enumerate(search_results)
        ])
        
        prompt = f"""
반도체 공정 학습용 질문을 생성하세요.

**주제**: {topic}
**난이도**: {difficulty}
**질문 유형**: {question_type}

**참고 자료**:
{context}

**요구사항**:
- 학부생 수준에 적합한 질문
- 이론과 실무를 연결하는 질문
- 명확한 평가 기준

JSON 형식:
{{
    "question": "질문",
    "hint": "힌트 (선택적)",
    "model_answer": "모범 답변",
    "evaluation_criteria": ["평가기준1", "평가기준2"],
    "related_concepts": ["관련개념1", "관련개념2"],
    "difficulty_explanation": "왜 이 난이도인지"
}}
"""
        
        response = self.openai_client.chat.completions.create(
            model=self.gpt_deployment,
            messages=[
                {"role": "system", "content": "당신은 반도체 공학 교수입니다."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        question_data = json.loads(response.choices[0].message.content)
        question_data['search_context'] = search_results
        
        return question_data
    
    def generate_interview_question(
        self,
        student_profile: Optional[Dict] = None,
        focus_area: Optional[str] = None
    ) -> Dict:
        """면접 모드 - 맞춤형 질문 생성"""
        if student_profile:
            # 개인 맞춤형 질문
            resume_data = student_profile.get('resume_analysis', {})
            statement_data = student_profile.get('statement_analysis', {})
            
            # 관심 분야 기반 검색
            interests = resume_data.get('interests', [])
            search_query = focus_area or (interests[0] if interests else "반도체 공정")
            
            search_results = self.search_knowledge(search_query, top_k=3)
            
            context = f"""
**학생 정보**:
- 전공: {resume_data.get('education', {}).get('major', 'N/A')}
- 경험: {len(resume_data.get('semiconductor_experience', []))}건
- 관심분야: {', '.join(interests)}
- 목표: {statement_data.get('career_goals', {}).get('short_term', 'N/A')}

**검색된 관련 질문**:
{chr(10).join([f"{i+1}. {q['question']}" for i, q in enumerate(search_results)])}
"""
            
            prompt = f"""
다음 학생에게 적합한 면접 질문을 생성하세요:

{context}

**요구사항**:
- 학생의 경험/관심사와 연결
- 학부생 수준에 적합
- 구체적이고 평가 가능한 질문

JSON 형식:
{{
    "question": "면접 질문",
    "category": "공정 카테고리",
    "personalization_reason": "이 학생에게 왜 적합한지",
    "expected_points": ["기대답변1", "기대답변2"],
    "follow_ups": ["추가질문1", "추가질문2"]
}}
"""
        else:
            # 일반 질문
            search_results = self.search_knowledge(
                focus_area or "반도체 공정",
                top_k=3
            )
            
            prompt = f"""
반도체 기업 면접 질문을 생성하세요.

참고 질문:
{chr(10).join([f"{i+1}. {q['question']}" for i, q in enumerate(search_results)])}

JSON 형식:
{{
    "question": "질문",
    "category": "카테고리",
    "model_answer": "모범답변",
    "evaluation_points": ["평가1", "평가2"]
}}
"""
        
        response = self.openai_client.chat.completions.create(
            model=self.gpt_deployment,
            messages=[
                {"role": "system", "content": "당신은 반도체 기업 면접관입니다."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        question_data = json.loads(response.choices[0].message.content)
        question_data['search_context'] = search_results
        
        return question_data
    
    def evaluate_answer(
        self,
        question: str,
        student_answer: str,
        model_answer: str,
        context: List[Dict]
    ) -> Dict:
        """답변 평가"""
        reference_context = "\n".join([
            f"참고 답변: {c.get('answer', '')}"
            for c in context
        ])
        
        prompt = f"""
학생의 답변을 평가하세요.

**질문**: {question}

**학생 답변**: {student_answer}

**모범 답변**: {model_answer}

**참고 자료**:
{reference_context}

**평가 기준**:
1. 정확성 (30점): 기술적으로 정확한가?
2. 깊이 (25점): 원리를 이해하고 있는가?
3. 구조 (20점): 논리적으로 설명하는가?
4. 응용 (15점): 실무/실습과 연결하는가?
5. 의사소통 (10점): 명확하게 전달하는가?

JSON 형식:
{{
    "total_score": 0-100,
    "breakdown": {{
        "accuracy": 0-30,
        "depth": 0-25,
        "structure": 0-20,
        "application": 0-15,
        "communication": 0-10
    }},
    "strengths": ["강점1", "강점2"],
    "improvements": ["개선점1", "개선점2"],
    "feedback": "상세 피드백 (3-4문장)",
    "recommended_review": ["복습할 개념1", "복습할 개념2"]
}}
"""
        
        response = self.openai_client.chat.completions.create(
            model=self.gpt_deployment,
            messages=[
                {"role": "system", "content": "당신은 반도체 공학 교수이자 평가 전문가입니다."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
    
    def generate_process_diagram(self, process_name: str) -> Optional[str]:
        """공정 다이어그램 생성 (DALL-E)"""
        try:
            prompt = f"Technical diagram of {process_name} semiconductor fabrication process, cross-section view, labeled, educational style, clean and professional"
            
            result = self.openai_client.images.create(
                model=self.dalle_deployment,
                prompt=prompt,
                n=1,
                size="1024x1024"
            )
            
            return result.data[0].url
        except Exception as e:
            print(f"이미지 생성 오류: {e}")
            return None


def create_gradio_interface():
    """Gradio UI 구성"""
    simulator = SemiconductorSimulator()
    
    # 세션 상태
    class SessionState:
        def __init__(self):
            self.student_profile = None
            self.current_question = None
            self.question_count = 0
            self.score_history = []
            self.mode = "study"  # study or interview
    
    state = SessionState()
    
    # === 함수 정의 ===
    
    def upload_and_analyze_documents(resume_file, statement_file):
        """이력서/자소서 업로드 및 분석"""
        if not resume_file and not statement_file:
            return "❌ 최소 하나의 파일을 업로드하세요.", ""
        
        try:
            profile = simulator.resume_analyzer.create_student_profile(
                resume_path=resume_file.name if resume_file else None,
                statement_path=statement_file.name if statement_file else None
            )
            
            state.student_profile = profile
            
            # 프로필 요약
            summary = f"### ✅ 프로필 분석 완료\n\n"
            summary += f"**요약**: {profile['summary']}\n\n"
            
            resume_data = profile.get('resume_analysis', {})
            if resume_data:
                summary += "**학력**:\n"
                edu = resume_data.get('education', {})
                summary += f"- {edu.get('major', 'N/A')} {edu.get('year', '')}학년\n\n"
                
                summary += "**반도체 경험**:\n"
                for exp in resume_data.get('semiconductor_experience', [])[:3]:
                    summary += f"- {exp.get('title', 'N/A')}\n"
                summary += "\n"
                
                summary += f"**관심 분야**: {', '.join(resume_data.get('interests', []))}\n\n"
            
            statement_data = profile.get('statement_analysis', {})
            if statement_data:
                summary += f"**커리어 목표**: {statement_data.get('career_goals', {}).get('short_term', 'N/A')}\n\n"
            
            return summary, "✅ 맞춤형 질문을 생성할 준비가 되었습니다!"
        
        except Exception as e:
            return f"❌ 오류: {str(e)}", ""
    
    def start_study_mode(topic, difficulty, question_type):
        """학습 모드 시작"""
        state.mode = "study"
        state.question_count += 1
        
        question_data = simulator.generate_study_question(
            topic=topic,
            difficulty=difficulty,
            question_type=question_type
        )
        
        state.current_question = question_data
        
        # TTS
        audio_file = f"study_q_{state.question_count}.wav"
        simulator.text_to_speech(question_data['question'], audio_file)
        
        # 화면 표시
        display = f"### 📚 학습 질문 {state.question_count}\n\n"
        display += f"**주제**: {topic}\n"
        display += f"**난이도**: {difficulty}\n"
        display += f"**유형**: {question_type}\n\n"
        display += f"**질문**: {question_data['question']}\n\n"
        
        if question_data.get('hint'):
            display += f"💡 *힌트*: {question_data['hint']}\n"
        
        return display, audio_file
    
    def start_interview_mode(focus_area, use_profile):
        """면접 모드 시작"""
        state.mode = "interview"
        state.question_count += 1
        
        profile = state.student_profile if use_profile else None
        
        question_data = simulator.generate_interview_question(
            student_profile=profile,
            focus_area=focus_area
        )
        
        state.current_question = question_data
        
        # TTS
        audio_file = f"interview_q_{state.question_count}.wav"
        simulator.text_to_speech(question_data['question'], audio_file)
        
        # 화면 표시
        display = f"### 🎯 면접 질문 {state.question_count}\n\n"
        display += f"**카테고리**: {question_data.get('category', 'N/A')}\n\n"
        display += f"**질문**: {question_data['question']}\n\n"
        
        if question_data.get('personalization_reason'):
            display += f"*📌 맞춤 이유*: {question_data['personalization_reason']}\n"
        
        return display, audio_file
    
    def submit_answer(audio_input, text_input):
        """답변 제출 및 평가"""
        # 답변 추출
        if audio_input:
            answer = simulator.speech_to_text(audio_input)
        else:
            answer = text_input
        
        if not answer or answer.strip() == "":
            return "❌ 답변을 입력하세요.", None, ""
        
        # 평가
        model_answer = state.current_question.get('model_answer', state.current_question.get('expected_points', [''])[0])
        
        evaluation = simulator.evaluate_answer(
            question=state.current_question['question'],
            student_answer=answer,
            model_answer=model_answer,
            context=state.current_question.get('search_context', [])
        )
        
        state.score_history.append(evaluation['total_score'])
        
        # 피드백 TTS
        feedback_text = f"점수: {evaluation['total_score']}점. {evaluation['feedback']}"
        feedback_audio = f"feedback_{state.question_count}.wav"
        simulator.text_to_speech(feedback_text, feedback_audio)
        
        # 화면 표시
        result = f"### 📊 평가 결과\n\n"
        result += f"**총점**: {evaluation['total_score']}/100\n\n"
        
        result += "**세부 점수**:\n"
        breakdown = evaluation.get('breakdown', {})
        result += f"- 정확성: {breakdown.get('accuracy', 0)}/30\n"
        result += f"- 깊이: {breakdown.get('depth', 0)}/25\n"
        result += f"- 구조: {breakdown.get('structure', 0)}/20\n"
        result += f"- 응용: {breakdown.get('application', 0)}/15\n"
        result += f"- 의사소통: {breakdown.get('communication', 0)}/10\n\n"
        
        result += f"**강점**: {', '.join(evaluation.get('strengths', []))}\n\n"
        result += f"**개선점**: {', '.join(evaluation.get('improvements', []))}\n\n"
        result += f"**피드백**: {evaluation['feedback']}\n\n"
        
        if evaluation.get('recommended_review'):
            result += f"**복습 추천**: {', '.join(evaluation['recommended_review'])}\n"
        
        avg_score = sum(state.score_history) / len(state.score_history) if state.score_history else 0
        stats = f"평균 점수: {avg_score:.1f} | 총 {len(state.score_history)}문제"
        
        return result, feedback_audio, stats
    
    def upload_course_materials(files):
        """수업자료 업로드 및 처리"""
        if not files:
            return "❌ 파일을 업로드하세요."
        
        try:
            file_paths = [f.name for f in files]
            result = simulator.doc_processor.process_course_materials(file_paths)
            
            summary = f"### ✅ 수업자료 처리 완료\n\n"
            summary += f"- 파일: {result['files_processed']}개\n"
            summary += f"- 추출된 청크: {result['chunks_extracted']}개\n"
            summary += f"- 지식 항목: {result['knowledge_items']}개\n"
            summary += f"- 생성된 질문: {result['questions_generated']}개\n"
            summary += f"- 업로드 성공: {result['upload_result']['success']}개\n\n"
            summary += "이제 생성된 질문을 학습/면접 모드에서 사용할 수 있습니다!"
            
            return summary
        
        except Exception as e:
            return f"❌ 오류: {str(e)}"
    
    # === Gradio UI ===
    
    with gr.Blocks(title="반도체 공정 학습 & 면접 시뮬레이터", theme=gr.themes.Soft()) as demo:
        gr.Markdown("""
        # ⚡ 반도체 공정 학습 & 면접 시뮬레이터
        ### 학부생을 위한 맞춤형 학습 및 면접 준비 플랫폼
        
        **주요 기능**:
        - 📚 수업자료 기반 RAG 학습 시스템
        - 🎯 이력서/자소서 분석을 통한 맞춤형 면접
        - 🔊 Custom Voice로 실감나는 시뮬레이션
        - 📊 상세한 답변 평가 및 피드백
        """)
        
        with gr.Tabs():
            # === 탭 1: 프로필 설정 ===
            with gr.Tab("👤 프로필 설정"):
                gr.Markdown("""
                ## 개인 맞춤형 학습을 위한 프로필 설정
                이력서와 자기소개서를 업로드하면 맞춤형 질문을 생성합니다.
                """)
                
                with gr.Row():
                    resume_upload = gr.File(
                        label="이력서 (PDF/DOCX)",
                        file_types=[".pdf", ".docx"]
                    )
                    statement_upload = gr.File(
                        label="자기소개서 (PDF/DOCX)",
                        file_types=[".pdf", ".docx"]
                    )
                
                analyze_btn = gr.Button("분석 시작", variant="primary", size="lg")
                
                profile_result = gr.Markdown()
                profile_status = gr.Textbox(label="상태", interactive=False)
                
                analyze_btn.click(
                    fn=upload_and_analyze_documents,
                    inputs=[resume_upload, statement_upload],
                    outputs=[profile_result, profile_status]
                )
            
            # === 탭 2: 수업자료 업로드 ===
            with gr.Tab("📖 수업자료 관리"):
                gr.Markdown("""
                ## 수업자료 업로드
                PDF, PPT, DOCX 형식의 수업자료를 업로드하면 자동으로 지식을 추출하여 RAG DB를 구축합니다.
                """)
                
                course_files = gr.File(
                    label="수업자료 파일 (여러 개 가능)",
                    file_count="multiple",
                    file_types=[".pdf", ".pptx", ".docx"]
                )
                
                process_btn = gr.Button("자료 처리 시작", variant="primary")
                process_result = gr.Markdown()
                
                process_btn.click(
                    fn=upload_course_materials,
                    inputs=[course_files],
                    outputs=[process_result]
                )
            
            # === 탭 3: 학습 모드 ===
            with gr.Tab("📚 학습 모드"):
                gr.Markdown("""
                ## 개념 학습 및 이론 복습
                주제를 선택하고 난이도별 학습 질문을 풀어보세요.
                """)
                
                with gr.Row():
                    with gr.Column():
                        study_topic = gr.Textbox(
                            label="학습 주제",
                            placeholder="예: CVD 증착 공정, 플라즈마 식각, 포토리소그래피",
                            value="CVD 증착"
                        )
                        study_difficulty = gr.Radio(
                            choices=["기초", "중급", "고급"],
                            label="난이도",
                            value="중급"
                        )
                        study_type = gr.Radio(
                            choices=["개념이해", "원리설명", "응용", "비교", "실무"],
                            label="질문 유형",
                            value="개념이해"
                        )
                        study_start_btn = gr.Button("질문 받기 📝", variant="primary")
                    
                    with gr.Column():
                        study_question = gr.Markdown()
                        study_audio = gr.Audio(label="질문 음성")
                
                gr.Markdown("---")
                
                with gr.Row():
                    with gr.Column():
                        study_answer_audio = gr.Audio(
                            sources=["microphone"],
                            type="filepath",
                            label="음성 답변"
                        )
                        study_answer_text = gr.Textbox(
                            label="텍스트 답변",
                            lines=5,
                            placeholder="답변을 입력하세요..."
                        )
                        study_submit_btn = gr.Button("답변 제출", variant="primary")
                    
                    with gr.Column():
                        study_evaluation = gr.Markdown()
                        study_feedback_audio = gr.Audio(label="피드백 음성")
                        study_stats = gr.Textbox(label="학습 통계", interactive=False)
                
                study_start_btn.click(
                    fn=start_study_mode,
                    inputs=[study_topic, study_difficulty, study_type],
                    outputs=[study_question, study_audio]
                )
                
                study_submit_btn.click(
                    fn=submit_answer,
                    inputs=[study_answer_audio, study_answer_text],
                    outputs=[study_evaluation, study_feedback_audio, study_stats]
                )
            
            # === 탭 4: 면접 모드 ===
            with gr.Tab("🎯 면접 모드"):
                gr.Markdown("""
                ## 실전 면접 시뮬레이션
                반도체 기업 면접을 대비한 실전 연습
                """)
                
                with gr.Row():
                    with gr.Column():
                        interview_focus = gr.Textbox(
                            label="중점 분야 (선택사항)",
                            placeholder="예: 증착 공정, 박막 분석, 공정 최적화",
                            value=""
                        )
                        interview_use_profile = gr.Checkbox(
                            label="내 프로필 기반 맞춤형 질문",
                            value=True
                        )
                        interview_start_btn = gr.Button("면접 시작 🚀", variant="primary")
                    
                    with gr.Column():
                        interview_question = gr.Markdown()
                        interview_audio = gr.Audio(label="면접관 음성 (Custom Voice)")
                
                gr.Markdown("---")
                
                with gr.Row():
                    with gr.Column():
                        interview_answer_audio = gr.Audio(
                            sources=["microphone"],
                            type="filepath",
                            label="음성 답변"
                        )
                        interview_answer_text = gr.Textbox(
                            label="텍스트 답변",
                            lines=5
                        )
                        interview_submit_btn = gr.Button("답변 제출", variant="primary")
                    
                    with gr.Column():
                        interview_evaluation = gr.Markdown()
                        interview_feedback_audio = gr.Audio(label="피드백 음성")
                        interview_stats = gr.Textbox(label="면접 통계", interactive=False)
                
                interview_start_btn.click(
                    fn=start_interview_mode,
                    inputs=[interview_focus, interview_use_profile],
                    outputs=[interview_question, interview_audio]
                )
                
                interview_submit_btn.click(
                    fn=submit_answer,
                    inputs=[interview_answer_audio, interview_answer_text],
                    outputs=[interview_evaluation, interview_feedback_audio, interview_stats]
                )
    
    return demo


if __name__ == "__main__":
    demo = create_gradio_interface()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )
