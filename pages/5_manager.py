# pages/5_manager.py

import streamlit as st
import pandas as pd
import altair as alt
from database import get_db
from services.kpi_service import KpiService
from services.user_service import UserService
from utils.utils import check_login, show_notifications
from models.kpi import Evaluation, EvaluationStatus

st.set_page_config(layout="wide", page_title="Menecer Paneli")

# Təhlükəsizlik yoxlaması
current_user = check_login()

# Yalnız manager və ya admin roluna sahib istifadəçilər bu səhifəyə daxil ola bilər
if current_user.role not in ["manager", "admin"]:
    st.error("Bu səhifəyə giriş üçün icazəniz yoxdur.")
    st.stop()

st.title(f"Menecer Paneli - Xoş gəldiniz, {current_user.get_full_name()}!")

show_notifications()  # Show notifications in sidebar

# Əgər istifadəçi managerdirsə, yalnız öz komanda üzvlərini görəcək
# Əgər istifadəçi admindirsə, bütün istifadəçiləri görəcək
if current_user.role == "manager":
    subordinates = UserService.get_subordinates(current_user.id)
    subordinate_ids = [sub.id for sub in subordinates]
    subordinate_names = [sub.get_full_name() for sub in subordinates]
else:
    # Admin üçün bütün aktiv istifadəçilər
    all_users = UserService.get_all_active_users()
    # Admin özünü çıxardırıq
    all_users = [user for user in all_users if user.id != current_user.id]
    subordinate_ids = [user.id for user in all_users]
    subordinate_names = [user.get_full_name() for user in all_users]

st.sidebar.page_link(page="pages/5_manager.py", label="Menecer Paneli", icon=":material/group:")
st.sidebar.divider()

# Qiymətləndirmə dövrlərini əldə edirik
periods = KpiService.get_all_evaluation_periods()

if not periods:
    st.info("Hələ heç bir qiymətləndirmə dövrü yaradılmayıb.")
