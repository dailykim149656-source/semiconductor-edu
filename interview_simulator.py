"""
Azure 기반 모의 면접 시뮬레이션 시스템
- Custom Voice로 면접관 음성
- RAG 기반 질문 생성
- 코드 실행 및 이미지 생성 기능
"""

import os
import json
import base64
from io import BytesIO
from typing import List, Dict, Tuple
import gradio as gr
import azure.cognitiveservices.speech as speechsdk
from openai import AzureOpenAI
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from azure.core.credentials import AzureKeyCredential
from PIL import Image
import requests
import numpy as np

class InterviewSimulator:
    def __init__(self):
        # Azure Speech Service 설정
        self.speech_key = os.getenv("AZURE_SPEECH_KEY")
        self.speech_region = os.getenv("AZURE_SPEECH_REGION")
        self.custom_voice_name = os.getenv("CUSTOM_VOICE_NAME")  # 예: "YourCustomVoice"
        
        # Azure OpenAI 설정
        self.openai_client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_KEY"),
            api_version="2024-02-15-preview",
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        self.gpt_deployment = os.getenv("GPT_DEPLOYMENT_NAME", "gpt-4")
        self.dalle_deployment = os.getenv("DALLE_DEPLOYMENT_NAME", "dall-e-3")
        
        # Azure AI Search 설정 (RAG)
        self.search_client = SearchClient(
            endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
            index_name=os.getenv("AZURE_SEARCH_INDEX", "interview-questions"),
            credential=AzureKeyCredential(os.getenv("AZURE_SEARCH_KEY"))
        )
        
        # 대화 히스토리
        self.conversation_history = []
        self.current_question_context = None
        
    def initialize_speech_config(self):
        """Speech 설정 초기화"""
        speech_config = speechsdk.SpeechConfig(
            subscription=self.speech_key,
            region=self.speech_region
        )
        # Custom Voice 설정
        speech_config.speech_synthesis_voice_name = self.custom_voice_name
        return speech_config
    
    def speech_to_text(self, audio_file) -> str:
        """음성을 텍스트로 변환 (STT)"""
        speech_config = speechsdk.SpeechConfig(
            subscription=self.speech_key,
            region=self.speech_region
        )
        speech_config.speech_recognition_language = "ko-KR"
        
        audio_config = speechsdk.audio.AudioConfig(filename=audio_file)
        speech_recognizer = speechsdk.SpeechRecognizer(
            speech_config=speech_config,
            audio_config=audio_config
        )
        
        result = speech_recognizer.recognize_once_async().get()
        
        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            return result.text
        else:
            return f"음성 인식 실패: {result.reason}"
    
    def text_to_speech(self, text: str, output_file: str = "output.wav"):
        """텍스트를 Custom Voice로 음성 변환 (TTS)"""
        speech_config = self.initialize_speech_config()
        audio_config = speechsdk.audio.AudioOutputConfig(filename=output_file)
        
        speech_synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=speech_config,
            audio_config=audio_config
        )
        
        # SSML을 사용하여 더 자연스러운 음성 생성
        ssml = f"""
        <speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='ko-KR'>
            <voice name='{self.custom_voice_name}'>
                <prosody rate='0.95' pitch='0%'>
                    {text}
                </prosody>
            </voice>
        </speak>
        """
        
        result = speech_synthesizer.speak_ssml_async(ssml).get()
        
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            return output_file
        else:
            print(f"TTS 실패: {result.reason}")
            return None
    
    def get_embedding(self, text: str) -> List[float]:
        """텍스트 임베딩 생성"""
        response = self.openai_client.embeddings.create(
            model="text-embedding-ada-002",
            input=text
        )
        return response.data[0].embedding
    
    def search_interview_questions(self, query: str, top_k: int = 3) -> List[Dict]:
        """RAG: 벡터 검색으로 관련 면접 질문 검색"""
        try:
            query_vector = self.get_embedding(query)
            vector_query = VectorizedQuery(
                vector=query_vector,
                k_nearest_neighbors=top_k,
                fields="contentVector"
            )
            
            results = self.search_client.search(
                search_text=query,
                vector_queries=[vector_query],
                select=["question", "category", "difficulty", "context", "sample_answer"],
                top=top_k
            )
            
            return [
                {
                    "question": doc["question"],
                    "category": doc.get("category", "일반"),
                    "difficulty": doc.get("difficulty", "중"),
                    "context": doc.get("context", ""),
                    "sample_answer": doc.get("sample_answer", "")
                }
                for doc in results
            ]
        except Exception as e:
            print(f"검색 오류: {e}")
            return []
    
    def generate_code_visualization(self, code_description: str) -> str:
        """코드 실행 및 시각화 생성"""
        prompt = f"""
다음 요구사항에 맞는 Python 코드를 작성하고 실행하여 시각화를 생성하세요:
{code_description}

matplotlib를 사용하여 그래프를 생성하고, 실행 가능한 코드만 반환하세요.
"""
        
        response = self.openai_client.chat.completions.create(
            model=self.gpt_deployment,
            messages=[
                {"role": "system", "content": "당신은 데이터 시각화 전문가입니다."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        
        return response.choices[0].message.content
    
    def generate_image(self, prompt: str) -> str:
        """DALL-E로 이미지 생성"""
        try:
            result = self.openai_client.images.generate(
                model=self.dalle_deployment,
                prompt=prompt,
                n=1,
                size="1024x1024"
            )
            
            image_url = result.data[0].url
            return image_url
        except Exception as e:
            print(f"이미지 생성 오류: {e}")
            return None
    
    def generate_interview_question(
        self, 
        user_profile: str, 
        difficulty: str = "중",
        use_visualization: bool = False
    ) -> Dict:
        """RAG 기반 면접 질문 생성"""
        # 1. RAG로 관련 질문 검색
        search_results = self.search_interview_questions(user_profile, top_k=3)
        
        # 2. 검색 결과를 컨텍스트로 활용
        context = "\n\n".join([
            f"참고 질문 {i+1}:\n"
            f"질문: {q['question']}\n"
            f"카테고리: {q['category']}\n"
            f"맥락: {q['context']}"
            for i, q in enumerate(search_results)
        ])
        
        # 3. GPT-4로 맞춤형 질문 생성
        system_prompt = f"""
당신은 전문 면접관입니다. 아래 검색된 질문들을 참고하여, 지원자에게 적합한 면접 질문을 생성하세요.

**중요**: 검색된 질문들의 맥락과 의도를 참고하되, 지원자의 프로필에 맞게 변형하거나 새로운 질문을 만들어야 합니다.
절대로 검색 결과를 그대로 출력하지 마세요. 할루시네이션을 피하기 위해 반드시 제공된 컨텍스트에 근거해야 합니다.

난이도: {difficulty}
시각자료 사용: {"예" if use_visualization else "아니오"}

검색된 참고 질문들:
{context}
"""
        
        user_prompt = f"""
지원자 프로필: {user_profile}

위 참고 질문들을 바탕으로 이 지원자에게 적합한 면접 질문을 생성하세요.

{"만약 시각자료가 필요한 질문이라면, 어떤 시각자료(차트, 이미지 등)가 필요한지 명시하세요." if use_visualization else ""}

JSON 형식으로 응답:
{{
    "question": "면접 질문",
    "category": "질문 카테고리",
    "rationale": "이 질문을 선택한 이유",
    "visualization_needed": true/false,
    "visualization_description": "필요한 시각자료 설명 (선택사항)"
}}
"""
        
        response = self.openai_client.chat.completions.create(
            model=self.gpt_deployment,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        question_data = json.loads(response.choices[0].message.content)
        
        # 4. 시각자료 생성 (필요한 경우)
        visualization_url = None
        if use_visualization and question_data.get("visualization_needed"):
            viz_desc = question_data.get("visualization_description", "")
            # 이미지 생성 또는 차트 생성
            if "차트" in viz_desc or "그래프" in viz_desc:
                # 코드 실행은 제한적이므로 이미지로 대체
                visualization_url = self.generate_image(
                    f"Professional business chart or graph: {viz_desc}"
                )
            else:
                visualization_url = self.generate_image(viz_desc)
        
        question_data["visualization_url"] = visualization_url
        question_data["search_context"] = search_results
        
        return question_data
    
    def evaluate_answer(self, question: str, answer: str, context: List[Dict]) -> Dict:
        """답변 평가"""
        # 참고 답변 컨텍스트 구성
        reference_answers = "\n\n".join([
            f"참고 답변 예시 {i+1}:\n{q['sample_answer']}"
            for i, q in enumerate(context) if q.get('sample_answer')
        ])
        
        prompt = f"""
면접 질문: {question}
지원자 답변: {answer}

참고 답변들:
{reference_answers}

위 참고 답변들을 기준으로 지원자의 답변을 평가하세요.

JSON 형식으로 응답:
{{
    "score": 0-100,
    "strengths": ["강점 1", "강점 2"],
    "weaknesses": ["개선점 1", "개선점 2"],
    "feedback": "구체적인 피드백",
    "suggested_answer": "더 나은 답변 예시"
}}
"""
        
        response = self.openai_client.chat.completions.create(
            model=self.gpt_deployment,
            messages=[
                {"role": "system", "content": "당신은 면접 평가 전문가입니다."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)


# Question Generator 임포트
from question_generator import QuestionGenerator

# Gradio 인터페이스 구성
def create_gradio_interface():
    simulator = InterviewSimulator()
    question_gen = QuestionGenerator()
    
    # 세션 상태 관리
    class SessionState:
        def __init__(self):
            self.current_question = None
            self.question_count = 0
            self.total_score = 0
            self.feedback_history = []
            self.question_requirements = None
            self.gen_conversation = []
    
    state = SessionState()
    
    def start_interview(profile, difficulty, use_viz):
        """면접 시작"""
        state.current_question = simulator.generate_interview_question(
            profile, difficulty, use_viz
        )
        state.question_count += 1
        
        question_text = state.current_question["question"]
        
        # TTS로 음성 생성
        audio_file = f"question_{state.question_count}.wav"
        simulator.text_to_speech(question_text, audio_file)
        
        # 시각자료가 있으면 표시
        viz_url = state.current_question.get("visualization_url")
        
        return (
            f"**질문 {state.question_count}** (카테고리: {state.current_question['category']})\n\n"
            f"{question_text}\n\n"
            f"*선택 이유: {state.current_question['rationale']}*",
            audio_file,
            viz_url if viz_url else None
        )
    
    def process_answer(audio_input, text_input):
        """답변 처리 및 평가"""
        # 음성 또는 텍스트 입력 처리
        if audio_input:
            answer_text = simulator.speech_to_text(audio_input)
        else:
            answer_text = text_input
        
        # 답변 평가
        evaluation = simulator.evaluate_answer(
            state.current_question["question"],
            answer_text,
            state.current_question["search_context"]
        )
        
        state.total_score += evaluation["score"]
        state.feedback_history.append(evaluation)
        
        # 피드백 음성 생성
        feedback_text = f"""
평가 점수: {evaluation['score']}점

강점: {', '.join(evaluation['strengths'])}

개선점: {', '.join(evaluation['weaknesses'])}

피드백: {evaluation['feedback']}
"""
        
        feedback_audio = f"feedback_{state.question_count}.wav"
        simulator.text_to_speech(feedback_text, feedback_audio)
        
        return (
            f"**답변:** {answer_text}\n\n"
            f"**평가 결과**\n\n"
            f"점수: **{evaluation['score']}/100**\n\n"
            f"**강점:**\n" + "\n".join([f"- {s}" for s in evaluation['strengths']]) + "\n\n"
            f"**개선점:**\n" + "\n".join([f"- {w}" for w in evaluation['weaknesses']]) + "\n\n"
            f"**피드백:**\n{evaluation['feedback']}\n\n"
            f"**제안 답변:**\n{evaluation['suggested_answer']}",
            feedback_audio,
            f"현재까지 평균 점수: {state.total_score / state.question_count:.1f}점"
        )
    
    # === 질문 생성 관련 함수 ===
    
    def chat_generate_questions(user_message, chat_history):
        """대화형 질문 생성"""
        result = question_gen.chat_for_requirements(user_message)
        
        bot_response = result['response']
        state.gen_conversation.append((user_message, bot_response))
        
        # 정보 수집 완료 여부 확인
        if result.get('is_complete'):
            state.question_requirements = result['collected_info']
            return (
                chat_history + [[user_message, bot_response]],
                "",
                True,  # 생성 버튼 활성화
                f"✅ 정보 수집 완료! 총 {result['collected_info'].get('question_count', 20)}개 질문을 생성합니다."
            )
        else:
            return (
                chat_history + [[user_message, bot_response]],
                "",
                False,  # 생성 버튼 비활성화
                "💬 대화를 계속하세요..."
            )
    
    def execute_question_generation():
        """실제 질문 생성 및 업로드"""
        if not state.question_requirements:
            return "❌ 먼저 대화를 통해 요구사항을 수집하세요.", ""
        
        try:
            # 질문 생성
            questions = question_gen.generate_questions(state.question_requirements)
            
            # 미리보기 텍스트 생성
            preview = f"### 생성된 질문 ({len(questions)}개)\n\n"
            for i, q in enumerate(questions[:5], 1):
                preview += f"**{i}. [{q['difficulty']}] {q['category']}**\n"
                preview += f"{q['question']}\n\n"
            
            if len(questions) > 5:
                preview += f"... 외 {len(questions) - 5}개 질문\n\n"
            
            # Azure AI Search에 업로드
            upload_result = question_gen.upload_to_search(questions)
            
            result_msg = (
                f"### ✅ 질문 생성 완료!\n\n"
                f"- 생성: {len(questions)}개\n"
                f"- 업로드 성공: {upload_result['success']}개\n"
                f"- 업로드 실패: {upload_result['failed']}개\n\n"
                f"이제 면접 시작 탭에서 생성된 질문을 사용할 수 있습니다!"
            )
            
            return result_msg, preview
            
        except Exception as e:
            return f"❌ 오류 발생: {str(e)}", ""
    
    def analyze_question_db():
        """질문 DB 현황 분석"""
        stats = question_gen.analyze_existing_questions()
        
        if 'error' in stats:
            return f"❌ 오류: {stats['error']}"
        
        analysis = f"### 📊 질문 DB 현황\n\n"
        analysis += f"**총 질문 수**: {stats['total_questions']}개\n\n"
        
        if stats.get('by_category'):
            analysis += "**카테고리별**:\n"
            for cat, count in stats['by_category'].items():
                analysis += f"- {cat}: {count}개\n"
            analysis += "\n"
        
        if stats.get('by_difficulty'):
            analysis += "**난이도별**:\n"
            for diff, count in stats['by_difficulty'].items():
                analysis += f"- {diff}: {count}개\n"
            analysis += "\n"
        
        if stats.get('by_position'):
            analysis += "**직무별**:\n"
            for pos, count in sorted(stats['by_position'].items(), key=lambda x: x[1], reverse=True)[:10]:
                if pos:
                    analysis += f"- {pos}: {count}개\n"
        
        return analysis
    
    def generate_from_job_description(jd_text, num_questions):
        """직무기술서 기반 질문 생성"""
        if not jd_text.strip():
            return "❌ 직무기술서를 입력하세요.", ""
        
        try:
            questions = question_gen.generate_from_document(jd_text, num_questions)
            
            # 미리보기
            preview = f"### 생성된 질문 ({len(questions)}개)\n\n"
            for i, q in enumerate(questions, 1):
                preview += f"**{i}. [{q.get('difficulty', '중')}] {q.get('category', '')}**\n"
                preview += f"{q['question']}\n"
                preview += f"*연관성: {q.get('document_relevance', 'N/A')}*\n\n"
            
            # 업로드
            upload_result = question_gen.upload_to_search(questions)
            
            result = (
                f"### ✅ 질문 생성 완료!\n\n"
                f"- 생성: {len(questions)}개\n"
                f"- 업로드 성공: {upload_result['success']}개\n"
            )
            
            return result, preview
            
        except Exception as e:
            return f"❌ 오류: {str(e)}", ""
    
    # Gradio UI 구성
    with gr.Blocks(title="AI 모의 면접 시뮬레이터", theme=gr.themes.Soft()) as demo:
        gr.Markdown("""
        # 🎤 AI 모의 면접 시뮬레이터
        ### Azure Custom Voice 기반 실전 면접 연습
        
        **특징:**
        - ✅ 당신의 목소리로 면접관 역할
        - ✅ RAG 기반 맞춤형 질문 (할루시네이션 방지)
        - ✅ 대화형 질문 자동 생성
        - ✅ 시각자료 제공 (차트, 이미지)
        - ✅ 실시간 답변 평가 및 피드백
        """)
        
        with gr.Tabs():
            # ===== 탭 1: 질문 자동 생성 =====
            with gr.Tab("🤖 질문 자동 생성"):
                gr.Markdown("""
                ## 대화형 질문 생성
                AI와 대화하면서 원하는 면접 질문을 자동으로 생성하고 DB에 추가합니다.
                """)
                
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("### 💬 AI와 대화하기")
                        gr.Markdown("""
                        **예시 시작 멘트:**
                        - "Python 백엔드 개발자 면접 질문 만들어줘"
                        - "5년차 데이터 사이언티스트 질문 생성해줘"
                        - "React 프론트엔드 신입 면접 준비 중이야"
                        """)
                        
                        gen_chatbot = gr.Chatbot(
                            label="AI 큐레이터",
                            height=400
                        )
                        gen_input = gr.Textbox(
                            label="메시지",
                            placeholder="어떤 면접 질문이 필요하신가요?",
                            lines=2
                        )
                        gen_send_btn = gr.Button("전송", variant="primary")
                        gen_status = gr.Textbox(
                            label="상태",
                            value="💬 대화를 시작하세요...",
                            interactive=False
                        )
                    
                    with gr.Column(scale=1):
                        gr.Markdown("### ⚙️ 생성 및 관리")
                        
                        gen_button = gr.Button(
                            "📝 질문 생성 시작",
                            variant="primary",
                            size="lg",
                            interactive=False
                        )
                        gen_result = gr.Markdown()
                        gen_preview = gr.Markdown(label="미리보기")
                        
                        gr.Markdown("---")
                        gr.Markdown("### 📊 질문 DB 현황")
                        analyze_btn = gr.Button("현황 분석")
                        analyze_result = gr.Markdown()
                
                # 이벤트 핸들러
                def send_and_update(msg, history):
                    return chat_generate_questions(msg, history)
                
                gen_send_btn.click(
                    fn=send_and_update,
                    inputs=[gen_input, gen_chatbot],
                    outputs=[gen_chatbot, gen_input, gen_button, gen_status]
                )
                
                gen_input.submit(
                    fn=send_and_update,
                    inputs=[gen_input, gen_chatbot],
                    outputs=[gen_chatbot, gen_input, gen_button, gen_status]
                )
                
                gen_button.click(
                    fn=execute_question_generation,
                    outputs=[gen_result, gen_preview]
                )
                
                analyze_btn.click(
                    fn=analyze_question_db,
                    outputs=[analyze_result]
                )
            
            # ===== 탭 2: 직무기술서 기반 생성 =====
            with gr.Tab("📄 직무기술서 분석"):
                gr.Markdown("""
                ## 직무기술서/공고 기반 질문 생성
                채용 공고나 직무기술서를 붙여넣으면 관련 면접 질문을 자동으로 생성합니다.
                """)
                
                with gr.Row():
                    with gr.Column():
                        jd_input = gr.Textbox(
                            label="직무기술서 / 채용공고",
                            placeholder="직무기술서나 채용공고 내용을 붙여넣으세요...",
                            lines=15
                        )
                        jd_num = gr.Slider(
                            minimum=5,
                            maximum=30,
                            value=15,
                            step=1,
                            label="생성할 질문 개수"
                        )
                        jd_btn = gr.Button("질문 생성", variant="primary")
                    
                    with gr.Column():
                        jd_result = gr.Markdown()
                        jd_preview = gr.Markdown()
                
                jd_btn.click(
                    fn=generate_from_job_description,
                    inputs=[jd_input, jd_num],
                    outputs=[jd_result, jd_preview]
                )
            
            # ===== 탭 3: 면접 시작 =====
            with gr.Tab("🎯 면접 시작"):
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("### 📋 면접 설정")
                        profile_input = gr.Textbox(
                            label="지원자 프로필",
                            placeholder="예: 3년차 백엔드 개발자, Python/Django 전문, AWS 경험",
                            lines=3
                        )
                        difficulty_select = gr.Radio(
                            choices=["하", "중", "상"],
                            label="난이도",
                            value="중"
                        )
                        use_visualization = gr.Checkbox(
                            label="시각자료 활용",
                            value=True
                        )
                        start_btn = gr.Button("면접 시작 🚀", variant="primary")
                    
                    with gr.Column(scale=2):
                        gr.Markdown("### 💬 면접 진행")
                        question_display = gr.Markdown()
                        question_audio = gr.Audio(label="면접관 음성 (Custom Voice)")
                        question_image = gr.Image(label="시각자료")
                
                gr.Markdown("---")
                
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("### 🎙️ 답변하기")
                        answer_audio = gr.Audio(
                            sources=["microphone"],
                            type="filepath",
                            label="음성으로 답변"
                        )
                        gr.Markdown("**또는**")
                        answer_text = gr.Textbox(
                            label="텍스트로 답변",
                            placeholder="답변을 입력하세요...",
                            lines=5
                        )
                        submit_btn = gr.Button("답변 제출", variant="primary")
                    
                    with gr.Column():
                        gr.Markdown("### 📊 평가 결과")
                        evaluation_display = gr.Markdown()
                        feedback_audio = gr.Audio(label="피드백 음성")
                        score_display = gr.Textbox(label="누적 점수", interactive=False)
                
                # 이벤트 핸들러
                start_btn.click(
                    fn=start_interview,
                    inputs=[profile_input, difficulty_select, use_visualization],
                    outputs=[question_display, question_audio, question_image]
                )
                
                submit_btn.click(
                    fn=process_answer,
                    inputs=[answer_audio, answer_text],
                    outputs=[evaluation_display, feedback_audio, score_display]
                )
    
    return demo


if __name__ == "__main__":
    demo = create_gradio_interface()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=True
    )
