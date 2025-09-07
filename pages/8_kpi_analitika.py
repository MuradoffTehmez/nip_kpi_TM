# pages/8_kpi_analitika.py

import streamlit as st
st.set_page_config(layout="wide")

import pandas as pd
import altair as alt
from database import get_db
from services.kpi_service import KpiService
from services.user_service import UserService
from utils.utils import check_login, logout, show_notifications

current_user = check_login()
if current_user.role != "admin":
    st.error("Bu səhifəyə giriş üçün icazəniz yoxdur.")
    st.stop()

st.sidebar.page_link(page="pages/6_kpi_idarəetmə.py", label="KPI İdarəetmə", icon=":material/settings:")
show_notifications()  # Show notifications in sidebar
st.sidebar.page_link(page="pages/8_kpi_analitika.py", label="KPI Analitika", icon=":material/monitoring:")
logout()

# Tabs
tab1, tab2, tab3 = st.tabs(["📊 Ümumi Analitika", "🔄 Dövrlər Arası Müqayisə", "🧠 Səriştə üzrə Analiz"])

with tab1:
    st.title("KPI Analitika Paneli")
    st.divider()

    available_periods = KpiService.get_all_evaluation_periods()

    if not available_periods:
        st.info("Hələ heç bir qiymətləndirmə dövrü yaradılmayıb.")
        st.stop()

    period_options = [p.name for p in available_periods]
    selected_period_name = st.selectbox("Qiymətləndirmə dövrünü seçin:", options=period_options, index=0)
    selected_period = next((p for p in available_periods if p.name == selected_period_name), None)

    if not selected_period:
        st.error("Seçilmiş dövr tapılmadı.")
        st.stop()

    period_id = selected_period.id

    st.divider()

    # Ümumi Nəticələr
    st.header("Ümumi Nəticələr")

    # Şöbələr siyahısını əldə edirik
    with get_db() as session:
        from models.user_profile import UserProfile
        departments = sorted(list(set(session.scalars(
            session.query(UserProfile.department).filter(UserProfile.department.isnot(None))
        ).all())))

    col1, col2 = st.columns(2)
    with col1:
        selected_department = st.selectbox("Şöbə seçin (vacib deyil):", options=["Bütün şöbələr"] + departments, index=0)

    st.divider()

    # Performans məlumatlarını əldə edirik
    department_filter = None if selected_department == "Bütün şöbələr" else selected_department
    performance_data = KpiService.get_user_performance_data(period_id, department=department_filter)

    if performance_data:
        df_performance = pd.DataFrame(performance_data)
        df_performance = df_performance.rename(columns={
            "full_name": "Əməkdaş",
            "department": "Şöbə",
            "total_score": "Yekun Bal"
        })
        
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

        # Şöbələr üzrə Müqayisə
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
            
            # Şöbə detalları
            st.subheader("Şöbə Detalları")
            st.dataframe(dept_scores.rename(columns={"Yekun Bal": "Orta Yekun Bal"}), use_container_width=True)
        else:
            st.info("Şöbə məlumatı mövcud deyil.")

        st.divider()

        # İşçilərin Performans Müqayisəsi
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

        # Performans Səviyyələrinin Paylanması
        st.header("Performans Səviyyələrinin Paylanması")
        
        def get_performance_level(score):
            """
            Verilmiş balla əsasən performans səviyyəsini müəyyən edir.
            
            Args:
                score (float): Yekun bal.
                
            Returns:
                str: Performans səviyyəsi ("Əla (5)", "Yaxşı (4)", "Kafi (3)", "Qeyri-kafi (2)").
            """
            if score >= 4.6: 
                return "Əla (5)"
            if 3.6 <= score < 4.6: 
                return "Yaxşı (4)"
            if 2.6 <= score < 3.6: 
                return "Kafi (3)"
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

        # Şöbələr üzrə Səviyyə Paylanması
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

    st.divider()

    # Fərdi İnkişaf Trendləri
    st.header("Fərdi İnkişaf Trendləri")

    users = UserService.get_all_active_users()
    user_options = [u.get_full_name() for u in users]
    user_id_map = {u.get_full_name(): u.id for u in users}

    selected_user_name = st.selectbox("İnkişaf trendinə baxmaq üçün işçi seçin:", options=user_options, index=0)
    selected_user_id = user_id_map.get(selected_user_name)

    if selected_user_id:
        trend_data = KpiService.get_user_performance_trend(selected_user_id)
        
        if trend_data:
            df_trend = pd.DataFrame(trend_data)
            df_trend = df_trend.rename(columns={
                "period_name": "Dövr",
                "score": "Yekun Bal"
            })
            
            # Xətt qrafiki üçün trend
            trend_chart = alt.Chart(df_trend).mark_line(point=True).encode(
                x=alt.X('Dövr:N', title="Dövr", sort=None),
                y=alt.Y('Yekun Bal:Q', title="Yekun Bal"),
                tooltip=['Dövr', 'Yekun Bal']
            ).properties(
                title=f"{selected_user_name} - Performans İnkişaf Trendi"
            )
            st.altair_chart(trend_chart, use_container_width=True)
            
            # Trend detalları
            st.subheader("Trend Detalları")
            st.dataframe(df_trend[["Dövr", "Yekun Bal"]], use_container_width=True)
            
            # İnkişaf məlumatı
            if len(df_trend) > 1:
                first_score = df_trend.iloc[0]["Yekun Bal"]
                last_score = df_trend.iloc[-1]["Yekun Bal"]
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

