# services/kpi_service.py

from database import get_db
from models.kpi import Evaluation, Question, Answer, EvaluationPeriod, EvaluationStatus
from services.user_service import UserService
from services.notification_service import NotificationService
from typing import List

class KpiService:
    @staticmethod
    def calculate_evaluation_score(evaluation_id):
        """
        Hər bir qiymətləndirmə (Evaluation) üçün yekun balı hesablayır.
        
        Formula:
        Yekun Bal = (Σ (cavab.score * sual.weight)) / (Σ sual.weight)
        
        Args:
            evaluation_id (int): Qiymətləndirmənin ID-si.
            
        Returns:
            float: Yekun bal. Əgər qiymətləndirmə tapılmazsa və ya sual yoxdursa, 0.0 qaytarır.
        """
        with get_db() as session:
            # Qiymətləndirməni əldə edirik
            evaluation = session.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
            if not evaluation:
                return 0.0
            
            # Qiymətləndirməyə aid cavabları və sualları əldə edirik
            answers = session.query(Answer).filter(Answer.evaluation_id == evaluation_id).all()
            if not answers:
                return 0.0
                
            total_weighted_score = 0.0
            total_weight = 0.0
            
            for answer in answers:
                question = session.query(Question).filter(Question.id == answer.question_id).first()
                if question:
                    total_weighted_score += answer.score * question.weight
                    total_weight += question.weight
                    
            if total_weight == 0:
                return 0.0
                
            return total_weighted_score / total_weight

    @staticmethod
    def update_evaluation_status(evaluation_id, new_status):
        """
        Qiymətləndirmənin statusunu yeniləyir və tərəflərə bildiriş göndərir.
        
        Args:
            evaluation_id (int): Qiymətləndirmənin ID-si.
            new_status (EvaluationStatus): Yeni status.
        """
        with get_db() as session:
            evaluation = session.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
            if evaluation:
                old_status = evaluation.status
                evaluation.status = new_status
                session.commit()
                
                # Bildiriş göndərmək
                if new_status == EvaluationStatus.SELF_EVAL_COMPLETED:
                    # Rəhbərə bildiriş göndər
                    manager = UserService.get_user_by_id(evaluation.evaluator_user_id)
                    if manager and manager.id != evaluation.evaluated_user_id:
                        NotificationService.create_notification(
                            user_id=manager.id,
                            message=f"{evaluation.evaluated_user.get_full_name()} özünü qiymətləndirdi. Zəhmət olmasa, nəzərdən keçirin."
                        )
                elif new_status == EvaluationStatus.FINALIZED:
                    # İşçiyə bildiriş göndər
                    employee = UserService.get_user_by_id(evaluation.evaluated_user_id)
                    if employee:
                        NotificationService.create_notification(
                            user_id=employee.id,
                            message=f"{evaluation.period.name} qiymətləndirməniz yekunlaşdırıldı."
                        )

    @staticmethod
    def get_user_performance_data(period_id, department=None):
        """
        Verilmiş dövr üçün istifadəçilərin performans məlumatlarını əldə edir.
        Yalnız FINALIZED statuslu qiymətləndirmələri nəzərə alır.
        
        Args:
            period_id (int): Qiymətləndirmə dövrünün ID-si.
            department (str, optional): Şöbə. Əgər verilməzsə, bütün şöbələr üçün məlumat qaytarılır.
            
        Returns:
            list: Hər bir istifadəçi üçün əməkdaş adı, şöbə və yekun bal siyahısı.
        """
        performance_data = []
        
        with get_db() as session:
            # Qiymətləndirmə dövrünə aid FINALIZED qiymətləndirmələri əldə edirik
            evaluations = session.query(Evaluation).filter(
                Evaluation.period_id == period_id,
                Evaluation.status == EvaluationStatus.FINALIZED
            ).all()
            
            user_scores = {}
            user_departments = {}
            
            for evaluation in evaluations:
                score = KpiService.calculate_evaluation_score(evaluation.id)
                user_id = evaluation.evaluated_user_id
                
                if user_id not in user_scores:
                    user_scores[user_id] = []
                user_scores[user_id].append(score)
                
                # İstifadəçinin şöbəsini əldə edirik (əgər yoxdursa, None olacaq)
                if user_id not in user_departments:
                    profile = UserService.get_user_profile_by_user_id(user_id)
                    user_departments[user_id] = profile.department if profile else None
                    
            # Hər bir istifadəçi üçün orta balı hesablayırıq
            for user_id, scores in user_scores.items():
                if scores:
                    avg_score = sum(scores) / len(scores)
                    user = UserService.get_user_by_id(user_id)
                    full_name = user.get_full_name() if user else "Naməlum"
                    department_name = user_departments.get(user_id)
                    
                    # Əgər şöbə filtr varsa və istifadəçi həmin şöbədə deyilsə, əlavə etmirik
                    if department and department_name != department:
                        continue
                        
                    performance_data.append({
                        "full_name": full_name,
                        "department": department_name,
                        "total_score": avg_score
                    })
                    
        return performance_data

    @staticmethod
    def get_department_performance_data(period_id):
        """
        Verilmiş dövr üçün şöbələrin orta performans məlumatlarını əldə edir.
        Yalnız FINALIZED statuslu qiymətləndirmələri nəzərə alır.
        
        Args:
            period_id (int): Qiymətləndirmə dövrünün ID-si.
            
        Returns:
            list: Hər bir şöbə üçün adı və orta bal siyahısı.
        """
        department_data = []
        
        with get_db() as session:
            # Qiymətləndirmə dövrünə aid FINALIZED qiymətləndirmələri əldə edirik
            evaluations = session.query(Evaluation).filter(
                Evaluation.period_id == period_id,
                Evaluation.status == EvaluationStatus.FINALIZED
            ).all()
            
            dept_scores = {}
            
            for evaluation in evaluations:
                score = KpiService.calculate_evaluation_score(evaluation.id)
                user_id = evaluation.evaluated_user_id
                
                # İstifadəçinin şöbəsini əldə edirik
                profile = UserService.get_user_profile_by_user_id(user_id)
                department_name = profile.department if profile else "Naməlum"
                
                if department_name not in dept_scores:
                    dept_scores[department_name] = []
                dept_scores[department_name].append(score)
                    
            # Hər bir şöbə üçün orta balı hesablayırıq
            for dept_name, scores in dept_scores.items():
                if scores:
                    avg_score = sum(scores) / len(scores)
                    department_data.append({
                        "department": dept_name,
                        "avg_score": avg_score
                    })
                    
        return department_data

    @staticmethod
    def get_user_performance_trend(user_id):
        """
        Verilmiş istifadəçi üçün performans trendini əldə edir.
        Yalnız FINALIZED statuslu qiymətləndirmələri nəzərə alır.
        
        Args:
            user_id (int): İstifadəçinin ID-si.
            
        Returns:
            list: Hər bir qiymətləndirmə dövrü üçün dövr adı və yekun bal siyahısı.
        """
        trend_data = []
        
        with get_db() as session:
            # İstifadəçinin qiymətləndirildiyi FINALIZED qiymətləndirmələri əldə edirik
            evaluations = session.query(Evaluation).filter(
                Evaluation.evaluated_user_id == user_id,
                Evaluation.status == EvaluationStatus.FINALIZED
            ).order_by(Evaluation.period_id).all()
            
            for evaluation in evaluations:
                score = KpiService.calculate_evaluation_score(evaluation.id)
                period_name = evaluation.period.name
                
                trend_data.append({
                    "period_name": period_name,
                    "score": score
                })
                    
        return trend_data

    @staticmethod
    def get_all_evaluation_periods():
        """Bütün qiymətləndirmə dövrlərini əldə edir."""
        with get_db() as session:
            return session.query(EvaluationPeriod).order_by(EvaluationPeriod.start_date.desc()).all()

    @staticmethod
    def get_evaluation_period_by_id(period_id):
        """Qiymətləndirmə dövrünü ID-sinə görə əldə edir."""
        with get_db() as session:
            return session.query(EvaluationPeriod).filter(EvaluationPeriod.id == period_id).first()

    @staticmethod
    def get_pending_evaluations_for_user(user_id):
        """İstifadəçinin tamamlanmamış qiymətləndirmələrini əldə edir."""
        with get_db() as session:
            return session.query(Evaluation).filter(
                Evaluation.evaluator_user_id == user_id,
                Evaluation.status == EvaluationStatus.PENDING
            ).all()

    @staticmethod
    def get_completed_evaluations_for_user(user_id):
        """
        İstifadəçinin tamamlanmış qiymətləndirmələrini əldə edir.
        Burada "tamamlanmış" ifadəsi FINALIZED statusu ilə bağlıdır.
        """
        with get_db() as session:
            return session.query(Evaluation).filter(
                Evaluation.evaluator_user_id == user_id,
                Evaluation.status == EvaluationStatus.FINALIZED
            ).all()
            
    @staticmethod
    def get_self_eval_completed_evaluations_for_manager(manager_id):
        """
        Menecer üçün SELF_EVAL_COMPLETED statuslu qiymətləndirmələri əldə edir.
        """
        with get_db() as session:
            return session.query(Evaluation).filter(
                Evaluation.evaluator_user_id == manager_id,
                Evaluation.status == EvaluationStatus.SELF_EVAL_COMPLETED
            ).all()
            
    @staticmethod
    def get_multiple_periods_performance_data(period_ids: List[int]):
        """
        Birdən çox qiymətləndirmə dövrünün nəticələrini eyni anda qaytaran servis funksiyası.
        
        Args:
            period_ids (List[int]): Qiymətləndirmə dövrlərinin ID-ləri.
            
        Returns:
            dict: Hər bir dövr üçün əməkdaş adı, şöbə və yekun bal siyahısı.
        """
        performance_comparison = {}
        
        with get_db() as session:
            for period_id in period_ids:
                period = session.query(EvaluationPeriod).filter(EvaluationPeriod.id == period_id).first()
                if period:
                    # Qiymətləndirmə dövrünə aid FINALIZED qiymətləndirmələri əldə edirik
                    evaluations = session.query(Evaluation).filter(
                        Evaluation.period_id == period_id,
                        Evaluation.status == EvaluationStatus.FINALIZED
                    ).all()
                    
                    user_scores = {}
                    user_departments = {}
                    
                    for evaluation in evaluations:
                        score = KpiService.calculate_evaluation_score(evaluation.id)
                        user_id = evaluation.evaluated_user_id
                        
                        if user_id not in user_scores:
                            user_scores[user_id] = []
                        user_scores[user_id].append(score)
                        
                        # İstifadəçinin şöbəsini əldə edirik (əgər yoxdursa, None olacaq)
                        if user_id not in user_departments:
                            profile = UserService.get_user_profile_by_user_id(user_id)
                            user_departments[user_id] = profile.department if profile else None
                    
                    # Hər bir istifadəçi üçün orta balı hesablayırıq
                    period_data = []
                    for user_id, scores in user_scores.items():
                        if scores:
                            avg_score = sum(scores) / len(scores)
                            user = UserService.get_user_by_id(user_id)
                            full_name = user.get_full_name() if user else "Naməlum"
                            department_name = user_departments.get(user_id)
                            
                            period_data.append({
                                "full_name": full_name,
                                "department": department_name,
                                "total_score": avg_score
                            })
                    
                    performance_comparison[period.name] = period_data
                    
        return performance_comparison

    @staticmethod
    def submit_evaluation(evaluation_id: int, user_id: int, answers: dict):
        """
        Qiymətləndirməni təsdiqləyir və statusu yeniləyir.
        
        Args:
            evaluation_id (int): Qiymətləndirmənin ID-si
            user_id (int): İstifadəçinin ID-si
            answers (dict): Cavablar sözlüğü (sual_id: {"score": int, "comment": str})
        """
        with get_db() as session:
            # Qiymətləndirməni əldə edirik
            evaluation = session.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
            if not evaluation:
                raise ValueError("Qiymətləndirmə tapılmadı")
            
            # İstifadəçinin qiymətləndirməyə icazəsi olub-olmadığını yoxlayırıq
            if evaluation.evaluator_user_id != user_id:
                raise PermissionError("Bu qiymətləndirməyə icazəniz yoxdur")
            
            # İstifadəçinin rolu (əməkdaş və ya rəhbər)
            is_employee = evaluation.evaluated_user_id == user_id
            is_manager = evaluation.evaluator_user_id == user_id and evaluation.evaluated_user_id != user_id
            
            # Mövcud cavabları silirik
            session.query(Answer).filter(Answer.evaluation_id == evaluation_id).delete()
            
            # Yeni cavabları əlavə edirik
            for question_id, answer_data in answers.items():
                author_role = 'employee' if is_employee else 'manager'
                new_answer = Answer(
                    evaluation_id=evaluation_id,
                    question_id=question_id,
                    score=answer_data['score'],
                    comment=answer_data.get('comment'),
                    author_role=author_role
                )
                session.add(new_answer)
            
            # Statusu yeniləyirik
            if is_employee:
                # Əgər işçi özünü qiymətləndirirsə
                evaluation.status = EvaluationStatus.SELF_EVAL_COMPLETED
                # Rəhbərə bildiriş göndəririk
                manager = UserService.get_user_by_id(evaluation.evaluator_user_id)
                if manager and manager.id != evaluation.evaluated_user_id:
                    NotificationService.create_notification(
                        user_id=manager.id,
                        message=f"{evaluation.evaluated_user.get_full_name()} özünü qiymətləndirdi. Zəhmət olmasa, nəzərdən keçirin."
                    )
            elif is_manager:
                # Əgər rəhbər qiymətləndirirsə
                evaluation.status = EvaluationStatus.FINALIZED
                # İşçiyə bildiriş göndəririk
                employee = UserService.get_user_by_id(evaluation.evaluated_user_id)
                if employee:
                    NotificationService.create_notification(
                        user_id=employee.id,
                        message=f"{evaluation.period.name} qiymətləndirməniz yekunlaşdırıldı."
                    )
            
            session.commit()