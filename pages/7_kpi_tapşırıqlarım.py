# pages/7_kpi_tapşırıqlarım.py

import streamlit as st
from database import get_db
from models.user import User
from models.kpi import Evaluation, EvaluationStatus
from utils.utils import check_login

st.set_page_config(layout="centered", page_title="KPI Tapşırıqlarım")

current_user = check_login()

user_id = st.session_state['user_id']

st.title(f"Xoş gəldin, {current_user.get_full_name()}!")
st.header("KPI Tapşırıqlarınız")

with get_db() as session:
    try:
        pending_evaluations = session.query(Evaluation).filter(
            Evaluation.evaluator_user_id == user_id,
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
                        if eval.evaluated_user_id == user_id:
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
            Evaluation.evaluator_user_id == user_id,
            Evaluation.status == EvaluationStatus.COMPLETED
        ).limit(10).all()

        if completed_evaluations:
            for eval in completed_evaluations:
                st.success(f"**{eval.evaluated_user.get_full_name()}** üçün qiymətləndirmə tamamlandı. ({eval.period.name})")
    except Exception as e:
        st.error(f"Tapşırıqları yükləyərkən xəta baş verdi: {str(e)}")