with tab2:
    st.title("Dövrlər Arası Müqayisə")
    st.divider()
    
    # Birdən çox dövr seçimi
    available_periods = KpiService.get_all_evaluation_periods()
    if not available_periods:
        st.info("Hələ heç bir qiymətləndirmə dövrü yaradılmayıb.")
        st.stop()
    
    period_options = [p.name for p in available_periods]
    selected_period_names = st.multiselect(
        "Müqayisə üçün dövrləri seçin:", 
        options=period_options, 
        default=period_options[:2] if len(period_options) >= 2 else period_options
    )
    
    if not selected_period_names:
        st.warning("Müqayisə etmək üçün ən azı bir dövr seçməlisiniz.")
        st.stop()
    
    selected_periods = [p for p in available_periods if p.name in selected_period_names]
    period_ids = [p.id for p in selected_periods]
    
    # Performans məlumatlarını əldə edirik
    performance_comparison = KpiService.get_multiple_periods_performance_data(period_ids)
    
    if performance_comparison:
        # Məlumatları vizuallaşdırmaq üçün hazırlanır
        comparison_data = []
        for period_name, data in performance_comparison.items():
            for item in data:
                comparison_data.append({
                    "Dövr": period_name,
                    "Əməkdaş": item["full_name"],
                    "Şöbə": item["department"],
                    "Yekun Bal": item["total_score"]
                })
        
        df_comparison = pd.DataFrame(comparison_data)
        
        # Hər bir işçinin müxtəlif dövrlərdəki nəticələri
        st.header("İşçilərin Dövrlər Üzrə Nəticələri")
        pivot_df = df_comparison.pivot(index="Əməkdaş", columns="Dövr", values="Yekun Bal")
        st.dataframe(pivot_df, use_container_width=True)
        
        # Qrafik şəkildə müqayisə
        st.divider()
        st.header("Dövrlər Üzrə Ortalama Performans")
        period_avg_scores = df_comparison.groupby("Dövr")["Yekun Bal"].mean().reset_index()
        period_avg_scores = period_avg_scores.sort_values("Dövr")
        
        line_chart = alt.Chart(period_avg_scores).mark_line(point=True).encode(
            x=alt.X('Dövr:N', title="Dövr", sort=None),
            y=alt.Y('Yekun Bal:Q', title="Orta Yekun Bal"),
            tooltip=['Dövr', 'Yekun Bal']
        ).properties(
            title="Dövrlər Üzrə Ortalama Performans",
            height=400
        )
        st.altair_chart(line_chart, use_container_width=True)
        
        # Hər bir işçinin dövrlər üzrə nəticələri
        st.divider()
        st.header("İşçilərin Dövrlər Üzrə Nəticələri (Qrafik)")
        if not df_comparison.empty:
            # Hər bir işçinin dövrlər üzrə nəticələrini göstərmək üçün line chart
            line_chart_users = alt.Chart(df_comparison).mark_line(point=True).encode(
                x=alt.X('Dövr:N', title="Dövr", sort=None),
                y=alt.Y('Yekun Bal:Q', title="Yekun Bal"),
                color=alt.Color('Əməkdaş:N', legend=None),
                tooltip=['Əməkdaş', 'Dövr', 'Yekun Bal']
            ).properties(
                title="Hər bir işçinin dövrlər üzrə nəticələri",
                height=400
            )
            st.altair_chart(line_chart_users, use_container_width=True)
            
            # Cədvəl şəklində göstərmək
            st.subheader("Ətraflı Məlumat")
            st.dataframe(df_comparison, use_container_width=True)
    else:
        st.warning("Seçilmiş dövrlər üçün heç bir qiymətləndirmə məlumatı tapılmadı.")

