"""
Azure AI Search 인덱스 생성 및 면접 질문 데이터 업로드
RAG 시스템을 위한 벡터 검색 설정
"""

import os
import json
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SimpleField,
    SearchableField,
    SearchField,
    SearchFieldDataType,
    VectorSearch,
    VectorSearchProfile,
    HnswAlgorithmConfiguration,
)
from azure.core.credentials import AzureKeyCredential
from openai import AzureOpenAI

# Azure 설정
SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
SEARCH_KEY = os.getenv("AZURE_SEARCH_KEY")
INDEX_NAME = "interview-questions"

OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY")

# 인덱스 생성
def create_search_index():
    """벡터 검색이 가능한 인덱스 생성"""
    index_client = SearchIndexClient(
        endpoint=SEARCH_ENDPOINT,
        credential=AzureKeyCredential(SEARCH_KEY)
    )
    
    # 벡터 검색 설정
    vector_search = VectorSearch(
        algorithms=[
            HnswAlgorithmConfiguration(
                name="hnsw-config",
                parameters={
                    "m": 4,
                    "efConstruction": 400,
                    "efSearch": 500,
                    "metric": "cosine"
                }
            )
        ],
        profiles=[
            VectorSearchProfile(
                name="vector-profile",
                algorithm_configuration_name="hnsw-config",
            )
        ]
    )
    
    # 인덱스 필드 정의
    fields = [
        SimpleField(
            name="id",
            type=SearchFieldDataType.String,
            key=True,
            filterable=True
        ),
        SearchableField(
            name="question",
            type=SearchFieldDataType.String,
            searchable=True
        ),
        SearchableField(
            name="category",
            type=SearchFieldDataType.String,
            filterable=True,
            facetable=True
        ),
        SimpleField(
            name="difficulty",
            type=SearchFieldDataType.String,
            filterable=True,
            facetable=True
        ),
        SearchableField(
            name="context",
            type=SearchFieldDataType.String,
            searchable=True
        ),
        SearchableField(
            name="sample_answer",
            type=SearchFieldDataType.String,
            searchable=True
        ),
        SearchField(
            name="contentVector",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=1536,
            vector_search_profile_name="vector-profile"
        ),
        SearchableField(
            name="tags",
            type=SearchFieldDataType.Collection(SearchFieldDataType.String),
            filterable=True,
            facetable=True
        )
    ]
    
    # 인덱스 생성
    index = SearchIndex(
        name=INDEX_NAME,
        fields=fields,
        vector_search=vector_search
    )
    
    result = index_client.create_or_update_index(index)
    print(f"인덱스 '{result.name}' 생성 완료!")
    return result


