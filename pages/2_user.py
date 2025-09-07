# pages/2_user.py

import streamlit as st
st.set_page_config(layout="wide")

import pandas as pd
import altair as alt
from datetime import date
from database import get_db
from services.kpi_service import KpiService
from services.degree360_service import Degree360Service
from services.user_service import UserService
from utils.utils import (
    download_guide_doc_file, 
    logout, 
    to_excel_formatted_report, 
    get_styled_table_html, 
    check_login, 
    show_notifications
)

# Təhlükəsizlik yoxlaması
current_user = check_login()

# Sidebar menyusu
st.sidebar.page_link(page="pages/2_user.py", label="Şəxsi Panel", icon=":material/person:")
show_notifications()  # Show notifications in sidebar
st.sidebar.page_link(page="pages/7_kpi_tapşırıqlarım.py", label="KPI Tapşırıqlarım", icon=":material/task:")
st.sidebar.page_link(page="pages/13_360_tapsiriqlarim.py", label="360° Tapşırıqlarım", icon=":material/task:")
download_guide_doc_file()
logout()

st.title(f"Xoş gəldiniz, {current_user.get_full_name()}!")

# Tab-lər
tab1, tab2, tab3 = st.tabs(["📋 Mənim Tapşırıqlarım", "📊 Mənim Nəticələrim", "🎯 Fərdi İnkişaf Planım"])

# Tab 1: Mənim Tapşırıqlarım
with tab1:
    st.header("Mənim Tapşırıqlarım")
    
    # KPI tapşırıqları
    st.subheader("KPI Qiymətləndirmələri")
    pending_evaluations = KpiService.get_pending_evaluations_for_user(current_user.id)
    
    if not pending_evaluations:
        st.success("Hazırda tamamlanmalı KPI tapşırığınız yoxdur.")
    else:
        st.info(f"Tamamlanmalı {len(pending_evaluations)} KPI tapşırığınız var.")
        for eval in pending_evaluations:
            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                with col1:
                    if eval.evaluated_user_id == current_user.id:
                        st.markdown("**Özünüqiymətləndirmə**")
                    else:
                        evaluated_user = UserService.get_user_by_id(eval.evaluated_user_id)
                        st.markdown(f"**Qiymətləndirilən:** {evaluated_user.get_full_name() if evaluated_user else 'Naməlum'}")
                    st.caption(f"Dövr: {eval.period.name} | Son tarix: {eval.period.end_date.strftime('%d.%m.%Y')}")
                with col2:
                    if st.button("Başla", key=f"eval_{eval.id}", use_container_width=True):
                        st.switch_page(f"pages/5_qiymetlendirme_formu.py?evaluation_id={eval.id}")
    
    # 360° qiymətləndirmə tapşırıqları
    st.subheader("360° Qiymətləndirmələr")
    pending_360_evaluations = Degree360Service.get_pending_360_evaluations_for_user(current_user.id)
    
    if not pending_360_evaluations:
        st.success("Hazırda tamamlanmalı 360° qiymətləndirmə tapşırığınız yoxdur.")
    else:
        # Vaxtı yaxınlaşan tapşırıqlar üçün xəbərdarlıq
        upcoming_deadlines = []
        for eval_info in pending_360_evaluations:
            end_date = date(*map(int, eval_info["end_date"].split(".")))
            days_until_deadline = (end_date - date.today()).days
            if days_until_deadline <= 3:
                upcoming_deadlines.append({
                    "session_name": eval_info["session_name"],
                    "evaluated_user": eval_info["evaluated_user"],
                    "days_left": days_until_deadline
                })
        
        if upcoming_deadlines:
            st.warning("⚠️ Aşağıdakı 360° qiymətləndirmələrin bitməsinə az bir zaman qalıb:")
            for deadline in upcoming_deadlines:
                st.write(f"- **{deadline['session_name']}** ({deadline['evaluated_user']}) - {deadline['days_left']} gün qalıb")
            st.divider()
        
        st.info(f"Tamamlanmalı {len(pending_360_evaluations)} 360° qiymətləndirmə tapşırığınız var.")
        for eval_info in pending_360_evaluations:
            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**{eval_info['session_name']}**")
                    st.markdown(f"**Qiymətləndirilən:** {eval_info['evaluated_user']}")
                    st.caption(f"Rol: {eval_info['role']} | Son tarix: {eval_info['end_date']}")
                with col2:
                    if st.button("Başla", key=f"eval360_{eval_info['session_id']}", use_container_width=True):
                        st.switch_page("pages/13_360_tapsiriqlarim.py")
    
    # KPI tapşırıqları üçün əlavə keçid
    st.divider()
    st.info("Bütün KPI qiymətləndirmə tapşırıqlarını görmək üçün aşağıdakı düyməyə klikləyin:")
    if st.button("KPI Tapşırıqlarım", type="primary"):
        st.switch_page("pages/7_kpi_tapşırıqlarım.py")
    
    # 360° qiymətləndirmə tapşırıqları üçün əlavə keçid
    st.info("Bütün 360° qiymətləndirmə tapşırıqlarını görmək üçün aşağıdakı düyməyə klikləyin:")
    if st.button("360° Tapşırıqlarım", type="primary"):
        st.switch_page("pages/13_360_tapsiriqlarim.py")