with tab3:
    st.title("Səriştə üzrə Analiz")
    st.divider()
    
    # Competency service
    from services.competency_service import CompetencyService
    db = next(get_db())
    competency_service = CompetencyService(db)
    
    # Get all competencies
    competencies = competency_service.get_all_competencies()
    
    if not competencies:
        st.info("Hələ heç bir səriştə yaradılmayıb.")
    else:
        # Select competency for analysis
        competency_options = {f"{c.name} ({c.category or 'Kateqoriyasız'})": c.id for c in competencies}
        selected_competency_name = st.selectbox("Analiz etmək üçün səriştə seçin:", options=list(competency_options.keys()))
        
        if selected_competency_name:
            selected_competency_id = competency_options[selected_competency_name]
            competency = competency_service.get_competency_by_id(selected_competency_id)
            
            if competency:
                st.subheader(f"Analiz: {competency.name}")
                
                # Get performance data for this competency
                # This is a simplified example - in a real implementation, you would need to
                # implement the actual performance calculation logic in the service
                
                # For demonstration, let's show associated questions
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("KPI Sualları:")
                    if competency.kpi_questions:
                        kpi_questions_df = pd.DataFrame([
                            {"ID": q.id, "Sual": q.text[:100] + "..." if len(q.text) > 100 else q.text}
                            for q in competency.kpi_questions
                        ])
                        st.dataframe(kpi_questions_df, use_container_width=True, hide_index=True)
                    else:
                        st.info("Bu səriştə ilə əlaqəli KPI sualı yoxdur.")
                
                with col2:
                    st.write("360° Sualları:")
                    if competency.degree360_questions:
                        degree360_questions_df = pd.DataFrame([
                            {"ID": q.id, "Sual": q.text[:100] + "..." if len(q.text) > 100 else q.text}
                            for q in competency.degree360_questions
                        ])
                        st.dataframe(degree360_questions_df, use_container_width=True, hide_index=True)
                    else:
                        st.info("Bu səriştə ilə əlaqəli 360° sualı yoxdur.")
                
                # Show performance by department (mock data for demonstration)
                st.divider()
                st.subheader("Şöbələr üzrə Performans")
                
                # Mock data for demonstration
                import random
                dept_performance_data = []
                departments = ["İnsan Resursları", "Maliyyə", "Marketinq", "İT", "Satış"]
                
                for dept in departments:
                    dept_performance_data.append({
                        "Şöbə": dept,
                        "Orta Bal": round(random.uniform(3.0, 5.0), 2),
                        "İşçi Sayı": random.randint(5, 20)
                    })
                
                dept_df = pd.DataFrame(dept_performance_data)
                dept_df = dept_df.sort_values("Orta Bal", ascending=False)
                
                st.dataframe(dept_df, use_container_width=True, hide_index=True)
                
                # Chart for department performance
                import altair as alt
                chart = alt.Chart(dept_df).mark_bar().encode(
                    x=alt.X('Orta Bal:Q', scale=alt.Scale(domain=[0, 5])),
                    y=alt.Y('Şöbə:N', sort='-x'),
                    color=alt.Color('Orta Bal:Q', scale=alt.Scale(scheme='blues')),
                    tooltip=['Şöbə', 'Orta Bal']
                ).properties(
                    title=f"'{competency.name}' Səriştəsi üzrə Şöbələr Arası Müqayisə",
                    height=300
                )
                
                st.altair_chart(chart, use_container_width=True)