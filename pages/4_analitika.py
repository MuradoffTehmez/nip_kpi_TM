import streamlit as st
st.set_page_config(layout="wide")

import pandas as pd
import altair as alt
from sqlalchemy import select, func
from database import get_db
from models.user import User
from models.user_profile import UserProfile
from models.performance import Performance
from utils.utils import download_guide_doc_file, logout, check_login

current_user = check_login()
if current_user.role != "admin":
    st.error("Bu səhifəyə giriş üçün icazəniz yoxdur.")
    st.stop()


st.sidebar.page_link(page="pages/1_admin.py", label="Qiymətləndirmə", icon=":material/grading:")
st.sidebar.page_link(page="pages/3_idarəetmə.py", label="İdarəetmə", icon=":material/settings:")
st.sidebar.page_link(page="pages/4_analitika.py", label="Analitika", icon=":material/monitoring:")
download_guide_doc_file()
logout()


st.title("Analitika Paneli")
st.divider()


with get_db() as session:
    available_years = sorted(list(set(session.scalars(select(Performance.evaluation_year)).all())), reverse=True)
    available_months = sorted(list(set(session.scalars(select(Performance.evaluation_month)).all())))

col1, col2 = st.columns(2)
with col1:
    selected_year = st.selectbox("İli seçin:", options=available_years, index=0 if available_years else None)
with col2:
    selected_month = st.selectbox("Qiymətləndirmə növünü seçin:", options=available_months, index=0 if available_months else None)

st.divider()


if selected_year and selected_month:
    with get_db() as session:
        performance_query = session.query(
            UserProfile.full_name,
            func.sum(Performance.weighted_points).label('total_score')
        ).join(User, UserProfile.user_id == User.id)\
         .join(Performance, User.id == Performance.user_id)\
         .filter(
            Performance.evaluation_year == selected_year,
            Performance.evaluation_month == selected_month
         )\
         .group_by(UserProfile.full_name)\
         .order_by(func.sum(Performance.weighted_points).desc())

        performance_data = performance_query.all()

        if performance_data:
         
            df_performance = pd.DataFrame(performance_data)
       
            df_performance = df_performance.rename(columns={
                "full_name": "Əməkdaş",
                "total_score": "Yekun Bal"
            })
            
            st.header("Ümumi Nəticələr")
            col1, col2 = st.columns(2)
            with col1:
                st.metric(label="Qiymətləndirilən İşçi Sayı", value=len(df_performance))
            with col2:
                avg_score = df_performance["Yekun Bal"].mean()
                st.metric(label="Orta Yekun Bal", value=f"{avg_score:.2f}")
            
            st.divider()

            st.header("İşçilərin Performans Müqayisəsi")
            bar_chart = alt.Chart(df_performance).mark_bar().encode(
                x=alt.X('Yekun Bal:Q', title="Yekun Bal"),
                y=alt.Y('Əməkdaş:N', sort='-x', title="Əməkdaş"),
                tooltip=['Əməkdaş', 'Yekun Bal']
            ).properties(
                height=alt.Step(40)
            )
            st.altair_chart(bar_chart, use_container_width=True)

            st.divider()

            st.header("Performans Səviyyələrinin Paylanması")
            
            def get_performance_level(score):
                if score >= 4.6: return "Əla (5)"
                if 3.6 <= score < 4.6: return "Yaxşı (4)"
                if 2.6 <= score < 3.6: return "Kafi (3)"
                return "Qeyri-kafi (2)"

            df_performance['Səviyyə'] = df_performance['Yekun Bal'].apply(get_performance_level)
            level_counts = df_performance['Səviyyə'].value_counts().reset_index()
            
            pie_chart = alt.Chart(level_counts).mark_arc(innerRadius=50).encode(
                theta=alt.Theta(field="count", type="quantitative"),
                color=alt.Color(field="Səviyyə", type="nominal", title="Performans Səviyyəsi"),
                tooltip=['Səviyyə', 'count']
            ).properties(
                title='İşçilərin Səviyyələr Üzrə Paylanması'
            )
            st.altair_chart(pie_chart, use_container_width=True)

        else:
            st.warning("Seçilmiş dövr üçün heç bir qiymətləndirmə məlumatı tapılmadı.")
else:
    st.info("Nəticələri görmək üçün zəhmət olmasa, yuxarıdan il və qiymətləndirmə növünü seçin.")