# 샘플 면접 질문 데이터
SAMPLE_QUESTIONS = [
    {
        "id": "1",
        "question": "최근에 진행한 프로젝트에서 가장 어려웠던 기술적 챌린지는 무엇이었나요? 어떻게 해결하셨나요?",
        "category": "기술역량",
        "difficulty": "중",
        "context": "지원자의 문제 해결 능력과 기술적 깊이를 평가하는 질문입니다.",
        "sample_answer": "프로젝트에서 대용량 트래픽 처리가 필요했습니다. Redis 캐싱과 DB 인덱싱을 최적화하여 응답 시간을 70% 개선했습니다.",
        "tags": ["문제해결", "기술적챌린지", "프로젝트경험"]
    },
    {
        "id": "2",
        "question": "팀원과 의견 충돌이 있었던 경험과, 그것을 어떻게 해결했는지 설명해주세요.",
        "category": "소프트스킬",
        "difficulty": "중",
        "context": "협업 능력과 갈등 해결 능력을 평가하는 질문입니다.",
        "sample_answer": "기술 스택 선택에서 의견이 달랐습니다. 각자의 의견을 데이터로 정리하여 발표하고, 팀 투표로 결정했습니다. 결과적으로 모두가 납득할 수 있었습니다.",
        "tags": ["협업", "갈등해결", "커뮤니케이션"]
    },
    {
        "id": "3",
        "question": "RESTful API를 설계할 때 고려해야 할 핵심 원칙들을 설명하고, 실제 적용 사례를 공유해주세요.",
        "category": "기술역량",
        "difficulty": "상",
        "context": "API 설계 역량과 실무 경험을 평가하는 질문입니다.",
        "sample_answer": "무상태성, 캐시 가능성, 계층화 시스템, 일관된 인터페이스를 고려합니다. 이전 프로젝트에서 버저닝 전략(v1, v2)을 사용하여 하위 호환성을 유지했습니다.",
        "tags": ["API설계", "REST", "소프트웨어아키텍처"]
    },
    {
        "id": "4",
        "question": "데이터베이스 정규화의 목적과 각 정규형에 대해 설명해주세요. 실무에서 비정규화를 고려한 적이 있나요?",
        "category": "기술역량",
        "difficulty": "상",
        "context": "데이터베이스 설계 이론과 실무 적용 능력을 평가합니다.",
        "sample_answer": "정규화는 데이터 중복을 최소화하고 무결성을 보장합니다. 1NF부터 3NF까지는 필수적으로 적용하되, 조회 성능이 중요한 리포트 테이블은 의도적으로 비정규화했습니다.",
        "tags": ["데이터베이스", "정규화", "성능최적화"]
    },
    {
        "id": "5",
        "question": "마이크로서비스 아키텍처의 장단점을 설명하고, 모놀리식 아키텍처 대비 어떤 상황에서 적합한지 말씀해주세요.",
        "category": "기술역량",
        "difficulty": "상",
        "context": "아키텍처 이해도와 의사결정 능력을 평가합니다.",
        "sample_answer": "마이크로서비스는 독립적인 배포와 확장이 가능하지만 운영 복잡도가 높습니다. 트래픽 패턴이 다른 서비스들이나 대규모 팀 구조에서 적합합니다.",
        "tags": ["아키텍처", "마이크로서비스", "시스템설계"]
    },
    {
        "id": "6",
        "question": "시간 관리가 어려웠던 프로젝트 경험이 있나요? 우선순위를 어떻게 설정하셨나요?",
        "category": "소프트스킬",
        "difficulty": "하",
        "context": "시간 관리 능력과 우선순위 설정 능력을 평가합니다.",
        "sample_answer": "동시에 여러 요구사항이 들어왔을 때, 비즈니스 임팩트와 긴급도 매트릭스를 사용하여 우선순위를 정했습니다. PM과 긴밀히 소통하여 일정을 조율했습니다.",
        "tags": ["시간관리", "우선순위", "프로젝트관리"]
    },
    {
        "id": "7",
        "question": "CI/CD 파이프라인을 구축한 경험이 있나요? 어떤 도구를 사용하셨고, 어떤 이점이 있었나요?",
        "category": "기술역량",
        "difficulty": "중",
        "context": "DevOps 역량과 자동화 경험을 평가합니다.",
        "sample_answer": "Jenkins와 Docker를 사용하여 자동 빌드, 테스트, 배포 파이프라인을 구축했습니다. 배포 시간이 1시간에서 10분으로 단축되었고, 휴먼 에러가 줄었습니다.",
        "tags": ["DevOps", "CI/CD", "자동화"]
    },
    {
        "id": "8",
        "question": "코드 리뷰 시 어떤 점을 중점적으로 확인하시나요? 동료에게 피드백을 줄 때 어떤 방식을 사용하시나요?",
        "category": "소프트스킬",
        "difficulty": "중",
        "context": "코드 품질 관리와 커뮤니케이션 능력을 평가합니다.",
        "sample_answer": "가독성, 성능, 보안 이슈를 중점적으로 봅니다. 피드백은 '제안' 형태로 제시하고, 왜 그렇게 생각하는지 이유를 함께 설명합니다.",
        "tags": ["코드리뷰", "협업", "코드품질"]
    },
    {
        "id": "9",
        "question": "성능 최적화가 필요했던 경험이 있나요? 어떤 지표를 측정했고, 어떻게 개선하셨나요?",
        "category": "기술역량",
        "difficulty": "상",
        "context": "성능 분석 및 최적화 능력을 평가합니다.",
        "sample_answer": "API 응답 시간이 3초를 넘어 문제였습니다. New Relic으로 병목을 찾아 N+1 쿼리 문제를 발견하고, eager loading으로 해결하여 0.5초로 개선했습니다.",
        "tags": ["성능최적화", "모니터링", "문제해결"]
    },
    {
        "id": "10",
        "question": "보안 취약점을 발견하거나 대응한 경험이 있나요? 어떤 조치를 취하셨나요?",
        "category": "기술역량",
        "difficulty": "상",
        "context": "보안 인식과 대응 능력을 평가합니다.",
        "sample_answer": "SQL Injection 취약점을 발견했습니다. 즉시 Prepared Statement로 수정하고, 팀에 보안 가이드라인을 공유했습니다. OWASP Top 10 기준으로 전체 코드를 검토했습니다.",
        "tags": ["보안", "취약점대응", "코드품질"]
    },
    {
        "id": "11",
        "question": "새로운 기술이나 프레임워크를 학습할 때 어떤 방식으로 접근하시나요?",
        "category": "소프트스킬",
        "difficulty": "하",
        "context": "학습 능력과 적응력을 평가합니다.",
        "sample_answer": "공식 문서를 먼저 읽고 작은 프로젝트를 만들어봅니다. 온라인 강의와 커뮤니티를 활용하고, 블로그에 학습 내용을 정리하며 이해도를 높입니다.",
        "tags": ["학습능력", "자기계발", "적응력"]
    },
    {
        "id": "12",
        "question": "클라우드 환경(AWS, Azure, GCP 등)에서 작업한 경험이 있나요? 어떤 서비스를 주로 사용하셨나요?",
        "category": "기술역량",
        "difficulty": "중",
        "context": "클라우드 경험과 인프라 이해도를 평가합니다.",
        "sample_answer": "AWS에서 EC2, RDS, S3, Lambda를 사용했습니다. Auto Scaling으로 트래픽 변동에 대응하고, CloudWatch로 모니터링 시스템을 구축했습니다.",
        "tags": ["클라우드", "AWS", "인프라"]
    },
    {
        "id": "13",
        "question": "테스트 코드 작성의 중요성에 대해 어떻게 생각하시나요? 어떤 테스트 전략을 사용하시나요?",
        "category": "기술역량",
        "difficulty": "중",
        "context": "테스트 및 코드 품질에 대한 인식을 평가합니다.",
        "sample_answer": "테스트는 리팩토링의 안전장치입니다. Unit Test로 기본 로직을 검증하고, Integration Test로 API를 테스트합니다. 테스트 커버리지 80% 이상을 목표로 합니다.",
        "tags": ["테스트", "코드품질", "자동화"]
    },
    {
        "id": "14",
        "question": "실패한 프로젝트나 기능 개발 경험이 있나요? 그로부터 무엇을 배우셨나요?",
        "category": "소프트스킬",
        "difficulty": "중",
        "context": "실패 경험과 학습 능력을 평가합니다.",
        "sample_answer": "요구사항을 충분히 파악하지 않고 개발해 재작업했습니다. 이후 개발 전 상세 명세서를 작성하고, 프로토타입으로 검증하는 프로세스를 도입했습니다.",
        "tags": ["실패경험", "학습", "성장"]
    },
    {
        "id": "15",
        "question": "Git을 사용한 협업 경험이 있나요? 브랜치 전략과 Merge 방식은 어떻게 사용하셨나요?",
        "category": "기술역량",
        "difficulty": "하",
        "context": "버전 관리 및 협업 도구 사용 능력을 평가합니다.",
        "sample_answer": "Git Flow 전략을 사용했습니다. feature 브랜치에서 개발 후 Pull Request를 통해 코드 리뷰를 받고 merge했습니다. Squash merge로 커밋 히스토리를 깔끔하게 유지했습니다.",
        "tags": ["Git", "협업", "버전관리"]
    }
]