# Tab 2: Mənim Nəticələrim
with tab2:
    st.header("Mənim Nəticələrim")
    
    # KPI nəticələri
    st.subheader("KPI Qiymətləndirmə Nəticələrim")
    completed_evaluations = KpiService.get_completed_evaluations_for_user(current_user.id)
    
    if not completed_evaluations:
        st.info("Hələ heç bir KPI qiymətləndirməsi tamamlamısınız.")
    else:
        # Performans trendini əldə edirik
        trend_data = KpiService.get_user_performance_trend(current_user.id)
        
        if trend_data:
            df_trend = pd.DataFrame(trend_data)
            df_trend = df_trend.rename(columns={
                "period_name": "Dövr",
                "score": "Yekun Bal"
            })
            
            # Xətt qrafiki üçün trend
            if len(df_trend) > 1:
                trend_chart = alt.Chart(df_trend).mark_line(point=True).encode(
                    x=alt.X('Dövr:N', title="Dövr", sort=None),
                    y=alt.Y('Yekun Bal:Q', title="Yekun Bal"),
                    tooltip=['Dövr', 'Yekun Bal']
                ).properties(
                    title="Performansınızın Zamanla Dəyişməsi",
                    height=400
                )
                st.altair_chart(trend_chart, use_container_width=True)
            else:
                st.info("Trend qrafikini göstərmək üçün ən azı iki fərqli dövr üzrə nəticə olmalıdır.")
            
            # Dövrlər üzrə nəticələr cədvəli
            st.subheader("Dövrlər Üzrə Nəticələr")
            st.dataframe(
                df_trend,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Dövr": st.column_config.TextColumn(width=200),
                    "Yekun Bal": st.column_config.NumberColumn(format="%.2f")
                }
            )
        else:
            st.info("Performans trend məlumatı mövcud deyil.")
    
    # 360° qiymətləndirmə nəticələri
    st.subheader("360° Qiymətləndirmə Nəticələrim")
    
    # İstifadəçinin qiymətləndirildiyi 360° sessiyaları
    with get_db() as session:
        from models.degree360 import Degree360Session
        evaluated_sessions = session.query(Degree360Session).filter(
            Degree360Session.evaluated_user_id == current_user.id,
            Degree360Session.status == "ACTIVE"
        ).all()
        
        if not evaluated_sessions:
            st.info("Hələ heç bir 360° qiymətləndirməsi tamamlamısınız.")
        else:
            for degree360_session in evaluated_sessions:
                # Bütün iştirakçılar tamamlamıbsa, nəticələri göstərmə
                participants = Degree360Service.get_participants_for_360_session(degree360_session.id)
                completed_participants = [p for p in participants if p.status == "COMPLETED"]
                
                if len(completed_participants) >= len(participants) * 0.5:  # Ən az 50% tamamlanıbsa
                    st.markdown(f"**{degree360_session.name}**")
                    results = Degree360Service.calculate_360_session_results(degree360_session.id)
                    if results:
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric(label="Ümumi Bal", value=results['overall_score'])
                        with col2:
                            st.metric(label="Tamamlayan", value=f"{len(completed_participants)}/{len(participants)}")
                        
                        if st.button("Ətraflı bax", key=f"view_360_{degree360_session.id}"):
                            st.switch_page("pages/14_360_hesabatlar.py")
                    st.divider()
                else:
                    st.info(f"{degree360_session.name} - Hələ kifayət qədər rəy toplanmayıb.")

# Tab 3: Fərdi İnkişaf Planım (gələcəkdə əlavə ediləcək)
with tab3:
    st.header("Fərdi İnkişaf Planım")
    st.info("Bu bölmə gələcəkdə Fərdi İnkişaf Planı (FİP) modulu ilə zənginləşdiriləcək.")
    st.image("https://images.unsplash.com/photo-1517245386807-bb43f82c33c4?auto=format&fit=crop&w=800&q=80", caption="Fərdi İnkişaf Planı", use_column_width=True)