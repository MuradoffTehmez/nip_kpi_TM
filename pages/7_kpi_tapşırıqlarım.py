# pages/7_kpi_tapşırıqlarım.py

import streamlit as st
from database import get_db
from models.user import User
from models.kpi import Evaluation, EvaluationStatus

st.set_page_config(layout="centered", page_title="KPI Tapşırıqlarım")

if 'user_id' not in st.session_state:
    st.warning("Bu səhifəyə baxmaq üçün sistemə daxil olmalısınız.")
    st.link_button("Giriş səhifəsi", "/")
    st.stop()

user_id = st.session_state['user_id']

with get_db() as session:
    user = session.query(User).get(user_id)
    if not user:
        st.error("İstifadəçi tapılmadı.")
        st.stop()

    st.title(f"Xoş gəldin, {user.first_name}!")
    st.header("KPI Tapşırıqlarınız")

    pending_evaluations = session.query(Evaluation).filter(
        Evaluation.evaluator_user_id == user.id,
        Evaluation.status == EvaluationStatus.PENDING
    ).all()
    
    if not pending_evaluations:
        st.success("Hazırda tamamlanmalı KPI tapşırığınız yoxdur.")
    else:
        st.info(f"Tamamlanmalı {len(pending_evaluations)} tapşırığınız var.")
        for eval in pending_evaluations:
            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                with col1:
                    if eval.evaluated_user_id == user.id:
                        st.subheader("Özünüqiymətləndirmə")
                    else:
                        st.subheader(f"Qiymətləndirilən: {eval.evaluated_user.get_full_name()}")
                    st.caption(f"Dövr: {eval.period.name} | Son tarix: {eval.period.end_date.strftime('%d.%m.%Y')}")
                with col2:
                    if st.button("Başla", key=f"eval_{eval.id}", use_container_width=True, type="primary"):
                        st.switch_page(f"pages/5_qiymetlendirme_formu.py?evaluation_id={eval.id}")

    st.markdown("---")
    st.header("Tamamlanmış Tapşırıqlar")
    
    completed_evaluations = session.query(Evaluation).filter(
        Evaluation.evaluator_user_id == user.id,
        Evaluation.status == EvaluationStatus.COMPLETED
    ).limit(10).all()

    if completed_evaluations:
        for eval in completed_evaluations:
            st.success(f"**{eval.evaluated_user.get_full_name()}** üçün qiymətləndirmə tamamlandı. ({eval.period.name})")