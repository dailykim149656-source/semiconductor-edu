# 🔧 RAG 검색 및 프로필 분석 문제 해결

## 📋 발견된 문제

### 1. RAG 검색이 작동하지 않음
- **증상**: 학습 모드에서 "관련 지식을 찾을 수 없습니다"
- **원인**: AI Search 인덱스의 필드 이름 불일치

### 2. 프로필 분석 데이터가 활용되지 않음
- **증상**: 면접 모드에서 "학생의 경험 정보 부족" 메시지
- **원인**: 프로필 데이터 구조 문제 및 필드 매핑 이슈

## ✅ 수정 완료

### 1. RAG 검색 개선

**변경 사항:**
- 유연한 필드 이름 매핑 (question, Question, title 등 모두 인식)
- 검색 실패 시 필터 없이 재시도
- 검색 결과 없어도 GPT가 직접 질문 생성
- 상세한 로깅 (디버깅 용이)

**새로운 기능:**
```python
# 다양한 필드명 자동 인식
'question': result.get('question') or result.get('Question') or result.get('title')
'answer': result.get('answer') or result.get('Answer') or result.get('content')

# RAG 결과 없어도 작동
if not knowledge:
    logger.warning("RAG 결과 없음, GPT가 직접 생성")
    # GPT가 주제 기반으로 직접 질문 생성
```

### 2. 프로필 분석 개선

**변경 사항:**
- 더 상세한 정보 추출 (experiences, projects, skills, interests)
- 다양한 필드명 지원 (한글/영문)
- GPT 프롬프트에 구체적 예시 추가
- 프로필 데이터 검증 및 기본값 설정

**새로운 출력 형식:**
```json
{
    "education": "서울대학교 재료공학부 3학년, GPA 3.82/4.3",
    "experiences": [
        "ITO 박막 증착 최적화 프로젝트",
        "MEMS 압력센서 제작 실습",
        "저온 ALD 공정 연구"
    ],
    "projects": ["ITO 박막", "MEMS 센서"],
    "skills": ["RF 스퍼터링", "RIE 식각", "XRD"],
    "interests": ["박막 증착", "공정 최적화"],
    "career_goal": "대기업 공정 엔지니어",
    "strengths": ["끈기", "문제 해결"],
    "weaknesses": ["영어"]
}
```

### 3. 면접 질문 생성 개선

**변경 사항:**
- 프로필 전체 데이터를 GPT에 전달
- 구체적인 프로젝트/경험을 언급하도록 프롬프트 강화
- 질문 생성 예시 추가

**예상 결과:**
```
기존: "반도체 공정에 대해 설명하세요"

개선: "ITO 박막 프로젝트에서 RF 파워를 150W로 설정한 이유와,
      압력 3mTorr가 박막 특성에 미치는 영향을 설명하세요."
```

---

## 🧪 테스트 방법

### 1. RAG 검색 테스트

```bash
# 시뮬레이터 실행
python semiconductor_simulator_v2.py

# 로그 확인 (별도 터미널)
tail -f semiconductor_simulator.log
```

**학습 모드 테스트:**
1. 주제: "CVD 증착"
2. 난이도: "중급"
3. "학습 시작" 클릭

**기대 로그:**
```
🔍 검색 시작: query='CVD 증착', filter=difficulty eq '중급', top=3
✅ 검색 성공: 5개 결과 발견
✅ 학습 질문 생성 완료
```

또는:
```
⚠️  검색 결과 없음: 'CVD 증착'
⚠️  RAG 결과 없음, GPT가 직접 생성
✅ 학습 질문 생성 완료
```

### 2. 프로필 분석 테스트

**파일 업로드:**
1. "프로필 설정" 탭
2. sample_resume.docx 업로드
3. sample_personal_statement.docx 업로드
4. "분석 시작" 클릭

**기대 출력:**
```json
{
    "✅ 분석 완료": "프로필이 저장되었습니다...",
    "📚 학력": "서울대학교 재료공학부 3학년...",
    "💼 경험 (3개)": [
        "ITO 박막 증착 최적화...",
        "MEMS 압력센서 제작...",
        "저온 ALD 공정 연구..."
    ],
    "🛠️ 기술 스킬 (7개)": [...],
    "❤️ 관심 분야 (3개)": [...]
}
```

**기대 로그:**
```
👤 프로필 분석 시작...
📄 파일 처리 시작: sample_resume.docx, sample_personal_statement.docx
✅ 텍스트 추출 완료: 이력서 5234자, 자소서 3421자
✅ 프로필 분석 완료:
   - 경험: 3개
   - 스킬: 7개
   - 관심사: 3개
```

### 3. 맞춤형 면접 질문 테스트

