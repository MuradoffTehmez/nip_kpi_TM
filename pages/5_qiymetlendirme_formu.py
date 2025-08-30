# pages/5_qiymetlendirme_formu.py

import streamlit as st
from database import get_db
from models.kpi import Evaluation, Question, Answer
from models.user import User

st.set_page_config(layout="wide", page_title="Qiymətləndirmə Formu")

try:
    evaluation_id = int(st.query_params.get("evaluation_id"))
except (ValueError, TypeError):
    st.error("Qiymətləndirmə tapılmadı.")
    st.stop()

with get_db() as session:
    evaluation = session.query(Evaluation).get(evaluation_id)
    if not evaluation:
        st.error("Qiymətləndirmə tapılmadı.")
        st.stop()
        
    evaluated_user = session.query(User).get(evaluation.evaluated_user_id)
    
    st.title("Qiymətləndirmə Formu")
    st.write(f"**Qiymətləndirilən:** {evaluated_user.get_full_name()}")
    st.write(f"**Dövr:** {evaluation.period.name}")
    st.markdown("---")
    
    with st.form("evaluation_form"):
        questions = session.query(Question).all()
        answers_data = {}

        for question in questions:
            st.subheader(question.text)
            score = st.slider("Bal (1-dən 5-ə qədər)", 1, 5, 3, key=f"score_{question.id}")
            comment = st.text_area("Şərh", key=f"comment_{question.id}")
            answers_data[question.id] = {"score": score, "comment": comment}
            st.markdown("---")

        submitted = st.form_submit_button("Təsdiqlə", use_container_width=True)
        if submitted:
            for q_id, ans in answers_data.items():
                new_answer = Answer(
                    evaluation_id=evaluation.id,
                    question_id=q_id,
                    score=ans['score'],
                    comment=ans['comment']
                )
                session.add(new_answer)
            
            evaluation.status = 'COMPLETED'
            session.commit()
            
            st.success("Qiymətləndirmə uğurla tamamlandı!")
            st.switch_page("pages/2_user.py")