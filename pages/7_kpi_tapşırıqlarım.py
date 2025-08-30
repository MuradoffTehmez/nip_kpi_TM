# pages/7_kpi_tapşırıqlarım.py

import streamlit as st
from database import get_db
from models.user import User
from models.kpi import Evaluation

# Sessiyadan istifadəçi məlumatını alırıq
if 'user_id' not in st.session_state:
    st.warning("Bu səhifəyə baxmaq üçün sistemə daxil olmalısınız.")
    st.link_button("Giriş səhifəsi", "/")
    st.stop()

user_id = st.session_state['user_id']

with get_db() as session:
    user = session.query(User).get(user_id)
    st.title(f"{user.get_full_name()}, KPI Tapşırıqlarınız")
    
    pending_evaluations = session.query(Evaluation).filter(
        Evaluation.evaluator_user_id == user.id,
        Evaluation.status == 'PENDING'
    ).all()
    
    if not pending_evaluations:
        st.success("Hazırda tamamlanmalı KPI tapşırığınız yoxdur.")
    else:
        # Bu kod əvvəlki təklifdəki user panelinin eynisidir
        for eval in pending_evaluations:
            evaluated_user = session.query(User).get(eval.evaluated_user_id)
            with st.container(border=True):
                # ... (Qiymətləndirmə kartlarının göstərilməsi) ...
                if st.button("Qiymətləndir", key=f"eval_{eval.id}"):
                    # Qiymətləndirmə forması səhifəsinə yönləndirmə
                    st.switch_page(f"pages/5_qiymetlendirme_formu.py?evaluation_id={eval.id}")