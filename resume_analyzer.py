"""
이력서 및 자기소개서 분석 시스템
학생의 경험, 프로젝트, 관심사를 분석하여 맞춤형 질문 생성
"""

import os
import json
import re
from typing import List, Dict, Optional
from openai import AzureOpenAI
import PyPDF2
from docx import Document


class ResumeAnalyzer:
    """이력서/자소서 분석 및 맞춤형 질문 생성"""
    
    def __init__(self):
        self.openai_client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_KEY"),
            api_version="2024-02-15-preview",
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        self.gpt_deployment = os.getenv("GPT_DEPLOYMENT_NAME", "gpt-4")
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """PDF에서 텍스트 추출"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text()
                return text
        except Exception as e:
            print(f"PDF 추출 오류: {e}")
            return ""
    
    def extract_text_from_docx(self, docx_path: str) -> str:
        """DOCX에서 텍스트 추출"""
        try:
            doc = Document(docx_path)
            text = "\n".join([para.text for para in doc.paragraphs])
            return text
        except Exception as e:
            print(f"DOCX 추출 오류: {e}")
            return ""
    
    def analyze_resume(self, resume_text: str) -> Dict:
        """
        이력서 분석 - 학력, 경험, 스킬, 프로젝트 추출
        """
        prompt = f"""
다음 이력서를 분석하여 학생의 배경 정보를 구조화하세요:

**이력서:**
{resume_text[:3000]}

**추출할 정보:**
1. 학력 (전공, 학년, 주요 수강 과목)
2. 반도체 관련 경험 (인턴, 프로젝트, 실험)
3. 기술 스킬 (장비, 소프트웨어, 분석 도구)
4. 관심 공정 분야
5. 특기사항 (수상, 논문, 자격증)

JSON 형식으로 반환:
{{
    "education": {{
        "major": "전공명",
        "year": "학년",
        "gpa": "학점 (있는 경우)",
        "relevant_courses": ["과목1", "과목2"]
    }},
    "semiconductor_experience": [
        {{
            "title": "경험/프로젝트명",
            "description": "설명",
            "duration": "기간",
            "processes_used": ["사용한 공정"],
            "achievements": ["성과"]
        }}
    ],
    "technical_skills": {{
        "equipment": ["장비1", "장비2"],
        "software": ["소프트웨어1", "소프트웨어2"],
        "analysis_tools": ["분석도구1", "분석도구2"]
    }},
    "interests": ["관심분야1", "관심분야2"],
    "achievements": ["수상/자격증1", "수상/자격증2"],
    "strengths": ["강점1", "강점2"],
    "areas_to_improve": ["개선필요영역1", "개선필요영역2"]
}}
"""
        
        try:
            response = self.openai_client.chat.completions.create(
                model=self.gpt_deployment,
                messages=[
                    {"role": "system", "content": "당신은 반도체 공학 커리어 컨설턴트입니다. 이력서를 면밀히 분석합니다."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
        
        except Exception as e:
            print(f"이력서 분석 오류: {e}")
            return {}
    
    def analyze_personal_statement(self, statement_text: str) -> Dict:
        """
        자기소개서 분석 - 동기, 목표, 가치관 추출
        """
        prompt = f"""
다음 자기소개서를 분석하여 학생의 내적 동기와 목표를 파악하세요:

**자기소개서:**
{statement_text[:3000]}

**추출할 정보:**
1. 반도체 공학 선택 동기
2. 커리어 목표 (단기/장기)
3. 연구 관심사
4. 문제 해결 경험
5. 협업/리더십 경험
6. 학습 태도 및 성장 마인드셋

JSON 형식으로 반환:
{{
    "motivation": "반도체 공학을 선택한 이유",
    "career_goals": {{
        "short_term": "단기 목표",
        "long_term": "장기 목표"
    }},
    "research_interests": ["관심분야1", "관심분야2"],
    "problem_solving_examples": [
        {{
            "situation": "상황",
            "action": "행동",
            "result": "결과"
        }}
    ],
    "teamwork_experience": "협업 경험 요약",
    "learning_attitude": "학습 태도 평가",
    "growth_mindset": "성장 마인드셋 평가",
    "passion_indicators": ["열정을 보여주는 요소"]
}}
"""
        
        try:
            response = self.openai_client.chat.completions.create(
                model=self.gpt_deployment,
                messages=[
                    {"role": "system", "content": "당신은 심리학과 커리어 개발 전문가입니다."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
        
        except Exception as e:
            print(f"자소서 분석 오류: {e}")
            return {}
    
    def generate_personalized_questions(
        self, 
        resume_data: Dict, 
        statement_data: Dict,
        num_questions: int = 15
    ) -> List[Dict]:
        """
        분석된 이력서/자소서 기반 맞춤형 질문 생성
        """
        prompt = f"""
다음 학생의 이력서와 자기소개서 분석 결과를 바탕으로 맞춤형 면접 질문을 생성하세요:

**이력서 분석:**
- 전공: {resume_data.get('education', {}).get('major', 'N/A')}
- 경험: {len(resume_data.get('semiconductor_experience', []))}개
- 기술: {', '.join(resume_data.get('technical_skills', {}).get('equipment', [])[:3])}
- 관심분야: {', '.join(resume_data.get('interests', []))}

**자기소개서 분석:**
- 동기: {statement_data.get('motivation', 'N/A')[:100]}
- 목표: {statement_data.get('career_goals', {}).get('short_term', 'N/A')}
- 연구 관심: {', '.join(statement_data.get('research_interests', []))}

**질문 생성 요구사항:**
총 {num_questions}개의 질문 생성:
1. 경험 기반 질문 (40%): 이력서의 프로젝트/경험을 깊이 파고드는 질문
2. 이론 확인 질문 (30%): 수강 과목과 관심 분야 이론 질문
3. 동기/태도 질문 (20%): 자소서의 동기와 목표 검증 질문
4. 문제 해결 질문 (10%): 실전 상황 대응 질문

