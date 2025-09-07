# pages/5_qiymetlendirme_formu.py

import streamlit as st
from database import get_db
from models.kpi import Evaluation, Question, Answer, EvaluationStatus
from models.user import User
from services.kpi_service import KpiService

st.set_page_config(layout="centered", page_title="Qiymətləndirmə Formu")

if 'user_id' not in st.session_state:
    st.warning("Bu səhifəyə baxmaq üçün sistemə daxil olmalısınız.")
    st.link_button("Giriş səhifəsi", "/")
    st.stop()

try:
    evaluation_id = int(st.query_params.get("evaluation_id"))
except (ValueError, TypeError):
    st.error("Səhv sorğu. Qiymətləndirmə tapılmadı.")
    st.stop()

with get_db() as session:
    evaluation = session.query(Evaluation).get(evaluation_id)
    
    if not evaluation or evaluation.evaluator_user_id != st.session_state['user_id']:
        st.error("Bu qiymətləndirməyə icazəniz yoxdur və ya tapılmadı.")
        st.stop()
    
    # Qiymətləndirmənin cari statusuna görə müvafiq mesaj göstər
    if evaluation.status == EvaluationStatus.FINALIZED:
        st.success("Bu qiymətləndirmə yekunlaşdırılıb.")
        
        # Yekun hesabatı göstər
        st.subheader("Yekun Hesabat")
        
        # İşçinin cavablarını göstər
        st.markdown("### İşçinin Cavabları")
        employee_answers = session.query(Answer).filter(
            Answer.evaluation_id == evaluation.id,
            Answer.author_role == 'employee'
        ).all()
        
        questions = session.query(Question).filter(Question.is_active == True).all()
        question_dict = {q.id: q for q in questions}
        
        for i, answer in enumerate(employee_answers, 1):
            question = question_dict.get(answer.question_id)
            if question:
                st.subheader(f"{i}. {question.text}")
                st.caption(f"Kateqoriya: {question.category}")
                st.write(f"Bal: {answer.score}/5")
                if answer.comment:
                    st.write(f"Şərh: {answer.comment}")
                st.markdown("---")
        
        # Rəhbərin cavablarını göstər
        st.markdown("### Rəhbərin Cavabları")
        manager_answers = session.query(Answer).filter(
            Answer.evaluation_id == evaluation.id,
            Answer.author_role == 'manager'
        ).all()
        
        for i, answer in enumerate(manager_answers, 1):
            question = question_dict.get(answer.question_id)
            if question:
                st.subheader(f"{i}. {question.text}")
                st.caption(f"Kateqoriya: {question.category}")
                st.write(f"Bal: {answer.score}/5")
                if answer.comment:
                    st.write(f"Şərh: {answer.comment}")
                st.markdown("---")
        
        if st.button("Tapşırıqlar Səhifəsinə Qayıt"):
            st.switch_page("pages/7_kpi_tapşırıqlarım.py")
        st.stop()
        
    elif evaluation.status == EvaluationStatus.SELF_EVAL_COMPLETED:
        # Rəhbər üçün işçi cavablarını göstər və öz cavablarını daxil et
        st.info("Bu qiymətləndirmə işçi tərəfindən dəyərləndirilib. Zəhmət olmasa, öz qiymətləndirmənizi daxil edin.")
        
        evaluated_user = evaluation.evaluated_user
        
        st.title("Qiymətləndirmə Formu")
        st.info(f"**Qiymətləndirilən:** {evaluated_user.get_full_name()} | **Dövr:** {evaluation.period.name}")
        st.markdown("---")
        
        # İşçinin cavablarını göstər
        st.subheader("İşçinin Cavabları")
        employee_answers = session.query(Answer).filter(
            Answer.evaluation_id == evaluation.id,
            Answer.author_role == 'employee'
        ).all()
        
        questions = session.query(Question).filter(Question.is_active == True).all()
        question_dict = {q.id: q for q in questions}
        
        for i, answer in enumerate(employee_answers, 1):
            question = question_dict.get(answer.question_id)
            if question:
                st.subheader(f"{i}. {question.text}")
                st.caption(f"Kateqoriya: {question.category}")
                st.text(f"Bal: {answer.score}/5")
                if answer.comment:
                    st.text_area("Şərh:", value=answer.comment, key=f"emp_comment_{answer.question_id}", disabled=True)
                else:
                    st.text("Şərh: Yoxdur")
                st.markdown("---")
        
        # Rəhbər üçün cavab formu
        st.subheader("Öz Cavablarınız")
        with st.form("manager_evaluation_form"):
            manager_answers_data = {}
            
            for i, question in enumerate(questions, 1):
                st.subheader(f"{i}. {question.text}")
                st.caption(f"Kateqoriya: {question.category}")
                score = st.slider("Bal", 1, 5, 3, key=f"manager_score_{question.id}", help="1 - Çox zəif, 5 - Əla")
                comment = st.text_area("Şərh (isteğe bağlı)", key=f"manager_comment_{question.id}", placeholder="Fikirlərinizi əlavə edin...")
                manager_answers_data[question.id] = {"score": score, "comment": comment}
                if i < len(questions):
                    st.markdown("---")
            
            submitted = st.form_submit_button("Qiymətləndirməni Yekunlaşdır", use_container_width=True, type="primary")
            if submitted:
                try:
                    KpiService.submit_evaluation(evaluation_id, st.session_state['user_id'], manager_answers_data)
                    st.success("Qiymətləndirmə uğurla yekunlaşdırıldı! Tapşırıqlar səhifəsinə yönləndirilirsiniz...")
                    st.switch_page("pages/7_kpi_tapşırıqlarım.py")
                except Exception as e:
                    st.error(f"Qiymətləndirmə yekunlaşdırılarkən xəta baş verdi: {str(e)}")
        st.stop()
        
    elif evaluation.status == EvaluationStatus.PENDING:
        # İşçi özünü qiymətləndirir
        if evaluation.evaluated_user_id != st.session_state['user_id']:
            st.error("Bu qiymətləndirmə hələ başlamayıb və ya sizin üçün nəzərdə tutulmayıb.")
            st.stop()
            
        evaluated_user = evaluation.evaluated_user
        
        st.title("Qiymətləndirmə Formu")
        st.info(f"**Qiymətləndirilən:** {evaluated_user.get_full_name()} | **Dövr:** {evaluation.period.name}")
        st.markdown("---")
        
        with st.form("employee_evaluation_form"):
            questions = session.query(Question).filter(Question.is_active == True).all()
            employee_answers_data = {}

            for i, question in enumerate(questions, 1):
                st.subheader(f"{i}. {question.text}")
                st.caption(f"Kateqoriya: {question.category}")
                score = st.slider("Bal", 1, 5, 3, key=f"employee_score_{question.id}", help="1 - Çox zəif, 5 - Əla")
                comment = st.text_area("Şərh (isteğe bağlı)", key=f"employee_comment_{question.id}", placeholder="Fikirlərinizi əlavə edin...")
                employee_answers_data[question.id] = {"score": score, "comment": comment}
                if i < len(questions):
                    st.markdown("---")

            submitted = st.form_submit_button("Qiymətləndirməni Göndər", use_container_width=True, type="primary")
            if submitted:
                try:
                    KpiService.submit_evaluation(evaluation_id, st.session_state['user_id'], employee_answers_data)
                    st.success("Qiymətləndirmə uğurla göndərildi! Rəhbəriniz nəzərdən keçirənə qədər gözləyin. Tapşırıqlar səhifəsinə yönləndirilirsiniz...")
                    st.switch_page("pages/7_kpi_tapşırıqlarım.py")
                except Exception as e:
                    st.error(f"Qiymətləndirmə göndərilərkən xəta baş verdi: {str(e)}")
        st.stop()