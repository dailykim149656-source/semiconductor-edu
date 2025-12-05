#!/usr/bin/env python3
"""
질문 자동 생성 기능 데모 스크립트
대화형 CLI로 질문을 생성하고 Azure AI Search에 업로드합니다.
"""

import os
import sys
from dotenv import load_dotenv
from question_generator import QuestionGenerator

# 환경 변수 로드
load_dotenv()

def print_banner():
    """배너 출력"""
    print("""
╔════════════════════════════════════════════════════════════╗
║                                                            ║
║   🤖 AI 면접 질문 자동 생성 데모                          ║
║                                                            ║
║   Azure OpenAI + AI Search 기반                           ║
║   대화형 질문 생성 및 RAG DB 자동 업로드                  ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
""")

def print_separator():
    print("\n" + "="*60 + "\n")

def demo_conversational_generation():
    """대화형 질문 생성 데모"""
    print_banner()
    print("💬 대화형 질문 생성 데모를 시작합니다.\n")
    print("AI와 대화하면서 원하는 면접 질문을 만들어보세요!")
    print("(종료하려면 'quit' 입력)\n")
    print_separator()
    
    generator = QuestionGenerator()
    
    while True:
        user_input = input("\n당신: ").strip()
        
        if user_input.lower() in ['quit', 'exit', '종료', '그만']:
            print("\n👋 데모를 종료합니다.\n")
            break
        
        if not user_input:
            continue
        
        try:
            # AI와 대화
            result = generator.chat_for_requirements(user_input)
            
            print(f"\nAI: {result['response']}\n")
            
            # 정보 수집 완료 확인
            if result.get('is_complete'):
                print_separator()
                print("✅ 정보 수집이 완료되었습니다!\n")
                
                # 수집된 정보 출력
                info = result['collected_info']
                print("📋 수집된 정보:")
                print(f"  - 직무: {info.get('position', 'N/A')}")
                print(f"  - 경력: {info.get('experience_level', 'N/A')}")
                print(f"  - 기술: {info.get('tech_stack', 'N/A')}")
                print(f"  - 질문 수: {info.get('question_count', 'N/A')}개")
                print(f"  - 중점 영역: {', '.join(info.get('focus_areas', []))}")
                
                # 생성 확인
                confirm = input("\n질문을 생성하시겠습니까? (y/n): ").strip().lower()
                
                if confirm in ['y', 'yes', '네', '응']:
                    print("\n⏳ 질문을 생성 중입니다...\n")
                    
                    # 질문 생성
                    questions = generator.generate_questions(info)
                    
                    print(f"✨ {len(questions)}개의 질문을 생성했습니다!\n")
                    
                    # 미리보기 (첫 3개)
                    print("📝 미리보기 (처음 3개):\n")
                    for i, q in enumerate(questions[:3], 1):
                        print(f"{i}. [{q['difficulty']}] {q['category']}")
                        print(f"   {q['question']}")
                        print(f"   평가: {q['context']}\n")
                    
                    # 업로드 확인
                    upload = input("\nAzure AI Search에 업로드하시겠습니까? (y/n): ").strip().lower()
                    
                    if upload in ['y', 'yes', '네', '응']:
                        print("\n⏳ 업로드 중...\n")
                        
                        upload_result = generator.upload_to_search(questions)
                        
                        print("✅ 업로드 완료!")
                        print(f"  - 성공: {upload_result['success']}개")
                        print(f"  - 실패: {upload_result['failed']}개")
                        print(f"  - 전체: {upload_result['total']}개\n")
                        
                        print("🎉 질문이 RAG DB에 추가되었습니다!")
                        print("   이제 면접 시뮬레이터에서 사용할 수 있습니다.\n")
                    
                    # 계속 여부
                    continue_gen = input("\n다른 질문을 생성하시겠습니까? (y/n): ").strip().lower()
                    if continue_gen not in ['y', 'yes', '네', '응']:
                        print("\n👋 데모를 종료합니다.\n")
                        break
                    
                    # 대화 히스토리 초기화
                    generator.conversation_history = []
                    print_separator()
                    print("💬 새로운 대화를 시작합니다.\n")
        
        except Exception as e:
            print(f"\n❌ 오류 발생: {str(e)}\n")
            continue


