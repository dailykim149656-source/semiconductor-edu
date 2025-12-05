#!/usr/bin/env python3
"""
반도체 공정 샘플 질문 데이터 생성 및 업로드
초기 데이터베이스 구축용
"""

import os
from dotenv import load_dotenv
from document_processor import SemiconductorDocumentProcessor

load_dotenv()

# 샘플 반도체 공정 질문 데이터
SAMPLE_SEMICONDUCTOR_QUESTIONS = [
    # CVD (Chemical Vapor Deposition)
    {
        "question": "CVD 공정에서 온도, 압력, 반응가스 유량이 박막의 증착 속도에 미치는 영향을 설명하세요.",
        "answer": "온도 상승 시 화학 반응 속도가 증가하여 증착 속도가 빨라지나, 너무 높으면 균일도가 떨어집니다. 압력이 높으면 반응가스 농도가 증가하여 증착 속도가 빨라지지만, 과도하면 입자 형성이 일어납니다. 유량은 전구체 공급량을 결정하며, 적절한 유량에서 최적의 증착 속도와 균일도를 얻을 수 있습니다.",
        "process_category": "증착 (Deposition)",
        "question_type": "원리설명",
        "difficulty": "중급",
        "theory": "CVD는 화학 반응을 통해 기판 위에 박막을 형성하는 공정으로, 공정 파라미터가 박막 특성을 결정합니다.",
        "keywords": ["CVD", "증착속도", "온도", "압력", "유량"],
        "related_concepts": ["화학반응속도론", "아레니우스 방정식", "박막성장"]
    },
    {
        "question": "PECVD와 LPCVD의 차이점을 비교하고, 각각의 장단점을 설명하세요.",
        "answer": "PECVD는 플라즈마를 이용하여 저온에서 증착이 가능하며, 온도에 민감한 기판에 적합합니다. 하지만 박막 품질이 상대적으로 낮습니다. LPCVD는 고온, 저압에서 진행되어 우수한 균일도와 박막 품질을 제공하나, 높은 온도가 필요하고 처리량이 낮습니다.",
        "process_category": "증착 (Deposition)",
        "question_type": "비교",
        "difficulty": "중급",
        "theory": "CVD의 변형 공정들은 온도, 압력, 에너지원에 따라 다른 특성을 가집니다.",
        "keywords": ["PECVD", "LPCVD", "플라즈마", "저온증착"],
        "related_concepts": ["플라즈마 물리", "박막 품질", "공정 최적화"]
    },
    
    # 리소그래피 (Lithography)
    {
        "question": "포토리소그래피 공정의 주요 단계를 순서대로 설명하고, 각 단계의 목적을 기술하세요.",
        "answer": "1) 기판 준비 및 세정, 2) 포토레지스트 도포(스핀 코팅), 3) 소프트 베이크(용매 제거), 4) 노광(마스크를 통한 UV 조사), 5) 노광 후 베이크(PEB, 화학반응 촉진), 6) 현상(패턴 형성), 7) 하드 베이크(레지스트 경화). 각 단계는 정밀한 패턴 전사를 위해 필수적입니다.",
        "process_category": "리소그래피 (Lithography)",
        "question_type": "개념이해",
        "difficulty": "기초",
        "theory": "리소그래피는 반도체 패터닝의 핵심 공정으로, 빛을 이용하여 패턴을 전사합니다.",
        "keywords": ["포토리소그래피", "포토레지스트", "노광", "현상"],
        "related_concepts": ["광학", "화학 증폭", "패턴 전사"]
    },
    {
        "question": "NA(Numerical Aperture)와 λ(파장)가 리소그래피 해상도에 미치는 영향을 Rayleigh 식을 이용하여 설명하세요.",
        "answer": "Rayleigh 식: R = k₁(λ/NA)에서 해상도 R은 파장 λ에 비례하고 NA에 반비례합니다. 따라서 더 작은 패턴을 만들려면 짧은 파장(EUV 등)을 사용하거나 높은 NA 렌즈를 사용해야 합니다. k₁은 공정 인자로 0.25~0.6 범위입니다.",
        "process_category": "리소그래피 (Lithography)",
        "question_type": "원리설명",
        "difficulty": "고급",
        "theory": "광학적 해상도는 파장과 개구수에 의해 결정되며, 이는 반도체 미세화의 한계를 설명합니다.",
        "keywords": ["해상도", "NA", "파장", "Rayleigh식"],
        "related_concepts": ["광학 이론", "회절 한계", "EUV"]
    },
    
    # 식각 (Etching)
    {
        "question": "등방성 식각과 이방성 식각의 차이를 설명하고, 각각이 사용되는 응용 분야를 제시하세요.",
        "answer": "등방성 식각은 모든 방향으로 동일한 속도로 식각되어 언더컷이 발생합니다. 습식 식각이 대표적이며, 평탄화나 세정에 사용됩니다. 이방성 식각은 수직 방향으로만 식각되어 높은 종횡비를 구현할 수 있습니다. RIE 등의 건식 식각이 대표적이며, 미세 패턴 형성에 필수적입니다.",
        "process_category": "식각 (Etching)",
        "question_type": "비교",
        "difficulty": "중급",
        "theory": "식각의 방향성은 패턴 정밀도를 결정하는 핵심 요소입니다.",
        "keywords": ["등방성", "이방성", "언더컷", "종횡비"],
        "related_concepts": ["습식 식각", "건식 식각", "RIE"]
    },
    {
        "question": "RIE(Reactive Ion Etching)에서 플라즈마의 역할과 이온 충돌이 이방성 식각에 기여하는 메커니즘을 설명하세요.",
        "answer": "플라즈마는 반응성 라디칼과 이온을 생성합니다. 라디칼은 화학적 식각을 담당하고, 이온은 전기장에 의해 가속되어 기판에 수직으로 입사합니다. 이 이온 충돌이 수직 방향의 식각을 촉진하고 측면 식각을 억제하여 이방성을 만듭니다. 또한 이온이 표면을 물리적으로 스퍼터링하여 식각을 가속화합니다.",
        "process_category": "식각 (Etching)",
        "question_type": "원리설명",
        "difficulty": "고급",
        "theory": "RIE는 화학적 반응과 물리적 충돌을 결합하여 정밀한 식각을 구현합니다.",
        "keywords": ["RIE", "플라즈마", "이온충돌", "이방성"],
        "related_concepts": ["플라즈마 물리", "스퍼터링", "시스 전압"]
    },
    
    # 이온주입 (Ion Implantation)
    {
        "question": "이온주입 공정에서 에너지와 도즈가 도펀트 분포에 미치는 영향을 설명하세요.",
        "answer": "에너지는 이온의 주입 깊이를 결정합니다. 높은 에너지는 깊은 주입을, 낮은 에너지는 얕은 주입을 만듭니다. 도즈는 주입되는 이온의 총량으로, 도펀트 농도를 결정합니다. 높은 도즈는 높은 농도를, 낮은 도즈는 낮은 농도를 형성합니다. LSS 이론으로 예측 가능합니다.",
        "process_category": "이온주입 (Ion Implantation)",
        "question_type": "개념이해",
        "difficulty": "중급",
        "theory": "이온주입은 정밀한 도핑 농도와 깊이 제어가 가능한 핵심 공정입니다.",
        "keywords": ["이온주입", "에너지", "도즈", "도펀트분포"],
        "related_concepts": ["LSS 이론", "채널링", "어닐링"]
    },
    {
        "question": "채널링 현상을 설명하고, 이를 방지하기 위한 방법을 제시하세요.",
        "answer": "채널링은 이온이 결정 격자의 특정 방향을 따라 깊숙이 침투하는 현상입니다. 이는 예상보다 깊은 주입 분포를 만들어 소자 특성을 저하시킵니다. 방지 방법으로는 1) 기판을 7° 정도 틸팅하여 이온 입사각을 조정, 2) 비정질 표면층(산화막 등) 형성, 3) 사전 비정질화(PAI) 등이 있습니다.",
        "process_category": "이온주입 (Ion Implantation)",
        "question_type": "문제해결",
        "difficulty": "고급",
        "theory": "결정 구조와 이온 궤적의 상호작용은 주입 분포에 영향을 미칩니다.",
        "keywords": ["채널링", "결정격자", "틸팅", "비정질화"],
        "related_concepts": ["결정학", "이온-고체 상호작용", "PAI"]
    },
    
    # 박막 분석
    {
        "question": "SEM과 TEM의 차이점을 비교하고, 각각이 적합한 분석 대상을 설명하세요.",
        "answer": "SEM은 표면 형상과 조성을 분석하며, 해상도는 수 nm 수준입니다. 시료 준비가 간단하고 넓은 영역 관찰이 가능합니다. TEM은 투과 이미지를 통해 내부 구조를 분석하며, 원자 수준 해상도가 가능합니다. 박막의 결정 구조, 계면, 결함 분석에 적합하나 시료 준비가 복잡합니다.",
        "process_category": "검사 (Inspection)",
        "question_type": "비교",
        "difficulty": "중급",
        "theory": "전자 현미경은 반도체 박막의 구조와 특성을 분석하는 필수 도구입니다.",
        "keywords": ["SEM", "TEM", "표면분석", "투과전자현미경"],
        "related_concepts": ["전자-물질 상호작용", "회절", "이미징"]
    },
    
    # CMP
    {
        "question": "CMP 공정의 원리를 설명하고, 슬러리의 역할과 중요 파라미터를 기술하세요.",
        "answer": "CMP는 화학적 반응과 기계적 연마를 결합하여 웨이퍼 표면을 평탄화합니다. 슬러리는 연마제(abrasive)와 화학 첨가제를 포함하여 재료를 선택적으로 제거합니다. 중요 파라미터는 1) 압력(down force), 2) 회전 속도, 3) 슬러리 유량, 4) pH, 5) 연마 시간 등이며, 이들이 연마 속도와 균일도를 결정합니다.",
        "process_category": "CMP (Chemical Mechanical Polishing)",
        "question_type": "개념이해",
        "difficulty": "중급",
        "theory": "CMP는 다층 구조 형성을 위한 필수 평탄화 공정입니다.",
        "keywords": ["CMP", "평탄화", "슬러리", "연마"],
        "related_concepts": ["Preston 방정식", "선택비", "디싱"]
    },
    
    # 실무/통합
    {
        "question": "반도체 공정 중 발생할 수 있는 파티클(particle) 오염의 원인과 이를 최소화하기 위한 방법을 설명하세요.",
        "answer": "파티클은 장비, 화학물질, 환경(클린룸), 웨이퍼 핸들링 등에서 발생합니다. 최소화 방법: 1) 클린룸 청정도 유지(HEPA 필터), 2) 장비 정기 세정, 3) 고순도 화학물질 사용, 4) 정전기 방지, 5) 웨이퍼 세정 공정(RCA 등), 6) 인-시튜 모니터링. 파티클은 수율 저하의 주요 원인입니다.",
        "process_category": "세정 (Cleaning)",
        "question_type": "실무",
        "difficulty": "중급",
        "theory": "파티클 관리는 반도체 제조 수율을 결정하는 핵심 요소입니다.",
        "keywords": ["파티클", "오염", "클린룸", "세정"],
        "related_concepts": ["수율 관리", "품질 관리", "RCA 세정"]
    }
]