else:
    # Filterlər
    st.subheader("Filterlər")
    col1, col2 = st.columns(2)
    with col1:
        selected_employee = st.selectbox("İşçi seçin:", options=subordinate_names, index=None)
    with col2:
        period_options = [p.name for p in periods]
        selected_period_name = st.selectbox("Qiymətləndirmə dövrünü seçin:", options=period_options, index=0)
        selected_period = next((p for p in periods if p.name == selected_period_name), None)

    # Əgər işçi və dövr seçilibsə, nəticələri göstər
    if selected_employee and selected_period:
        # Seçilmiş işçinin ID-sini tap
        selected_user = None
        if current_user.role == "manager":
            selected_user = next((sub for sub in subordinates if sub.get_full_name() == selected_employee), None)
        else:
            selected_user = next((user for user in all_users if user.get_full_name() == selected_employee), None)
        
        if selected_user:
            # İşçinin seçilmiş dövr üzrə qiymətləndirmələrini əldə edirik
            with get_db() as session:
                evaluations = session.query(Evaluation).filter(
                    Evaluation.evaluated_user_id == selected_user.id,
                    Evaluation.period_id == selected_period.id
                ).all()
                
                if not evaluations:
                    st.info("Seçilmiş işçi üçün bu dövr üzrə hələ qiymətləndirmə yoxdur.")
                else:
                    # Qiymətləndirmələrin yekun ballarını hesablayırıq
                    scores = [KpiService.calculate_evaluation_score(e.id) for e in evaluations]
                    avg_score = sum(scores) / len(scores) if scores else 0
                    
                    st.subheader(f"{selected_employee} - {selected_period.name} Nəticələri")
                    st.metric(label="Orta Yekun Bal", value=f"{avg_score:.2f}")
                    
                    # Qiymətləndirmə detalları
                    eval_details = []
                    for e in evaluations:
                        evaluator = UserService.get_user_by_id(e.evaluator_user_id)
                        score = KpiService.calculate_evaluation_score(e.id)
                        status = e.status.value
                        
                        eval_details.append({
                            "ID": e.id,
                            "Qiymətləndirən": evaluator.get_full_name() if evaluator else "Naməlum",
                            "Status": status,
                            "Yekun Bal": round(score, 2)
                        })
                    
                    df_eval_details = pd.DataFrame(eval_details)
                    st.dataframe(df_eval_details, use_container_width=True)
                    
                    # Yekunlaşdırma funksiyası
                    # Yalnız həm SELF_EVAL_COMPLETED, həm də MANAGER_REVIEW_COMPLETED statuslu qiymətləndirmələri yekunlaşdırmaq olar
                    finalizable_evals = [e for e in evaluations if e.status in [EvaluationStatus.SELF_EVAL_COMPLETED, EvaluationStatus.MANAGER_REVIEW_COMPLETED]]
                    if finalizable_evals:
                        st.subheader("Yekunlaşdırma")
                        st.info("Aşağıdakı qiymətləndirmələri yekunlaşdırmaq mümkündür:")
                        
                        # Yekunlaşdırmaq üçün qiymətləndirmə seçimi
                        eval_options = [f"{e.id} - {UserService.get_user_by_id(e.evaluator_user_id).get_full_name() if UserService.get_user_by_id(e.evaluator_user_id) else 'Naməlum'} ({e.status.value})" for e in finalizable_evals]
                        selected_evals_to_finalize = st.multiselect(
                            "Yekunlaşdırmaq üçün qiymətləndirmələri seçin:",
                            options=eval_options,
                            default=eval_options
                        )
                        
                        if st.button("Seçilmiş Qiymətləndirmələri Yekunlaşdır"):
                            if selected_evals_to_finalize:
                                finalized_count = 0
                                for eval_option in selected_evals_to_finalize:
                                    eval_id = int(eval_option.split(" - ")[0])
                                    evaluation = session.query(Evaluation).filter(Evaluation.id == eval_id).first()
                                    if evaluation and evaluation.status in [EvaluationStatus.SELF_EVAL_COMPLETED, EvaluationStatus.MANAGER_REVIEW_COMPLETED]:
                                        evaluation.status = EvaluationStatus.FINALIZED
                                        session.commit()
                                        finalized_count += 1
                                
                                if finalized_count > 0:
                                    st.success(f"{finalized_count} qiymətləndirmə uğurla yekunlaşdırıldı!")
                                    st.rerun()
                                else:
                                    st.warning("Yekunlaşdırmaq üçün qiymətləndirmə seçilməyib.")
                            else:
                                st.warning("Yekunlaşdırmaq üçün qiymətləndirmə seçilməyib.")
                    
                    # Qiymətləndirmə formuna keçid
                    st.subheader("Qiymətləndirmə Formuna Bax")
                    if st.button("Qiymətləndirmə Formuna Bax"):
                        # Əgər yalnız bir qiymətləndirmə varsa, ona yönləndir
                        if len(evaluations) == 1:
                            st.switch_page(f"pages/5_qiymetlendirme_formu.py?evaluation_id={evaluations[0].id}")
                        else:
                            # Əks halda, qiymətləndirmə seçmək üçün dropdown göstər
                            eval_options = [f"{e.id} - {UserService.get_user_by_id(e.evaluator_user_id).get_full_name() if UserService.get_user_by_id(e.evaluator_user_id) else 'Naməlum'} ({e.status.value})" for e in evaluations]
                            selected_eval_option = st.selectbox("Qiymətləndirmə seçin:", options=eval_options)
                            if selected_eval_option:
                                eval_id = int(selected_eval_option.split(" - ")[0])
                                st.switch_page(f"pages/5_qiymetlendirme_formu.py?evaluation_id={eval_id}")
        else:
            st.error("Seçilmiş işçi tapılmadı.")
    else:
        # Ümumi statistika
        st.subheader("Komanda Üzvlərinin Ümumi Statistikası")
        
        # Bütün dövrləri göstər
        period_options = [p.name for p in periods]
        selected_overview_period_name = st.selectbox("Ümumi baxış üçün dövr seçin:", options=period_options, index=0, key="overview_period")
        selected_overview_period = next((p for p in periods if p.name == selected_overview_period_name), None)
        
        if selected_overview_period:
            # Komanda üzvlərinin seçilmiş dövr üzrə performansını əldə edirik
            performance_data = []
            with get_db() as session:
                for user_id in subordinate_ids:
                    # Yalnız FINALIZED statuslu qiymətləndirmələri nəzərə alırıq
                    evaluations = session.query(Evaluation).filter(
                        Evaluation.evaluated_user_id == user_id,
                        Evaluation.period_id == selected_overview_period.id,
                        Evaluation.status == EvaluationStatus.FINALIZED
                    ).all()
                    
                    if evaluations:
                        scores = [KpiService.calculate_evaluation_score(e.id) for e in evaluations]
                        avg_score = sum(scores) / len(scores) if scores else 0
                        
                        user = UserService.get_user_by_id(user_id)
                        performance_data.append({
                            "İşçi": user.get_full_name() if user else "Naməlum",
                            "Orta Yekun Bal": round(avg_score, 2)
                        })
            
            if performance_data:
                df_performance = pd.DataFrame(performance_data)
                
                # Cədvəl şəklində göstərmək
                st.dataframe(df_performance, use_container_width=True)
                
                # Ümumi orta bal
                overall_avg = df_performance["Orta Yekun Bal"].mean()
                st.metric(label="Komanda Üzvlərinin Orta Yekun Balı", value=f"{overall_avg:.2f}")
                
                # Qrafik şəklində göstərmək
                if len(df_performance) > 1:
                    chart = alt.Chart(df_performance).mark_bar().encode(
                        x=alt.X('Orta Yekun Bal:Q', title="Orta Yekun Bal"),
                        y=alt.Y('İşçi:N', sort='-x', title="İşçi"),
                        tooltip=['İşçi', 'Orta Yekun Bal']
                    ).properties(
                        title="Komanda Üzvlərinin Performansı",
                        height=400
                    )
                    st.altair_chart(chart, use_container_width=True)
            else:
                st.info("Seçilmiş dövr üçün hələ yekunlaşdırılmış qiymətləndirmə yoxdur.")
        
        # İşçilərin performans trendini göstərmək
        st.subheader("İşçilərin Performans Trendi")
        selected_trend_employee = st.selectbox("Trend üçün işçi seçin:", options=subordinate_names, index=None, key="trend_employee")
        
        if selected_trend_employee:
            # Seçilmiş işçinin ID-sini tap
            selected_user = None
            if current_user.role == "manager":
                selected_user = next((sub for sub in subordinates if sub.get_full_name() == selected_trend_employee), None)
            else:
                selected_user = next((user for user in all_users if user.get_full_name() == selected_trend_employee), None)
            
            if selected_user:
                # Performans trendini əldə edirik
                trend_data = KpiService.get_user_performance_trend(selected_user.id)
                
                if trend_data:
                    df_trend = pd.DataFrame(trend_data)
                    df_trend = df_trend.rename(columns={
                        "period_name": "Dövr",
                        "score": "Yekun Bal"
                    })
                    
                    # Xətt qrafiki
                    if len(df_trend) > 1:
                        trend_chart = alt.Chart(df_trend).mark_line(point=True).encode(
                            x=alt.X('Dövr:N', title="Dövr", sort=None),
                            y=alt.Y('Yekun Bal:Q', title="Yekun Bal"),
                            tooltip=['Dövr', 'Yekun Bal']
                        ).properties(
                            title=f"{selected_trend_employee} - Performans Trendi",
                            height=400
                        )
                        st.altair_chart(trend_chart, use_container_width=True)
                    
                    # Cədvəl şəklində göstərmək
                    st.dataframe(df_trend, use_container_width=True)
                else:
                    st.info("Seçilmiş işçi üçün hələ performans trend məlumatı yoxdur.")