**프로필 분석 후:**
1. "면접 모드" 탭
2. "내 프로필 기반 맞춤형 질문" ✅ 체크
3. "면접 시작" 클릭

**기대 결과:**
```
질문: "ITO 박막 증착 프로젝트에서 RF 스퍼터링 공정의 
압력 파라미터를 3mTorr로 선택한 이유는 무엇인가요? 
이 조건이 박막의 전기전도도에 미치는 영향을 
플라즈마 메커니즘과 연결하여 설명해주세요."
```

**기대 로그:**
```
💼 면접 질문 생성 시작 (프로필 사용: True, 중점: 전체)
📊 프로필 요약: 3개 경험, 3개 관심사, 7개 스킬
✅ 면접 질문 생성 완료
```

---

## 🔍 디버깅 가이드

### 문제: "관련 지식을 찾을 수 없습니다"

**확인 사항:**
1. AI Search 인덱스에 데이터가 있는지 확인
```bash
python init_semiconductor_db.py
```

2. 인덱스 이름 확인
```bash
# .env 파일
AZURE_SEARCH_INDEX_NAME=semicon-edu-rag  # 사용자 설정값
```

3. 로그 확인
```
2025-12-05 14:40:15 - __main__ - INFO - 🔍 검색 시작: query='CVD', filter=None, top=3
2025-12-05 14:40:16 - __main__ - WARNING - ⚠️  검색 결과 없음: 'CVD'
```

**해결:**
- 검색어를 더 일반적으로 변경 ("CVD 증착" → "증착")
- RAG 없이도 작동하도록 수정 완료 (GPT 직접 생성)

### 문제: 프로필 데이터가 면접 질문에 반영 안 됨

**확인 사항:**
1. 프로필 분석 성공 확인
```
✅ 프로필 분석 완료:
   - 경험: 0개  ← 문제!
   - 스킬: 0개   ← 문제!
```

2. GPT 응답 확인
```python
# 터미널에서 직접 테스트
python -c "
from semiconductor_simulator_v2 import SemiconductorSimulator
simulator = SemiconductorSimulator()
profile = simulator.analyze_profile('이력서 내용', '자소서 내용')
print(profile)
"
```

3. JSON 파싱 오류 확인
```
❌ JSON 파싱 오류: Expecting value: line 1 column 1
```

**해결:**
- GPT 프롬프트에 명확한 예시 추가 (수정 완료)
- Fallback 프로필 생성 (수정 완료)

---

## 📊 로그 레벨 조정

**디버깅을 위해 로그 레벨 변경:**

```bash
# .env 파일
LOG_LEVEL=DEBUG  # INFO → DEBUG로 변경
```

**재실행:**
```bash
python semiconductor_simulator_v2.py
```

**상세 로그 예시:**
```
DEBUG - 첫 번째 결과: CVD 공정에서 압력이 증착 속도에 미치는 영향...
DEBUG - 프로필 데이터: {'education': '서울대학교...', 'experiences': [...]}
DEBUG - GPT 응답: {"education": "서울대학교 재료공학부 3학년..."}
```

---

## ✅ 확인 체크리스트

### RAG 검색
- [ ] AI Search 인덱스 생성 (`python init_semiconductor_db.py`)
- [ ] 검색 로그에서 "✅ 검색 성공" 확인
- [ ] RAG 결과 없어도 질문 생성 확인

### 프로필 분석
- [ ] 파일 업로드 성공
- [ ] "✅ 프로필 분석 완료" 로그 확인
- [ ] 경험/스킬/관심사 개수가 0개 이상
- [ ] JSON 출력에서 "✅ 분석 완료" 확인

### 맞춤형 질문
- [ ] 프로필 체크박스 활성화
- [ ] 질문에 구체적인 프로젝트명 언급
- [ ] "📊 프로필 요약" 로그 확인

---

## 🆘 여전히 안 되면?

### 1. 전체 재설치
```bash
pip uninstall -r requirements.txt -y
pip install -r requirements.txt
```

### 2. 환경 변수 재확인
```bash
cat .env | grep -E "OPENAI|SEARCH"
```

### 3. AI Search 인덱스 재생성
```bash
python init_semiconductor_db.py --force-recreate
```

### 4. 로그 파일 전송
```bash
# 로그 저장
python semiconductor_simulator_v2.py > simulator.log 2>&1

# 문제 부분 확인
grep -A 5 "ERROR\|WARNING" simulator.log
```

---

**수정된 코드로 다시 실행해보세요!**

```bash
python semiconductor_simulator_v2.py
```

**이제 RAG 검색과 프로필 분석이 모두 개선되었습니다! 🎉**