def initialize_semiconductor_db():
    """반도체 샘플 질문 DB 초기화"""
    print("=" * 60)
    print("반도체 공정 질문 DB 초기화")
    print("=" * 60)
    
    processor = SemiconductorDocumentProcessor()
    
    # 인덱스 생성
    print("\n1. 검색 인덱스 생성 중...")
    try:
        processor.create_search_index()
        print("✅ 인덱스 생성 완료")
    except Exception as e:
        print(f"⚠️  인덱스 이미 존재하거나 오류: {e}")
    
    # 질문 업로드
    print(f"\n2. {len(SAMPLE_SEMICONDUCTOR_QUESTIONS)}개 샘플 질문 업로드 중...")
    result = processor.upload_to_search(SAMPLE_SEMICONDUCTOR_QUESTIONS)
    
    print(f"\n✅ 업로드 완료:")
    print(f"   - 성공: {result['success']}개")
    print(f"   - 실패: {result['failed']}개")
    print(f"   - 총: {result['total']}개")
    
    # 통계
    print("\n3. DB 통계:")
    print(f"   공정별 분포:")
    categories = {}
    for q in SAMPLE_SEMICONDUCTOR_QUESTIONS:
        cat = q['process_category']
        categories[cat] = categories.get(cat, 0) + 1
    
    for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        print(f"   - {cat}: {count}개")
    
    print("\n" + "=" * 60)
    print("✅ 초기화 완료! 이제 시뮬레이터를 사용할 수 있습니다.")
    print("=" * 60)


if __name__ == "__main__":
    initialize_semiconductor_db()