def demo_document_generation():
    """문서 기반 질문 생성 데모"""
    print_banner()
    print("📄 직무기술서 기반 질문 생성 데모\n")
    print_separator()
    
    generator = QuestionGenerator()
    
    print("채용 공고나 직무기술서를 입력하세요.")
    print("(입력 완료 후 빈 줄에서 Ctrl+D 또는 Ctrl+Z 입력)\n")
    
    lines = []
    try:
        while True:
            line = input()
            lines.append(line)
    except EOFError:
        pass
    
    document_text = "\n".join(lines)
    
    if not document_text.strip():
        print("\n❌ 입력된 내용이 없습니다.\n")
        return
    
    print(f"\n✅ 입력 완료 ({len(document_text)}자)\n")
    
    num_questions = input("생성할 질문 개수 (기본 10): ").strip()
    num_questions = int(num_questions) if num_questions.isdigit() else 10
    
    print(f"\n⏳ {num_questions}개의 질문을 생성 중...\n")
    
    try:
        questions = generator.generate_from_document(document_text, num_questions)
        
        print(f"✨ {len(questions)}개의 질문을 생성했습니다!\n")
        
        # 미리보기
        print("📝 생성된 질문:\n")
        for i, q in enumerate(questions, 1):
            print(f"{i}. [{q.get('difficulty', '중')}] {q.get('category', '')}")
            print(f"   {q['question']}")
            print(f"   문서 연관성: {q.get('document_relevance', 'N/A')}\n")
        
        # 업로드
        upload = input("Azure AI Search에 업로드하시겠습니까? (y/n): ").strip().lower()
        
        if upload in ['y', 'yes', '네', '응']:
            print("\n⏳ 업로드 중...\n")
            
            upload_result = generator.upload_to_search(questions)
            
            print("✅ 업로드 완료!")
            print(f"  - 성공: {upload_result['success']}개")
            print(f"  - 실패: {upload_result['failed']}개\n")
    
    except Exception as e:
        print(f"\n❌ 오류 발생: {str(e)}\n")


def demo_analyze_db():
    """질문 DB 분석 데모"""
    print_banner()
    print("📊 질문 DB 현황 분석\n")
    print_separator()
    
    generator = QuestionGenerator()
    
    print("⏳ 분석 중...\n")
    
    try:
        stats = generator.analyze_existing_questions()
        
        if 'error' in stats:
            print(f"❌ 오류: {stats['error']}\n")
            return
        
        print(f"📈 총 질문 수: {stats['total_questions']}개\n")
        
        if stats.get('by_category'):
            print("📂 카테고리별:")
            for cat, count in sorted(stats['by_category'].items(), key=lambda x: x[1], reverse=True):
                bar = "█" * (count // 2)
                print(f"  {cat:20s} {bar} {count}개")
            print()
        
        if stats.get('by_difficulty'):
            print("⚡ 난이도별:")
            for diff, count in sorted(stats['by_difficulty'].items()):
                bar = "█" * (count // 2)
                print(f"  {diff:20s} {bar} {count}개")
            print()
        
        if stats.get('by_position'):
            print("💼 직무별 (상위 10개):")
            sorted_pos = sorted(stats['by_position'].items(), key=lambda x: x[1], reverse=True)[:10]
            for pos, count in sorted_pos:
                if pos:
                    bar = "█" * (count // 2)
                    print(f"  {pos:20s} {bar} {count}개")
            print()
    
    except Exception as e:
        print(f"\n❌ 오류 발생: {str(e)}\n")


def main():
    """메인 함수"""
    if not os.getenv("AZURE_OPENAI_KEY"):
        print("\n❌ 오류: 환경 변수가 설정되지 않았습니다.")
        print("   .env 파일을 생성하고 Azure 키를 입력하세요.\n")
        sys.exit(1)
    
    while True:
        print_banner()
        print("어떤 데모를 실행하시겠습니까?\n")
        print("  1. 💬 대화형 질문 생성")
        print("  2. 📄 직무기술서 기반 생성")
        print("  3. 📊 질문 DB 현황 분석")
        print("  4. 🚪 종료\n")
        
        choice = input("선택 (1-4): ").strip()
        
        if choice == '1':
            demo_conversational_generation()
        elif choice == '2':
            demo_document_generation()
        elif choice == '3':
            demo_analyze_db()
        elif choice == '4':
            print("\n👋 프로그램을 종료합니다.\n")
            break
        else:
            print("\n❌ 잘못된 선택입니다.\n")
        
        input("\n계속하려면 Enter를 누르세요...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 프로그램을 종료합니다.\n")
        sys.exit(0)
