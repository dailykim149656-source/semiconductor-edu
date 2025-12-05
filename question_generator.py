"""
대화형 질문 자동 생성 시스템
사용자와 대화하면서 면접 질문을 자동으로 생성하고 RAG DB에 추가
"""

import os
import json
from typing import List, Dict, Optional
from openai import AzureOpenAI
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential


class QuestionGenerator:
    """대화형 면접 질문 자동 생성기"""
    
    def __init__(self):
        # Azure OpenAI 설정
        self.openai_client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_KEY"),
            api_version="2024-02-15-preview",
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        self.gpt_deployment = os.getenv("GPT_DEPLOYMENT_NAME", "gpt-4")
        
        # Azure AI Search 설정
        self.search_client = SearchClient(
            endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
            index_name=os.getenv("AZURE_SEARCH_INDEX", "interview-questions"),
            credential=AzureKeyCredential(os.getenv("AZURE_SEARCH_KEY"))
        )
        
        self.conversation_history = []
    
    def chat_for_requirements(self, user_message: str) -> Dict:
        """
        사용자와 대화하면서 질문 생성 요구사항 수집
        
        Returns:
            {
                'response': '사용자에게 보여줄 응답',
                'is_complete': 충분한 정보를 수집했는지,
                'requirements': 수집된 요구사항 딕셔너리
            }
        """
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        system_prompt = """
당신은 면접 질문 큐레이터입니다. 사용자와 대화하면서 다음 정보를 수집하세요:

1. **직무/분야**: 어떤 직무의 면접인가? (예: 백엔드 개발자, 데이터 사이언티스트, PM)
2. **경력 수준**: 신입, 주니어(1-3년), 미드(3-7년), 시니어(7년+)
3. **기술 스택/도메인**: 특정 기술이나 도메인 (예: Python/Django, React, 금융권)
4. **질문 개수**: 몇 개의 질문이 필요한가? (기본 20개)
5. **난이도 분포**: 쉬움/중간/어려움 비율 (기본 3:5:2)
6. **중점 평가 영역**: 기술역량, 소프트스킬, 문제해결, 리더십 등

**대화 전략**:
- 자연스럽게 필요한 정보를 물어보세요
- 이미 제공된 정보는 다시 묻지 마세요
- 모든 정보가 수집되면 요약하고 확인을 요청하세요

**응답 형식** (JSON):
{
    "response": "사용자에게 보낼 친근한 메시지",
    "is_complete": true/false,
    "collected_info": {
        "position": "직무명 또는 null",
        "experience_level": "경력수준 또는 null",
        "tech_stack": "기술스택 또는 null",
        "question_count": 숫자 또는 null,
        "difficulty_ratio": {"easy": 3, "medium": 5, "hard": 2} 또는 null,
        "focus_areas": ["영역1", "영역2"] 또는 null
    },
    "next_question": "다음에 물어볼 것 (is_complete가 false일 때)"
}
"""
        
        response = self.openai_client.chat.completions.create(
            model=self.gpt_deployment,
            messages=[
                {"role": "system", "content": system_prompt},
                *self.conversation_history
            ],
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        
        self.conversation_history.append({
            "role": "assistant",
            "content": response.choices[0].message.content
        })
        
        return result
    
    def generate_questions(self, requirements: Dict) -> List[Dict]:
        """
        수집된 요구사항을 바탕으로 면접 질문 생성
        
        Args:
            requirements: chat_for_requirements에서 수집된 정보
        
        Returns:
            생성된 질문 리스트
        """
        position = requirements.get('position', '개발자')
        experience = requirements.get('experience_level', '주니어')
        tech_stack = requirements.get('tech_stack', '일반')
        count = requirements.get('question_count', 20)
        difficulty_ratio = requirements.get('difficulty_ratio', {"easy": 3, "medium": 5, "hard": 2})
        focus_areas = requirements.get('focus_areas', ['기술역량', '소프트스킬'])
        
        # 난이도별 질문 개수 계산
        total_ratio = sum(difficulty_ratio.values())
        easy_count = int(count * difficulty_ratio['easy'] / total_ratio)
        medium_count = int(count * difficulty_ratio['medium'] / total_ratio)
        hard_count = count - easy_count - medium_count
        
        all_questions = []
        
        # 각 난이도별로 질문 생성
        for difficulty, num in [('하', easy_count), ('중', medium_count), ('상', hard_count)]:
            if num == 0:
                continue
                
            prompt = f"""
다음 조건에 맞는 면접 질문 {num}개를 생성하세요:

**면접 대상**:
- 직무: {position}
- 경력: {experience}
- 기술 스택: {tech_stack}
- 난이도: {difficulty}
- 중점 영역: {', '.join(focus_areas)}

**질문 생성 가이드라인**:
1. 실제 면접에서 나올 법한 현실적인 질문
2. 지원자의 경력 수준에 맞는 깊이
3. 기술 스택과 관련된 구체적인 질문
4. 평가 가능한 명확한 기준 포함
5. 각 질문마다 모범 답변 예시 포함

**난이도별 가이드**:
- 하: 기본 개념, 경험 중심, 정의 설명
- 중: 실무 적용, 트레이드오프, 문제 해결
- 상: 깊은 이해, 아키텍처, 최적화, 설계 철학

JSON 배열로 반환:
[
  {{
    "question": "구체적인 질문",
    "category": "기술역량 또는 소프트스킬",
    "context": "이 질문으로 무엇을 평가하려는지 설명",
    "sample_answer": "모범 답변 예시 (2-3문장)",
    "tags": ["관련태그1", "관련태그2", "관련태그3"],
    "evaluation_criteria": ["평가기준1", "평가기준2"]
  }}
]
"""
            
            response = self.openai_client.chat.completions.create(
                model=self.gpt_deployment,
                messages=[
                    {"role": "system", "content": "당신은 전문 면접 설계자입니다. 현실적이고 평가 가능한 면접 질문을 만듭니다."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            questions = result if isinstance(result, list) else result.get('questions', [])
            
            # 난이도 추가
            for q in questions:
                q['difficulty'] = difficulty
                q['position'] = position
                q['experience_level'] = experience
                q['tech_stack'] = tech_stack
            
            all_questions.extend(questions)
        
        return all_questions
    
    def get_embedding(self, text: str) -> List[float]:
        """텍스트 임베딩 생성"""
        response = self.openai_client.embeddings.create(
            model="text-embedding-ada-002",
            input=text
        )
        return response.data[0].embedding
    
    def upload_to_search(self, questions: List[Dict]) -> Dict:
        """
        생성된 질문을 Azure AI Search에 업로드
        
        Returns:
            {'success': 개수, 'failed': 개수, 'total': 개수}
        """
        # 기존 질문 개수 확인 (ID 생성용)
        try:
            results = self.search_client.search(search_text="*", top=1, select=["id"])
            existing_ids = [int(doc['id']) for doc in results if doc['id'].isdigit()]
            start_id = max(existing_ids) + 1 if existing_ids else 1
        except:
            start_id = 1
        
        # 문서 준비
        documents = []
        for i, q in enumerate(questions):
            # 임베딩 생성
            embedding_text = f"{q['question']} {q.get('context', '')} {' '.join(q.get('tags', []))}"
            embedding = self.get_embedding(embedding_text)
            
            doc = {
                "id": str(start_id + i),
                "question": q['question'],
                "category": q.get('category', '기술역량'),
                "difficulty": q.get('difficulty', '중'),
                "context": q.get('context', ''),
                "sample_answer": q.get('sample_answer', ''),
                "contentVector": embedding,
                "tags": q.get('tags', []),
                # 추가 메타데이터
                "position": q.get('position', ''),
                "experience_level": q.get('experience_level', ''),
                "tech_stack": q.get('tech_stack', ''),
                "evaluation_criteria": q.get('evaluation_criteria', [])
            }
            documents.append(doc)
        
        # 업로드
        result = self.search_client.upload_documents(documents=documents)
        
        success_count = sum(1 for r in result if r.succeeded)
        failed_count = len(result) - success_count
        
        return {
            'success': success_count,
            'failed': failed_count,
            'total': len(documents)
        }
    
    def analyze_existing_questions(self) -> Dict:
        """
        현재 저장된 질문 분석
        
        Returns:
            통계 정보
        """
        try:
            # 모든 질문 검색
            results = self.search_client.search(
                search_text="*",
                select=["category", "difficulty", "position", "tech_stack"],
                top=1000
            )
            
            questions = list(results)
            
            # 통계 계산
            total = len(questions)
            by_category = {}
            by_difficulty = {}
            by_position = {}
            
            for q in questions:
                # 카테고리별
                cat = q.get('category', '기타')
                by_category[cat] = by_category.get(cat, 0) + 1
                
                # 난이도별
                diff = q.get('difficulty', '중')
                by_difficulty[diff] = by_difficulty.get(diff, 0) + 1
                
                # 직무별
                pos = q.get('position', '일반')
                if pos:
                    by_position[pos] = by_position.get(pos, 0) + 1
            
            return {
                'total_questions': total,
                'by_category': by_category,
                'by_difficulty': by_difficulty,
                'by_position': by_position
            }
        except Exception as e:
            return {'error': str(e)}
    
    def generate_from_document(self, document_text: str, num_questions: int = 10) -> List[Dict]:
        """
        문서/텍스트 기반으로 질문 자동 생성
        예: 직무 기술서, 기술 문서, 회사 소개서 등을 분석하여 관련 질문 생성
        
        Args:
            document_text: 분석할 문서 텍스트
            num_questions: 생성할 질문 개수
        
        Returns:
            생성된 질문 리스트
        """
        prompt = f"""
다음 문서를 분석하여 관련된 면접 질문 {num_questions}개를 생성하세요:

**문서 내용**:
{document_text[:3000]}  # 최대 3000자

**생성 가이드라인**:
1. 문서에서 언급된 기술, 스킬, 요구사항을 기반으로 질문 생성
2. 해당 직무/분야에서 실제로 물어볼 법한 질문
3. 문서의 맥락과 연관된 실무 중심 질문
4. 다양한 난이도 (30% 쉬움, 50% 중간, 20% 어려움)

JSON 배열로 반환:
[
  {{
    "question": "질문",
    "category": "기술역량 또는 소프트스킬",
    "difficulty": "하, 중, 상",
    "context": "평가 목적",
    "sample_answer": "모범 답변",
    "tags": ["태그1", "태그2"],
    "document_relevance": "문서의 어떤 부분과 연관되는지"
  }}
]
"""
        
        response = self.openai_client.chat.completions.create(
            model=self.gpt_deployment,
            messages=[
                {"role": "system", "content": "당신은 문서 분석 및 면접 질문 생성 전문가입니다."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        questions = result if isinstance(result, list) else result.get('questions', [])
        
        return questions


# 테스트 및 예시 사용
if __name__ == "__main__":
    generator = QuestionGenerator()
    
    # 예시 1: 대화형 질문 생성
    print("=== 대화형 질문 생성 예시 ===\n")
    
    # 첫 번째 대화
    result1 = generator.chat_for_requirements("Python 백엔드 개발자 면접 질문 만들어줘")
    print(f"봇: {result1['response']}\n")
    
    # 두 번째 대화
    result2 = generator.chat_for_requirements("3년차 주니어 개발자야. Django랑 FastAPI 사용해")
    print(f"봇: {result2['response']}\n")
    
    # 세 번째 대화
    result3 = generator.chat_for_requirements("20개 정도 필요하고, 기술 역량 중심으로 만들어줘")
    print(f"봇: {result3['response']}\n")
    
    if result3.get('is_complete'):
        print("\n정보 수집 완료! 질문 생성 중...\n")
        
        # 질문 생성
        questions = generator.generate_questions(result3['collected_info'])
        print(f"생성된 질문 개수: {len(questions)}\n")
        
        # 첫 3개 질문 출력
        for i, q in enumerate(questions[:3], 1):
            print(f"\n질문 {i} [{q['difficulty']}]:")
            print(f"  {q['question']}")
            print(f"  카테고리: {q['category']}")
            print(f"  평가 목적: {q['context']}")
        
        # 업로드
        print("\n\nAzure AI Search에 업로드 중...")
        upload_result = generator.upload_to_search(questions)
        print(f"업로드 결과: {upload_result}")
    
    # 예시 2: 기존 질문 분석
    print("\n\n=== 기존 질문 DB 분석 ===")
    stats = generator.analyze_existing_questions()
    print(json.dumps(stats, indent=2, ensure_ascii=False))
