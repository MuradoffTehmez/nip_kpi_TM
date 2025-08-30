# pages/5_qiymetlendirme_formu.py

import streamlit as st
from database import get_db
from models.kpi import Evaluation, Question, Answer, EvaluationStatus
from models.user import User

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
    
    if evaluation.status == EvaluationStatus.COMPLETED:
        st.success("Bu qiymətləndirmə artıq tamamlanıb.")
        if st.button("Tapşırıqlar Səhifəsinə Qayıt"):
            st.switch_page("pages/7_kpi_tapşırıqlarım.py")
        st.stop()

    evaluated_user = evaluation.evaluated_user
    
    st.title("Qiymətləndirmə Formu")
    st.info(f"**Qiymətləndirilən:** {evaluated_user.get_full_name()} | **Dövr:** {evaluation.period.name}")
    st.markdown("---")
    
    with st.form("evaluation_form"):
        questions = session.query(Question).filter(Question.is_active == True).all()
        answers_data = {}

        for i, question in enumerate(questions, 1):
            st.subheader(f"{i}. {question.text}")
            st.caption(f"Kateqoriya: {question.category}")
            score = st.slider("Bal", 1, 5, 3, key=f"score_{question.id}", help="1 - Çox zəif, 5 - Əla")
            comment = st.text_area("Şərh (isteğe bağlı)", key=f"comment_{question.id}", placeholder="Fikirlərinizi əlavə edin...")
            answers_data[question.id] = {"score": score, "comment": comment}
            if i < len(questions):
                st.markdown("---")

        submitted = st.form_submit_button("Qiymətləndirməni Yadda Saxla", use_container_width=True, type="primary")
        if submitted:
            for q_id, ans in answers_data.items():
                new_answer = Answer(
                    evaluation_id=evaluation.id,
                    question_id=q_id,
                    score=ans['score'],
                    comment=ans['comment']
                )
                session.add(new_answer)
            
            evaluation.status = EvaluationStatus.COMPLETED
            session.commit()
            
            st.success("Qiymətləndirmə uğurla tamamlandı! Tapşırıqlar səhifəsinə yönləndirilirsiniz...")
            st.switch_page("pages/7_kpi_tapşırıqlarım.py")