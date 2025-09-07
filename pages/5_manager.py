# pages/5_manager.py

import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import desc
from database import get_db
from models.user import User
from models.user_profile import UserProfile
from models.performance import Performance
from models.indicator import Indicator
from utils.utils import check_login, get_subordinates, show_notifications
from data.months_in_azeri import evaluation_types

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
    subordinates = get_subordinates(current_user.id)
    subordinate_ids = [sub.id for sub in subordinates]
    subordinate_names = [sub.get_full_name() for sub in subordinates]
else:
    # Admin üçün bütün aktiv istifadəçilər
    with get_db() as session:
        all_users = session.query(User).filter(User.is_active == True, User.role != "admin").all()
        subordinate_ids = [user.id for user in all_users]
        subordinate_names = [user.get_full_name() for user in all_users]

st.sidebar.page_link(page="pages/5_manager.py", label="Menecer Paneli", icon=":material/group:")
st.sidebar.divider()

# Filterlər
st.subheader("Filterlər")
col1, col2 = st.columns(2)
with col1:
    selected_employee = st.selectbox("İşçi seçin:", options=subordinate_names, index=None)
with col2:
    available_years = []
    with get_db() as session:
        if selected_employee:
            # Seçilmiş işçinin ID-sini tap
            selected_user = None
            if current_user.role == "manager":
                selected_user = next((sub for sub in subordinates if sub.get_full_name() == selected_employee), None)
            else:
                selected_user = next((user for user in all_users if user.get_full_name() == selected_employee), None)
            
            if selected_user:
                available_years = sorted(list(set(session.query(Performance.evaluation_year).filter(
                    Performance.user_id == selected_user.id
                ).all())), reverse=True)
                available_years = [year[0] for year in available_years]  # Extract years from tuples
        else:
            # Bütün işçilər üçün mövcud illər
            available_years = sorted(list(set(session.query(Performance.evaluation_year).filter(
                Performance.user_id.in_(subordinate_ids)
            ).all())), reverse=True)
            available_years = [year[0] for year in available_years]  # Extract years from tuples
    
    selected_year = st.selectbox("İl seçin:", options=available_years if available_years else [2024, 2025, 2026], index=None)

# Əgər işçi və il seçilibsə, nəticələri göstər
if selected_employee and selected_year:
    # Seçilmiş işçinin ID-sini tap
    selected_user = None
    if current_user.role == "manager":
        selected_user = next((sub for sub in subordinates if sub.get_full_name() == selected_employee), None)
    else:
        selected_user = next((user for user in all_users if user.get_full_name() == selected_employee), None)
    
    if selected_user:
        with get_db() as session:
            # İşçinin qiymətləndirmə nəticələrini yüklə
            performance_data = session.query(
                Performance.indicator_id, Performance.evaluation_month,
                Performance.points, Performance.weighted_points
            ).filter(
                Performance.user_id == selected_user.id,
                Performance.evaluation_year == selected_year
            ).all()
            
            if performance_data:
                # Göstəriciləri yüklə
                indicators = session.query(Indicator).all()
                indicator_map = {ind.id: ind.description for ind in indicators}
                
                # Məlumatları DataFrame-ə çevir
                df = pd.DataFrame(performance_data, columns=["indicator_id", "evaluation_month", "points", "weighted_points"])
                df["Göstərici"] = df["indicator_id"].map(indicator_map)
                df = df.rename(columns={"evaluation_month": "Qiymətləndirmə növü", "points": "Bal", "weighted_points": "Yekun Bal"})
                
                # Ümumi nəticələri göstər
                st.subheader(f"{selected_employee} - {selected_year} Nəticələri")
                
                total_score = df["Yekun Bal"].sum()
                st.metric(label="Ümumi Yekun Bal", value=f"{total_score:.2f}")
                
                # Qiymətləndirmə növləri üzrə nəticələr
                st.markdown("---")
                st.subheader("Qiymətləndirmə Növləri Üzrə Nəticələr")
                
                grouped_df = df.groupby("Qiymətləndirmə növü")["Yekun Bal"].sum().reset_index()
                fig = px.bar(grouped_df, x="Qiymətləndirmə növü", y="Yekun Bal", 
                            title=f"{selected_employee} - {selected_year} Ümumi Nəticələr",
                            labels={"Yekun Bal": "Yekun Bal", "Qiymətləndirmə növü": "Qiymətləndirmə Növü"})
                st.plotly_chart(fig, use_container_width=True)
                
                # Detallı nəticələr
                st.markdown("---")
                st.subheader("Detallı Nəticələr")
                st.dataframe(df[["Göstərici", "Qiymətləndirmə növü", "Bal", "Yekun Bal"]], use_container_width=True)
                
                # Radar qrafiki
                st.markdown("---")
                st.subheader("Performansın Təhlili (Radar Qrafiki)")
                
                # Seçilmiş qiymətləndirmə növünü seç
                selected_eval_type = st.selectbox("Qiymətləndirmə növünü seçin:", 
                                                options=df["Qiymətləndirmə növü"].unique(), 
                                                key="radar_eval_type")
                
                if selected_eval_type:
                    radar_data = df[df["Qiymətləndirmə növü"] == selected_eval_type]
                    if not radar_data.empty:
                        fig_radar = px.line_polar(radar_data, r='Bal', theta='Göstərici', line_close=True,
                                                title=f"{selected_employee} - {selected_eval_type} Performansı",
                                                range_r=[0, 5], markers=True)
                        fig_radar.update_traces(fill='toself')
                        st.plotly_chart(fig_radar, use_container_width=True)
            else:
                st.info("Seçilmiş işçi üçün bu il üzrə hələ qiymətləndirmə yoxdur.")
    else:
        st.error("Seçilmiş işçi tapılmadı.")
else:
    # Ümumi statistika
    st.subheader("Komanda Üzvlərinin Ümumi Statistikası")
    
    with get_db() as session:
        # Bütün komanda üzvlərinin son qiymətləndirmə nəticələri
        latest_performances = []
        for user_id in subordinate_ids:
            latest_performance = session.query(Performance).filter(
                Performance.user_id == user_id
            ).order_by(desc(Performance.evaluation_year), desc(Performance.evaluation_month)).first()
            
            if latest_performance:
                user_name = next((name for i, name in enumerate(subordinate_names) if subordinate_ids[i] == user_id), "Naməlum")
                latest_performances.append({
                    "İşçi": user_name,
                    "İl": latest_performance.evaluation_year,
                    "Qiymətləndirmə": latest_performance.evaluation_month,
                    "Yekun Bal": latest_performance.weighted_points
                })
        
        if latest_performances:
            df_latest = pd.DataFrame(latest_performances)
            st.dataframe(df_latest, use_container_width=True)
            
            # Ümumi orta bal
            avg_score = df_latest["Yekun Bal"].mean()
            st.metric(label="Komanda Üzvlərinin Orta Yekun Balı", value=f"{avg_score:.2f}")
        else:
            st.info("Komanda üzvləri üçün hələ qiymətləndirmə yoxdur.")