import streamlit as st
st.set_page_config(layout="wide")

import pandas as pd
import altair as alt
from sqlalchemy import select, func
from database import get_db
from models.user import User
from models.user_profile import UserProfile
from models.performance import Performance
from utils.utils import download_guide_doc_file, logout, check_login, show_notifications

current_user = check_login()
if current_user.role != "admin":
    st.error("Bu səhifəyə giriş üçün icazəniz yoxdur.")
    st.stop()

st.sidebar.page_link(page="pages/1_admin.py", label="Qiymətləndirmə", icon=":material/grading:")
show_notifications()  # Show notifications in sidebar
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
        # Original performance query
        performance_query = session.query(
            UserProfile.full_name,
            UserProfile.department,
            func.sum(Performance.weighted_points).label('total_score')
        ).join(User, UserProfile.user_id == User.id)         .join(Performance, User.id == Performance.user_id)         .filter(
            Performance.evaluation_year == selected_year,
            Performance.evaluation_month == selected_month
        )         .group_by(UserProfile.full_name, UserProfile.department)         .order_by(func.sum(Performance.weighted_points).desc())

        performance_data = performance_query.all()

        if performance_data:
         
            df_performance = pd.DataFrame(performance_data)
       
            df_performance = df_performance.rename(columns={
                "full_name": "Əməkdaş",
                "department": "Şöbə",
                "total_score": "Yekun Bal"
            })
            
            st.header("Ümumi Nəticələr")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(label="Qiymətləndirilən İşçi Sayı", value=len(df_performance))
            with col2:
                avg_score = df_performance["Yekun Bal"].mean()
                st.metric(label="Orta Yekun Bal", value=f"{avg_score:.2f}")
            with col3:
                dept_count = df_performance["Şöbə"].nunique()
                st.metric(label="Şöbə Sayı", value=dept_count)
            
            st.divider()

            # Department comparison chart
            st.header("Şöbələr üzrə Müqayisə")
            if not df_performance["Şöbə"].isnull().all():
                dept_scores = df_performance.groupby("Şöbə")["Yekun Bal"].mean().reset_index()
                dept_scores = dept_scores.sort_values("Yekun Bal", ascending=False)
                
                bar_chart = alt.Chart(dept_scores).mark_bar().encode(
                    x=alt.X('Yekun Bal:Q', title="Orta Yekun Bal"),
                    y=alt.Y('Şöbə:N', sort='-x', title="Şöbə"),
                    tooltip=['Şöbə', 'Yekun Bal']
                ).properties(
                    title="Şöbələr üzrə Orta Performans",
                    height=alt.Step(40)
                )
                st.altair_chart(bar_chart, use_container_width=True)
                
                # Show department details
                st.subheader("Şöbə Detalları")
                st.dataframe(dept_scores.rename(columns={"Yekun Bal": "Orta Yekun Bal"}), use_container_width=True)
            else:
                st.info("Şöbə məlumatı mövcud deyil.")

            st.divider()

            # Individual performance chart
            st.header("İşçilərin Performans Müqayisəsi")
            bar_chart = alt.Chart(df_performance).mark_bar().encode(
                x=alt.X('Yekun Bal:Q', title="Yekun Bal"),
                y=alt.Y('Əməkdaş:N', sort='-x', title="Əməkdaş"),
                tooltip=['Əməkdaş', 'Yekun Bal', 'Şöbə']
            ).properties(
                height=alt.Step(40)
            )
            st.altair_chart(bar_chart, use_container_width=True)

            st.divider()

            # Performance level distribution
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

            # Department level distribution
            if not df_performance["Şöbə"].isnull().all():
                st.subheader("Şöbələr üzrə Səviyyə Paylanması")
                dept_level_dist = df_performance.groupby(['Şöbə', 'Səviyyə']).size().reset_index(name='count')
                dept_level_chart = alt.Chart(dept_level_dist).mark_bar().encode(
                    x=alt.X('Şöbə:N', title="Şöbə"),
                    y=alt.Y('count:Q', title="İşçi Sayı"),
                    color=alt.Color('Səviyyə:N', title="Performans Səviyyəsi"),
                    tooltip=['Şöbə', 'Səviyyə', 'count']
                ).properties(
                    title="Şöbələr üzrə Səviyyə Paylanması"
                )
                st.altair_chart(dept_level_chart, use_container_width=True)

        else:
            st.warning("Seçilmiş dövr üçün heç bir qiymətləndirmə məlumatı tapılmadı.")
else:
    st.info("Nəticələri görmək üçün zəhmət olmasa, yuxarıdan il və qiymətləndirmə növünü seçin.")

st.divider()

# Personal development trends section
st.header("Fərdi İnkişaf Trendləri")

with get_db() as session:
    # Get performance data over time for trend analysis
    trend_query = session.query(
        UserProfile.full_name,
        UserProfile.department,
        Performance.evaluation_year,
        Performance.evaluation_month,
        func.sum(Performance.weighted_points).label('total_score')
    ).join(User, UserProfile.user_id == User.id)     .join(Performance, User.id == Performance.user_id)     .group_by(UserProfile.full_name, UserProfile.department, Performance.evaluation_year, Performance.evaluation_month)     .order_by(UserProfile.full_name, Performance.evaluation_year, Performance.evaluation_month)

    trend_data = trend_query.all()

    if trend_data:
        df_trend = pd.DataFrame(trend_data)
        df_trend = df_trend.rename(columns={
            "full_name": "Əməkdaş",
            "department": "Şöbə",
            "evaluation_year": "İl",
            "evaluation_month": "Qiymətləndirmə",
            "total_score": "Yekun Bal"
        })
        
        # Create a time period column for sorting
        df_trend["Dövr"] = df_trend["İl"].astype(str) + " - " + df_trend["Qiymətləndirmə"]
        
        # Select employee for trend analysis
        employees = sorted(df_trend["Əməkdaş"].unique())
        selected_employee_trend = st.selectbox("İnkişaf trendinə baxmaq üçün işçi seçin:", options=employees, index=0 if employees else None)
        
        if selected_employee_trend:
            employee_trend_data = df_trend[df_trend["Əməkdaş"] == selected_employee_trend]
            
            if not employee_trend_data.empty:
                # Line chart for performance trend
                trend_chart = alt.Chart(employee_trend_data).mark_line(point=True).encode(
                    x=alt.X('Dövr:N', title="Dövr", sort=None),
                    y=alt.Y('Yekun Bal:Q', title="Yekun Bal"),
                    tooltip=['Dövr', 'Yekun Bal']
                ).properties(
                    title=f"{selected_employee_trend} - Performans İnkişaf Trendi"
                )
                st.altair_chart(trend_chart, use_container_width=True)
                
                # Show trend data
                st.subheader("Trend Detalları")
                st.dataframe(employee_trend_data[["Dövr", "Yekun Bal"]], use_container_width=True)
                
                # Calculate improvement
                if len(employee_trend_data) > 1:
                    first_score = employee_trend_data.iloc[0]["Yekun Bal"]
                    last_score = employee_trend_data.iloc[-1]["Yekun Bal"]
                    improvement = last_score - first_score
                    improvement_pct = (improvement / first_score) * 100 if first_score != 0 else 0
                    
                    st.metric(
                        label="Ümumi İnkişaf", 
                        value=f"{improvement:+.2f} bal", 
                        delta=f"{improvement_pct:+.1f}%" if improvement_pct != 0 else None
                    )
            else:
                st.info("Seçilmiş işçi üçün trend məlumatı mövcud deyil.")
    else:
        st.info("Performans trend analizi üçün məlumat mövcud deyil.")