**질문 원칙:**
- 학생의 실제 경험에 기반한 구체적 질문
- 관심 분야와 직접 연관된 질문
- 답변할 수 있는 수준의 질문 (학부생 수준)

JSON 배열로 반환:
[
  {{
    "question": "질문 내용",
    "question_type": "경험기반/이론/동기태도/문제해결",
    "category": "반도체 공정 카테고리",
    "difficulty": "기초/중급/고급",
    "personalization_reason": "왜 이 학생에게 이 질문이 적합한지",
    "expected_answer_points": ["평가포인트1", "평가포인트2"],
    "follow_up_questions": ["추가질문1", "추가질문2"]
  }}
]
"""
        
        try:
            response = self.openai_client.chat.completions.create(
                model=self.gpt_deployment,
                messages=[
                    {"role": "system", "content": "당신은 반도체 기업 면접관이자 교육자입니다. 학생의 잠재력을 평가하는 효과적인 질문을 만듭니다."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            questions = result if isinstance(result, list) else result.get('questions', [])
            
            # 메타데이터 추가
            for q in questions:
                q['personalized'] = True
                q['based_on'] = 'resume_and_statement'
            
            return questions
        
        except Exception as e:
            print(f"맞춤형 질문 생성 오류: {e}")
            return []
    
    def generate_experience_deep_dive_questions(
        self, 
        experience: Dict
    ) -> List[Dict]:
        """
        특정 경험/프로젝트에 대한 심층 질문 생성
        """
        prompt = f"""
다음 학생의 프로젝트 경험에 대한 심층 질문 5개를 생성하세요:

**프로젝트:**
- 제목: {experience.get('title', 'N/A')}
- 설명: {experience.get('description', 'N/A')}
- 사용 공정: {', '.join(experience.get('processes_used', []))}
- 성과: {', '.join(experience.get('achievements', []))}

**질문 유형:**
1. 기술적 세부사항 질문
2. 문제 해결 과정 질문
3. 의사결정 근거 질문
4. 개선 아이디어 질문
5. 학습 성과 질문

JSON 배열로 반환:
[
  {{
    "question": "구체적 질문",
    "focus": "기술/문제해결/의사결정/개선/학습",
    "evaluation_points": ["평가포인트1", "평가포인트2"]
  }}
]
"""
        
        try:
            response = self.openai_client.chat.completions.create(
                model=self.gpt_deployment,
                messages=[
                    {"role": "system", "content": "당신은 경험 기반 면접 전문가입니다."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return result if isinstance(result, list) else result.get('questions', [])
        
        except Exception as e:
            print(f"심층 질문 생성 오류: {e}")
            return []
    
    def create_student_profile(
        self,
        resume_path: Optional[str] = None,
        statement_path: Optional[str] = None,
        resume_text: Optional[str] = None,
        statement_text: Optional[str] = None
    ) -> Dict:
        """
        학생 프로필 생성 (종합 분석)
        """
        # 텍스트 추출
        if resume_path:
            ext = resume_path.lower().split('.')[-1]
            if ext == 'pdf':
                resume_text = self.extract_text_from_pdf(resume_path)
            elif ext == 'docx':
                resume_text = self.extract_text_from_docx(resume_path)
        
        if statement_path:
            ext = statement_path.lower().split('.')[-1]
            if ext == 'pdf':
                statement_text = self.extract_text_from_pdf(statement_path)
            elif ext == 'docx':
                statement_text = self.extract_text_from_docx(statement_path)
        
        # 분석
        resume_data = {}
        statement_data = {}
        
        if resume_text:
            resume_data = self.analyze_resume(resume_text)
        
        if statement_text:
            statement_data = self.analyze_personal_statement(statement_text)
        
        # 종합 프로필
        profile = {
            'resume_analysis': resume_data,
            'statement_analysis': statement_data,
            'created_at': __import__('datetime').datetime.now().isoformat()
        }
        
        # 요약
        profile['summary'] = self.create_profile_summary(resume_data, statement_data)
        
        return profile
    
    def create_profile_summary(self, resume_data: Dict, statement_data: Dict) -> str:
        """프로필 요약 생성"""
        summary_parts = []
        
        # 학력
        edu = resume_data.get('education', {})
        if edu:
            summary_parts.append(f"{edu.get('major', 'N/A')} {edu.get('year', '')}학년")
        
        # 경험
        exp_count = len(resume_data.get('semiconductor_experience', []))
        if exp_count > 0:
            summary_parts.append(f"반도체 관련 경험 {exp_count}건")
        
        # 관심 분야
        interests = resume_data.get('interests', [])
        if interests:
            summary_parts.append(f"관심: {', '.join(interests[:2])}")
        
        # 목표
        goal = statement_data.get('career_goals', {}).get('short_term', '')
        if goal:
            summary_parts.append(f"목표: {goal[:50]}")
        
        return " | ".join(summary_parts)


# 테스트 코드
if __name__ == "__main__":
    analyzer = ResumeAnalyzer()
    
    print("이력서/자소서 분석 시스템")
    print("\n사용 예시:")
    print("""
# 분석기 초기화
analyzer = ResumeAnalyzer()

# 학생 프로필 생성
profile = analyzer.create_student_profile(
    resume_path='student_resume.pdf',
    statement_path='personal_statement.docx'
)

# 맞춤형 질문 생성
questions = analyzer.generate_personalized_questions(
    resume_data=profile['resume_analysis'],
    statement_data=profile['statement_analysis'],
    num_questions=15
)

print(f"생성된 맞춤형 질문: {len(questions)}개")
    """)