def get_embeddings(texts):
    """OpenAI로 임베딩 생성"""
    client = AzureOpenAI(
        api_key=OPENAI_KEY,
        api_version="2024-02-15-preview",
        azure_endpoint=OPENAI_ENDPOINT
    )
    
    embeddings = []
    for text in texts:
        response = client.embeddings.create(
            model="text-embedding-ada-002",
            input=text
        )
        embeddings.append(response.data[0].embedding)
    
    return embeddings


def upload_documents():
    """문서 업로드"""
    search_client = SearchClient(
        endpoint=SEARCH_ENDPOINT,
        index_name=INDEX_NAME,
        credential=AzureKeyCredential(SEARCH_KEY)
    )
    
    # 각 질문에 대한 임베딩 생성
    print("임베딩 생성 중...")
    questions = [q["question"] for q in SAMPLE_QUESTIONS]
    embeddings = get_embeddings(questions)
    
    # 임베딩을 문서에 추가
    documents = []
    for i, question_data in enumerate(SAMPLE_QUESTIONS):
        doc = question_data.copy()
        doc["contentVector"] = embeddings[i]
        documents.append(doc)
    
    # 업로드
    print(f"{len(documents)}개 문서 업로드 중...")
    result = search_client.upload_documents(documents=documents)
    
    success_count = sum(1 for r in result if r.succeeded)
    print(f"업로드 완료: {success_count}/{len(documents)}개 성공")
    
    return result


def test_search():
    """검색 테스트"""
    search_client = SearchClient(
        endpoint=SEARCH_ENDPOINT,
        index_name=INDEX_NAME,
        credential=AzureKeyCredential(SEARCH_KEY)
    )
    
    test_query = "API 설계 경험"
    print(f"\n테스트 검색: '{test_query}'")
    
    results = search_client.search(
        search_text=test_query,
        select=["question", "category", "difficulty"],
        top=3
    )
    
    print("\n검색 결과:")
    for i, doc in enumerate(results):
        print(f"\n{i+1}. [{doc['category']}] {doc['question']}")


if __name__ == "__main__":
    print("=== Azure AI Search 설정 시작 ===\n")
    
    # 1. 인덱스 생성
    print("1. 인덱스 생성...")
    create_search_index()
    
    # 2. 문서 업로드
    print("\n2. 샘플 질문 업로드...")
    upload_documents()
    
    # 3. 검색 테스트
    print("\n3. 검색 테스트...")
    test_search()
    
    print("\n=== 설정 완료! ===")
