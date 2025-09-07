# pages/7_kpi_tapşırıqlarım.py

import streamlit as st
from database import get_db
from models.user import User
from models.kpi import Evaluation, EvaluationStatus
from utils.utils import check_login, show_notifications

st.set_page_config(layout="centered", page_title="KPI Tapşırıqlarım")

current_user = check_login()

user_id = st.session_state['user_id']

st.title(f"Xoş gəldin, {current_user.get_full_name()}!")
st.header("KPI Tapşırıqlarınız")

st.sidebar.page_link(page="pages/7_kpi_tapşırıqlarım.py", label="KPI Tapşırıqlarım", icon=":material/task:")
show_notifications()  # Show notifications in sidebar

with get_db() as session:
    try:
        # Gözləyən qiymətləndirmələr (PENDING)
        st.subheader("Gözləyən Qiymətləndirmələr")
        pending_evaluations = session.query(Evaluation).filter(
            Evaluation.evaluator_user_id == user_id,
            Evaluation.status == EvaluationStatus.PENDING
        ).all()
        
        if not pending_evaluations:
            st.info("Hazırda gözləyən KPI tapşırığınız yoxdur.")
        else:
            st.info(f"{len(pending_evaluations)} ədəd gözləyən qiymətləndirməniz var.")
            for eval in pending_evaluations:
                with st.container(border=True):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        if eval.evaluated_user_id == user_id:
                            st.markdown("**Özünüqiymətləndirmə**")
                        else:
                            st.markdown(f"**Qiymətləndirilən:** {eval.evaluated_user.get_full_name()}")
                        st.caption(f"Dövr: {eval.period.name} | Son tarix: {eval.period.end_date.strftime('%d.%m.%Y')}")
                    with col2:
                        if st.button("Başla", key=f"eval_{eval.id}", use_container_width=True):
                            st.switch_page(f"pages/5_qiymetlendirme_formu.py?evaluation_id={eval.id}")
        
        # Rəhbər Rəyi Gözləyən qiymətləndirmələr (SELF_EVAL_COMPLETED)
        st.subheader("Rəhbər Rəyi Gözləyən")
        self_eval_completed_evaluations = session.query(Evaluation).filter(
            Evaluation.evaluator_user_id == user_id,
            Evaluation.status == EvaluationStatus.SELF_EVAL_COMPLETED
        ).all()
        
        if not self_eval_completed_evaluations:
            st.info("Hazırda rəhbər rəyi gözləyən qiymətləndirməniz yoxdur.")
        else:
            st.info(f"{len(self_eval_completed_evaluations)} ədəd rəhbər rəyi gözləyən qiymətləndirməniz var.")
            for eval in self_eval_completed_evaluations:
                with st.container(border=True):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"**Qiymətləndirilən:** {eval.evaluated_user.get_full_name()}")
                        st.caption(f"Dövr: {eval.period.name} | Son tarix: {eval.period.end_date.strftime('%d.%m.%Y')}")
                        st.caption("İşçi özünü qiymətləndirib")
                    with col2:
                        if st.button("Rəy Bildir", key=f"review_{eval.id}", use_container_width=True):
                            st.switch_page(f"pages/5_qiymetlendirme_formu.py?evaluation_id={eval.id}")
        
        # Yekunlaşmış qiymətləndirmələr (FINALIZED)
        st.subheader("Yekunlaşmış Qiymətləndirmələr")
        finalized_evaluations = session.query(Evaluation).filter(
            Evaluation.evaluator_user_id == user_id,
            Evaluation.status == EvaluationStatus.FINALIZED
        ).limit(10).all()

        if not finalized_evaluations:
            st.info("Hazırda yekunlaşmış qiymətləndirməniz yoxdur.")
        else:
            for eval in finalized_evaluations:
                with st.container(border=True):
                    st.markdown(f"**Qiymətləndirilən:** {eval.evaluated_user.get_full_name()}")
                    st.caption(f"Dövr: {eval.period.name} | Tarix: {eval.period.end_date.strftime('%d.%m.%Y')}")
                    st.success("Qiymətləndirmə yekunlaşdırılıb")
                    if st.button("Ətraflı bax", key=f"view_{eval.id}", use_container_width=True):
                        st.switch_page(f"pages/5_qiymetlendirme_formu.py?evaluation_id={eval.id}")
                        
    except Exception as e:
        st.error(f"Tapşırıqları yükləyərkən xəta baş verdi: {str(e)}")