"""
데이터 저장 및 리포트 생성 모듈
- Azure Blob Storage에 질문/답변/평가 저장
- PDF 면접 리포트 생성
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class DataStorageManager:
    """Azure Blob Storage 데이터 관리"""
    
    def __init__(self):
        """초기화"""
        self.blob_service_client = None
        self.container_name = os.getenv('AZURE_STORAGE_CONTAINER', 'semiconductor-data')
        
        try:
            from azure.storage.blob import BlobServiceClient
            
            connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
            
            if connection_string:
                self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)
                
                # 컨테이너 생성 (없으면)
                try:
                    self.blob_service_client.create_container(self.container_name)
                    logger.info(f"✅ Blob 컨테이너 생성: {self.container_name}")
                except Exception:
                    # 이미 존재하면 무시
                    pass
                
                logger.info(f"✅ Blob Storage 초기화 성공 (컨테이너: {self.container_name})")
            else:
                logger.warning("⚠️  Blob Storage 설정 없음 (선택사항)")
        
        except ImportError:
            logger.warning("⚠️  azure-storage-blob 패키지 없음")
        except Exception as e:
            logger.warning(f"⚠️  Blob Storage 초기화 실패: {e}")
    
    def save_session(
        self,
        user_id: str,
        session_type: str,
        data: Dict
    ) -> Optional[str]:
        """세션 데이터 저장"""
        
        if not self.blob_service_client:
            logger.warning("Blob Storage가 설정되지 않았습니다")
            return None
        
        try:
            # 파일명 생성
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            blob_name = f"{user_id}/{session_type}/{timestamp}.json"
            
            # 데이터 준비
            session_data = {
                "user_id": user_id,
                "session_type": session_type,
                "timestamp": datetime.now().isoformat(),
                "data": data
            }
            
            # JSON 변환
            json_data = json.dumps(session_data, ensure_ascii=False, indent=2)
            
            # 업로드
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            
            blob_client.upload_blob(json_data, overwrite=True)
            
            logger.info(f"✅ 세션 데이터 저장: {blob_name}")
            return blob_name
        
        except Exception as e:
            logger.error(f"❌ 세션 저장 실패: {e}")
            return None
    
    def save_qa_record(
        self,
        user_id: str,
        question: str,
        answer: str,
        evaluation: Dict
    ) -> Optional[str]:
        """질문/답변/평가 레코드 저장"""
        
        data = {
            "question": question,
            "answer": answer,
            "evaluation": evaluation,
            "timestamp": datetime.now().isoformat()
        }
        
        return self.save_session(user_id, "qa_records", data)
    
    def save_interview_session(
        self,
        user_id: str,
        qa_list: List[Dict],
        profile: Optional[Dict] = None
    ) -> Optional[str]:
        """면접 세션 전체 저장"""
        
        data = {
            "profile": profile,
            "qa_list": qa_list,
            "total_questions": len(qa_list),
            "average_score": sum(qa.get("evaluation", {}).get("total_score", 0) for qa in qa_list) / len(qa_list) if qa_list else 0
        }
        
        return self.save_session(user_id, "interview_sessions", data)
    
    def get_user_sessions(self, user_id: str, session_type: Optional[str] = None) -> List[str]:
        """사용자의 세션 목록 조회"""
        
        if not self.blob_service_client:
            return []
        
        try:
            container_client = self.blob_service_client.get_container_client(self.container_name)
            
            prefix = f"{user_id}/{session_type}/" if session_type else f"{user_id}/"
            
            blobs = container_client.list_blobs(name_starts_with=prefix)
            
            return [blob.name for blob in blobs]
        
        except Exception as e:
            logger.error(f"❌ 세션 목록 조회 실패: {e}")
            return []


class PDFReportGenerator:
    """PDF 면접 리포트 생성"""
    
    def __init__(self):
        """초기화"""
        pass
    
    def generate_interview_report(
        self,
        user_name: str,
        profile: Dict,
        qa_list: List[Dict],
        output_path: str
    ) -> Optional[str]:
        """면접 리포트 PDF 생성"""
        
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import cm
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
            from reportlab.lib import colors
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            
            # 한글 폰트 등록 (시스템에 따라 경로 변경 필요)
            try:
                # Windows
                pdfmetrics.registerFont(TTFont('Malgun', 'malgun.ttf'))
                font_name = 'Malgun'
            except:
                try:
                    # macOS
                    pdfmetrics.registerFont(TTFont('AppleGothic', '/System/Library/Fonts/AppleGothic.ttf'))
                    font_name = 'AppleGothic'
                except:
                    # Linux or fallback
                    try:
                        pdfmetrics.registerFont(TTFont('NanumGothic', '/usr/share/fonts/truetype/nanum/NanumGothic.ttf'))
                        font_name = 'NanumGothic'
                    except:
                        logger.warning("⚠️  한글 폰트를 찾을 수 없습니다. 기본 폰트 사용")
                        font_name = 'Helvetica'
            
            # PDF 문서 생성
            doc = SimpleDocTemplate(
                output_path,
                pagesize=A4,
                rightMargin=2*cm,
                leftMargin=2*cm,
                topMargin=2*cm,
                bottomMargin=2*cm
            )
            
            # 스타일 정의
            styles = getSampleStyleSheet()
            
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontName=font_name,
                fontSize=24,
                textColor=colors.HexColor('#1a237e'),
                spaceAfter=30,
                alignment=1  # 중앙 정렬
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontName=font_name,
                fontSize=16,
                textColor=colors.HexColor('#283593'),
                spaceAfter=12
            )
            
            body_style = ParagraphStyle(
                'CustomBody',
                parent=styles['BodyText'],
                fontName=font_name,
                fontSize=10,
                leading=14
            )
            
            # 문서 요소 리스트
            story = []
            
            # 제목
            story.append(Paragraph("🎓 반도체 공정 면접 분석 리포트", title_style))
            story.append(Spacer(1, 0.5*cm))
            
            # 기본 정보
            story.append(Paragraph("📋 기본 정보", heading_style))
            
            info_data = [
                ['이름', user_name],
                ['분석 일시', datetime.now().strftime("%Y년 %m월 %d일 %H:%M")],
                ['총 질문 수', str(len(qa_list))],
            ]
            
            if profile:
                info_data.append(['학력', profile.get('education', 'N/A')])
            
            info_table = Table(info_data, colWidths=[4*cm, 12*cm])
            info_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8eaf6')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), font_name),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey)
            ]))
            
            story.append(info_table)
            story.append(Spacer(1, 1*cm))
            
            # 종합 평가
            if qa_list:
                story.append(Paragraph("📊 종합 평가", heading_style))
                
                # 평균 점수 계산
                total_scores = []
                accuracy_scores = []
                depth_scores = []
                structure_scores = []
                application_scores = []
                communication_scores = []
                
                for qa in qa_list:
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
                
                summary_data = [
                    ['평가 항목', '평균 점수', '만점', '달성률'],
                    ['총점', f'{avg_total:.1f}', '100', f'{avg_total:.0f}%'],
                    ['정확성', f'{avg_accuracy:.1f}', '30', f'{avg_accuracy/30*100:.0f}%'],
                    ['깊이', f'{avg_depth:.1f}', '25', f'{avg_depth/25*100:.0f}%'],
                    ['구조', f'{avg_structure:.1f}', '20', f'{avg_structure/20*100:.0f}%'],
                    ['응용', f'{avg_application:.1f}', '15', f'{avg_application/15*100:.0f}%'],
                    ['의사소통', f'{avg_communication:.1f}', '10', f'{avg_communication/10*100:.0f}%'],
                ]
                
                summary_table = Table(summary_data, colWidths=[5*cm, 3*cm, 3*cm, 3*cm])
                summary_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3f51b5')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, -1), font_name),
                    ('FONTSIZE', (0, 0), (-1, 0), 11),
                    ('FONTSIZE', (0, 1), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                    ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#fffde7')),
                    ('GRID', (0, 0), (-1, -1), 1, colors.grey)
                ]))
                
                story.append(summary_table)
                story.append(Spacer(1, 1*cm))
            
            # 페이지 나누기
            story.append(PageBreak())
            
            # 질문별 상세 분석
            story.append(Paragraph("📝 질문별 상세 분석", heading_style))
            story.append(Spacer(1, 0.5*cm))
            
            for idx, qa in enumerate(qa_list, 1):
                # 질문
                story.append(Paragraph(f"<b>질문 {idx}</b>", body_style))
                story.append(Spacer(1, 0.2*cm))
                story.append(Paragraph(qa.get('question', 'N/A'), body_style))
                story.append(Spacer(1, 0.3*cm))
                
                # 답변
                story.append(Paragraph("<b>답변</b>", body_style))
                story.append(Spacer(1, 0.2*cm))
                answer_text = qa.get('answer', 'N/A')[:500]  # 길이 제한
                story.append(Paragraph(answer_text, body_style))
                story.append(Spacer(1, 0.3*cm))
                
                # 평가
                eval_data = qa.get('evaluation', {})
                if eval_data and 'total_score' in eval_data:
                    story.append(Paragraph(f"<b>점수: {eval_data['total_score']:.0f}/100</b>", body_style))
                    story.append(Spacer(1, 0.2*cm))
                    
                    # 강점
                    strengths = eval_data.get('strengths', [])
                    if strengths:
                        story.append(Paragraph("<b>💪 강점:</b>", body_style))
                        for strength in strengths[:3]:
                            story.append(Paragraph(f"  • {strength}", body_style))
                        story.append(Spacer(1, 0.2*cm))
                    
                    # 개선점
                    improvements = eval_data.get('improvements', [])
                    if improvements:
                        story.append(Paragraph("<b>📈 개선점:</b>", body_style))
                        for improvement in improvements[:3]:
                            story.append(Paragraph(f"  • {improvement}", body_style))
                        story.append(Spacer(1, 0.2*cm))
                
                story.append(Spacer(1, 0.5*cm))
                
                # 구분선
                if idx < len(qa_list):
                    story.append(Paragraph("─" * 80, body_style))
                    story.append(Spacer(1, 0.5*cm))
            
            # 종합 피드백
            story.append(PageBreak())
            story.append(Paragraph("💡 종합 피드백 및 학습 가이드", heading_style))
            story.append(Spacer(1, 0.5*cm))
            
            # 전체 강점 수집
            all_strengths = []
            all_improvements = []
            all_recommendations = []
            
            for qa in qa_list:
                eval_data = qa.get('evaluation', {})
                all_strengths.extend(eval_data.get('strengths', []))
                all_improvements.extend(eval_data.get('improvements', []))
                all_recommendations.extend(eval_data.get('recommended_topics', []))
            
            # 중복 제거
            unique_strengths = list(set(all_strengths))[:5]
            unique_improvements = list(set(all_improvements))[:5]
            unique_recommendations = list(set(all_recommendations))[:5]
            
            if unique_strengths:
                story.append(Paragraph("<b>✅ 주요 강점:</b>", body_style))
                for strength in unique_strengths:
                    story.append(Paragraph(f"  • {strength}", body_style))
                story.append(Spacer(1, 0.5*cm))
            
            if unique_improvements:
                story.append(Paragraph("<b>🎯 중점 개선 사항:</b>", body_style))
                for improvement in unique_improvements:
                    story.append(Paragraph(f"  • {improvement}", body_style))
                story.append(Spacer(1, 0.5*cm))
            
            if unique_recommendations:
                story.append(Paragraph("<b>📚 복습 추천 주제:</b>", body_style))
                for topic in unique_recommendations:
                    story.append(Paragraph(f"  • {topic}", body_style))
                story.append(Spacer(1, 0.5*cm))
            
            # PDF 생성
            doc.build(story)
            
            logger.info(f"✅ PDF 리포트 생성 완료: {output_path}")
            return output_path
        
        except ImportError:
            logger.error("❌ reportlab 패키지가 설치되지 않았습니다")
            logger.info("설치: pip install reportlab")
            return None
        
        except Exception as e:
            logger.error(f"❌ PDF 생성 실패: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return None


# 싱글톤 인스턴스
storage_manager = DataStorageManager()
pdf_generator = PDFReportGenerator()
