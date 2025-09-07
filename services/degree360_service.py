# services/degree360_service.py

from database import get_db
from models.degree360 import (
    Degree360Session, 
    Degree360Participant, 
    Degree360Question, 
    Degree360Answer,
    Degree360ParticipantRole
)
from models.user import User
from services.notification_service import NotificationService
from datetime import date, datetime
from typing import List, Dict, Any

class Degree360Service:
    @staticmethod
    def create_360_session(
        name: str,
        evaluated_user_id: int,
        evaluator_user_id: int,
        start_date: date,
        end_date: date,
        is_anonymous: bool = True
    ) -> Degree360Session:
        """
        Yeni 360 dərəcə qiymətləndirmə sessiyası yaradır.
        
        Args:
            name (str): Sessiyanın adı
            evaluated_user_id (int): Qiymətləndiriləcək istifadəçinin ID-si
            evaluator_user_id (int): Sessiyanı yaradan rəhbərin ID-si
            start_date (date): Başlama tarixi
            end_date (date): Bitmə tarixi
            is_anonymous (bool): Anonimlik parametri
            
        Returns:
            Degree360Session: Yaradılmış sessiya obyekti
        """
        with get_db() as session:
            new_session = Degree360Session(
                name=name,
                evaluated_user_id=evaluated_user_id,
                evaluator_user_id=evaluator_user_id,
                start_date=start_date,
                end_date=end_date,
                is_anonymous=is_anonymous,
                status="ACTIVE"
            )
            session.add(new_session)
            session.commit()
            session.refresh(new_session)
            
            # Qiymətləndiriləcək işçiyə bildiriş göndər
            evaluated_user = session.query(User).filter(User.id == evaluated_user_id).first()
            if evaluated_user:
                NotificationService.create_notification(
                    user_id=evaluated_user_id,
                    message=f"Yeni 360° qiymətləndirmə sessiyası yaradıldı: {name}"
                )
            
            return new_session

    @staticmethod
    def get_360_session_by_id(session_id: int) -> Degree360Session:
        """
        ID-sinə görə 360 dərəcə qiymətləndirmə sessiyasını qaytarır.
        
        Args:
            session_id (int): Sessiyanın ID-si
            
        Returns:
            Degree360Session: Sessiya obyekti və ya None əgər tapılmazsa
        """
        with get_db() as session:
            return session.query(Degree360Session).filter(Degree360Session.id == session_id).first()

    @staticmethod
    def get_360_sessions_for_user(user_id: int) -> List[Degree360Session]:
        """
        İstifadəçinin bütün 360 dərəcə qiymətləndirmə sessiyalarını qaytarır.
        Həm qiymətləndiriləcək şəxs kimi, həm də rəhbər kimi olan sessiyaları əhatə edir.
        
        Args:
            user_id (int): İstifadəçinin ID-si
            
        Returns:
            List[Degree360Session]: Sessiyalar siyahısı
        """
        with get_db() as session:
            return session.query(Degree360Session).filter(
                (Degree360Session.evaluated_user_id == user_id) | 
                (Degree360Session.evaluator_user_id == user_id)
            ).all()

    @staticmethod
    def add_participant_to_360_session(
        session_id: int,
        evaluator_user_id: int,
        role: Degree360ParticipantRole
    ) -> Degree360Participant:
        """
        360 dərəcə qiymətləndirmə sessiyasına iştirakçı əlavə edir.
        
        Args:
            session_id (int): Sessiyanın ID-si
            evaluator_user_id (int): Qiymətləndirən istifadəçinin ID-si
            role (Degree360ParticipantRole): Qiymətləndiricinin rolu
            
        Returns:
            Degree360Participant: Əlavə edilmiş iştirakçı obyekti
        """
        with get_db() as session:
            participant = Degree360Participant(
                session_id=session_id,
                evaluator_user_id=evaluator_user_id,
                role=role,
                status="PENDING"
            )
            session.add(participant)
            session.commit()
            session.refresh(participant)
            return participant

    @staticmethod
    def get_participants_for_360_session(session_id: int) -> List[Degree360Participant]:
        """
        360 dərəcə qiymətləndirmə sessiyasının bütün iştirakçılarını qaytarır.
        
        Args:
            session_id (int): Sessiyanın ID-si
            
        Returns:
            List[Degree360Participant]: İştirakçılar siyahısı
        """
        with get_db() as session:
            return session.query(Degree360Participant).filter(
                Degree360Participant.session_id == session_id
            ).all()

    @staticmethod
    def add_question_to_360_session(
        session_id: int,
        text: str,
        category: str = "Ümumi",
        weight: int = 1
    ) -> Degree360Question:
        """
        360 dərəcə qiymətləndirmə sessiyasına sual əlavə edir.
        
        Args:
            session_id (int): Sessiyanın ID-si
            text (str): Sualın mətni
            category (str): Kateqoriya
            weight (int): Sualın çəkisi (1-5)
            
        Returns:
            Degree360Question: Əlavə edilmiş sual obyekti
        """
        with get_db() as session:
            question = Degree360Question(
                session_id=session_id,
                text=text,
                category=category,
                weight=weight,
                is_active=True
            )
            session.add(question)
            session.commit()
            session.refresh(question)
            return question

    @staticmethod
    def get_questions_for_360_session(session_id: int) -> List[Degree360Question]:
        """
        360 dərəcə qiymətləndirmə sessiyasının bütün suallarını qaytarır.
        
        Args:
            session_id (int): Sessiyanın ID-si
            
        Returns:
            List[Degree360Question]: Suallar siyahısı
        """
        with get_db() as session:
            return session.query(Degree360Question).filter(
                Degree360Question.session_id == session_id,
                Degree360Question.is_active == True
            ).all()

    @staticmethod
    def submit_answers_for_360_participant(
        participant_id: int,
        answers: List[Dict[str, Any]]
    ) -> None:
        """
        360 dərəcə qiymətləndirmə iştirakçısı üçün cavabları təsdiqləyir.
        
        Args:
            participant_id (int): İştirakçının ID-si
            answers (List[Dict[str, Any]]): Cavablar siyahısı. Hər bir cavab aşağıdakı formada olmalıdır:
                {
                    "question_id": int,
                    "score": int (1-5),
                    "comment": str (vacib deyil)
                }
        """
        with get_db() as session:
            # Mövcud cavabları sil
            session.query(Degree360Answer).filter(
                Degree360Answer.participant_id == participant_id
            ).delete()
            
            # Yeni cavabları əlavə et
            for answer_data in answers:
                answer = Degree360Answer(
                    participant_id=participant_id,
                    question_id=answer_data["question_id"],
                    score=answer_data["score"],
                    comment=answer_data.get("comment")
                )
                session.add(answer)
            
            # İştirakçının statusunu "COMPLETED" et
            participant = session.query(Degree360Participant).filter(
                Degree360Participant.id == participant_id
            ).first()
            if participant:
                participant.status = "COMPLETED"
                
                # Qiymətləndirmə sessiyasını əldə et
                degree360_session = session.query(Degree360Session).filter(
                    Degree360Session.id == participant.session_id
                ).first()
                
                # Qiymətləndiriləcək işçiyə bildiriş göndər
                if degree360_session:
                    evaluated_user = session.query(User).filter(
                        User.id == degree360_session.evaluated_user_id
                    ).first()
                    evaluator_user = session.query(User).filter(
                        User.id == participant.evaluator_user_id
                    ).first()
                    
                    if evaluated_user and evaluator_user:
                        NotificationService.create_notification(
                            user_id=degree360_session.evaluated_user_id,
                            message=f"{evaluator_user.get_full_name()} 360° qiymətləndirmə sessiyasında rəy bildirdi: {degree360_session.name}"
                        )
            
            session.commit()

    @staticmethod
    def get_answers_for_360_participant(participant_id: int) -> List[Degree360Answer]:
        """
        360 dərəcə qiymətləndirmə iştirakçısının cavablarını qaytarır.
        
        Args:
            participant_id (int): İştirakçının ID-si
            
        Returns:
            List[Degree360Answer]: Cavablar siyahısı
        """
        with get_db() as session:
            return session.query(Degree360Answer).filter(
                Degree360Answer.participant_id == participant_id
            ).all()

    @staticmethod
    def calculate_360_session_results(session_id: int) -> Dict[str, Any]:
        """
        360 dərəcə qiymətləndirmə sessiyasının nəticələrini hesablayır.
        
        Args:
            session_id (int): Sessiyanın ID-si
            
        Returns:
            Dict[str, Any]: Nəticələr. Aşağıdakı formada olur:
                {
                    "evaluated_user": str,  # Qiymətləndirilən istifadəçinin adı
                    "overall_score": float,  # Ümumi bal (0-5)
                    "scores_by_role": Dict[str, float],  # Rol üzrə ballar
                    "detailed_results": List[Dict]  # Hər bir sual üzrə ətraflı nəticələr
                }
        """
        with get_db() as session:
            # Sessiyanı əldə et
            degree360_session = session.query(Degree360Session).filter(
                Degree360Session.id == session_id
            ).first()
            
            if not degree360_session:
                return {}
            
            # Qiymətləndirilən istifadəçinin adını əldə et
            evaluated_user = session.query(User).filter(
                User.id == degree360_session.evaluated_user_id
            ).first()
            evaluated_user_name = evaluated_user.get_full_name() if evaluated_user else "Naməlum"
            
            # Bütün iştirakçıları əldə et
            participants = session.query(Degree360Participant).filter(
                Degree360Participant.session_id == session_id,
                Degree360Participant.status == "COMPLETED"
            ).all()
            
            if not participants:
                return {
                    "evaluated_user": evaluated_user_name,
                    "overall_score": 0.0,
                    "scores_by_role": {},
                    "detailed_results": []
                }
            
            # Bütün sualları əldə et
            questions = session.query(Degree360Question).filter(
                Degree360Question.session_id == session_id,
                Degree360Question.is_active == True
            ).all()
            
            question_scores = {}
            role_scores = {}
            
            # Hər bir sual üçün qiymətləndirmələri topla
            for question in questions:
                question_scores[question.id] = {
                    "text": question.text,
                    "category": question.category,
                    "weight": question.weight,
                    "scores_by_role": {},
                    "average_score": 0.0
                }
            
            # Hər bir iştirakçı üçün cavabları topla
            for participant in participants:
                # İştirakçının rolu
                role = participant.role.value
                
                # Bu rola görə qiymətləndirmə sayı
                if role not in role_scores:
                    role_scores[role] = {"total_score": 0.0, "count": 0}
                
                # İştirakçının cavablarını əldə et
                answers = session.query(Degree360Answer).filter(
                    Degree360Answer.participant_id == participant.id
                ).all()
                
                # Hər bir cavabı topla
                for answer in answers:
                    question_id = answer.question_id
                    score = answer.score
                    
                    # Sual üzrə qiymətləri topla
                    if question_id in question_scores:
                        if role not in question_scores[question_id]["scores_by_role"]:
                            question_scores[question_id]["scores_by_role"][role] = {
                                "total_score": 0.0,
                                "count": 0
                            }
                        
                        question_scores[question_id]["scores_by_role"][role]["total_score"] += score
                        question_scores[question_id]["scores_by_role"][role]["count"] += 1
                        
                        # Ümumi qiymətləri topla
                        role_scores[role]["total_score"] += score
                        role_scores[role]["count"] += 1
            
            # Hesablamaları tamamla
            detailed_results = []
            overall_total_score = 0.0
            overall_count = 0
            
            for question_id, data in question_scores.items():
                # Hər bir sual üzrə orta qiyməti hesabla
                question_total_score = 0.0
                question_count = 0
                
                for role, role_data in data["scores_by_role"].items():
                    role_average = role_data["total_score"] / role_data["count"] if role_data["count"] > 0 else 0
                    data["scores_by_role"][role]["average_score"] = role_average
                    
                    question_total_score += role_data["total_score"]
                    question_count += role_data["count"]
                
                question_average = question_total_score / question_count if question_count > 0 else 0
                data["average_score"] = question_average
                
                detailed_results.append({
                    "question": data["text"],
                    "category": data["category"],
                    "weight": data["weight"],
                    "average_score": round(question_average, 2),
                    "scores_by_role": {
                        role: round(role_data["average_score"], 2) 
                        for role, role_data in data["scores_by_role"].items()
                    }
                })
                
                overall_total_score += question_total_score
                overall_count += question_count
            
            # Ümumi orta qiyməti hesabla
            overall_average = overall_total_score / overall_count if overall_count > 0 else 0.0
            
            # Rol üzrə orta qiymətləri hesabla
            roles_average = {}
            for role, role_data in role_scores.items():
                role_average = role_data["total_score"] / role_data["count"] if role_data["count"] > 0 else 0
                roles_average[role] = round(role_average, 2)
            
            return {
                "evaluated_user": evaluated_user_name,
                "overall_score": round(overall_average, 2),
                "scores_by_role": roles_average,
                "detailed_results": detailed_results
            }

    @staticmethod
    def get_pending_360_evaluations_for_user(user_id: int) -> List[Dict[str, Any]]:
        """
        İstifadəçinin tamamlanmamış 360 dərəcə qiymətləndirmələrini qaytarır.
        
        Args:
            user_id (int): İstifadəçinin ID-si
            
        Returns:
            List[Dict[str, Any]]: Tamamlanmamış qiymətləndirmələr siyahısı
        """
        pending_evaluations = []
        
        with get_db() as session:
            # İstifadəçinin iştirakçı olduğu, lakin hələ tamamlamadığı sessiyaları əldə edirik
            participants = session.query(Degree360Participant).filter(
                Degree360Participant.evaluator_user_id == user_id,
                Degree360Participant.status == "PENDING"
            ).all()
            
            for participant in participants:
                degree360_session = session.query(Degree360Session).filter(
                    Degree360Session.id == participant.session_id
                ).first()
                
                if degree360_session and degree360_session.status == "ACTIVE":
                    evaluated_user = session.query(User).filter(
                        User.id == degree360_session.evaluated_user_id
                    ).first()
                    
                    pending_evaluations.append({
                        "session_id": degree360_session.id,
                        "session_name": degree360_session.name,
                        "evaluated_user": evaluated_user.get_full_name() if evaluated_user else "Naməlum",
                        "role": participant.role.value,
                        "end_date": degree360_session.end_date.strftime("%d.%m.%Y")
                    })
            
            return pending_evaluations
            
    @staticmethod
    def send_360_reminders() -> None:
        """
        360 dərəcə qiymətləndirmələr üçün xatırlatma bildirişləri göndərir.
        Bitmə tarixinə 3 gün qalmış iştirakçılara xatırlatma göndərilir.
        """
        from datetime import timedelta
        
        with get_db() as session:
            # Bitmə tarixinə 3 gün qalmış aktiv sessiyaları tap
            reminder_date = date.today() + timedelta(days=3)
            
            sessions = session.query(Degree360Session).filter(
                Degree360Session.status == "ACTIVE",
                Degree360Session.end_date == reminder_date
            ).all()
            
            for degree360_session in sessions:
                # Hələ tamamlamamış iştirakçıları tap
                participants = session.query(Degree360Participant).filter(
                    Degree360Participant.session_id == degree360_session.id,
                    Degree360Participant.status == "PENDING"
                ).all()
                
                for participant in participants:
                    evaluator_user = session.query(User).filter(
                        User.id == participant.evaluator_user_id
                    ).first()
                    
                    if evaluator_user:
                        NotificationService.create_notification(
                            user_id=participant.evaluator_user_id,
                            message=f"Xatırlatma: {degree360_session.name} 360° qiymətləndirmə sessiyasının bitməsinə 3 gün qalıb. Zəhmət olmasa, rəyinizi bildirin."
                        )
                        
    @staticmethod
    def get_all_active_360_sessions() -> List[Degree360Session]:
        """
        Bütün aktiv 360 dərəcə qiymətləndirmə sessiyalarını qaytarır.
        
        Returns:
            List[Degree360Session]: Aktiv sessiyalar siyahısı
        """
        with get_db() as session:
            return session.query(Degree360Session).filter(
                Degree360Session.status == "ACTIVE"
            ).all()
            
    @staticmethod
    def generate_360_report(session_id: int) -> Dict[str, Any]:
        """
        360 dərəcə qiymətləndirmə üçün PDF hesabat generasiya edir.
        
        Args:
            session_id (int): Sessiyanın ID-si
            
        Returns:
            Dict[str, Any]: Hesabat məlumatları və statistikalar
        """
        # Əsas nəticələri əldə edirik
        results = Degree360Service.calculate_360_session_results(session_id)
        
        if not results:
            return {}
            
        with get_db() as session:
            # Sessiyanı əldə et
            degree360_session = session.query(Degree360Session).filter(
                Degree360Session.id == session_id
            ).first()
            
            if not degree360_session:
                return {}
                
            # Güclü və zəif tərəfləri müəyyən etmək üçün analiz
            strengths = []
            weaknesses = []
            
            for result in results.get("detailed_results", []):
                avg_score = result.get("average_score", 0)
                # 4.0 və yuxarı bal güclü tərəf kimi qəbul edilir
                if avg_score >= 4.0:
                    strengths.append({
                        "question": result["question"],
                        "category": result["category"],
                        "score": avg_score
                    })
                # 2.5 və aşağı bal zəif tərəf kimi qəbul edilir
                elif avg_score <= 2.5:
                    weaknesses.append({
                        "question": result["question"],
                        "category": result["category"],
                        "score": avg_score
                    })
            
            # Öz və başqalarının qiyməti arasındakı fərq analizi (gap analysis)
            gap_analysis = []
            detailed_results = results.get("detailed_results", [])
            
            for result in detailed_results:
                scores_by_role = result.get("scores_by_role", {})
                if scores_by_role:
                    # Öz qiymətləndirməsi və digər rolların qiymətləndirmələri arasında fərq
                    self_score = scores_by_role.get("Özünü qiymətləndirən", 0)
                    other_scores = [score for role, score in scores_by_role.items() if role != "Özünü qiymətləndirən"]
                    
                    if other_scores and self_score > 0:
                        avg_other_score = sum(other_scores) / len(other_scores)
                        gap = avg_other_score - self_score
                        
                        gap_analysis.append({
                            "question": result["question"],
                            "category": result["category"],
                            "self_score": self_score,
                            "others_avg_score": round(avg_other_score, 2),
                            "gap": round(gap, 2),
                            "interpretation": "Özünü qiymətləndirməsi aşağıdır" if gap > 0.5 else 
                                            "Özünü qiymətləndirməsi yüksəkdir" if gap < -0.5 else 
                                            "Uyğundur"
                        })
            
            # Hesabat məlumatlarını hazırlayırıq
            report_data = {
                "session_name": degree360_session.name,
                "evaluated_user": results.get("evaluated_user", "Naməlum"),
                "generated_date": datetime.now().strftime("%d.%m.%Y %H:%M"),
                "overall_score": results.get("overall_score", 0),
                "scores_by_role": results.get("scores_by_role", {}),
                "strengths": strengths,
                "weaknesses": weaknesses,
                "gap_analysis": gap_analysis,
                "detailed_results": detailed_results
            }
            
            return report_data