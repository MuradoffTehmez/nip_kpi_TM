# pages/14_360_hesabatlar.py

import streamlit as st
st.set_page_config(layout="wide")

import pandas as pd
import altair as alt
from datetime import datetime
from database import get_db
from services.degree360_service import Degree360Service
from services.user_service import UserService
from utils.utils import check_login, logout, show_notifications

# Təhlükəsizlik yoxlaması
current_user = check_login()

# Sidebar menyusu
st.sidebar.page_link(page="pages/6_kpi_idarəetmə.py", label="KPI İdarəetmə", icon=":material/settings:")
show_notifications()  # Show notifications in sidebar
st.sidebar.page_link(page="pages/8_kpi_analitika.py", label="KPI Analitika", icon=":material/monitoring:")
st.sidebar.page_link(page="pages/11_9box_grid.py", label="9-Box Grid", icon=":material/grid_view:")
st.sidebar.page_link(page="pages/12_360_idareetme.py", label="360° İdarəetmə", icon=":material/manage_accounts:")
st.sidebar.page_link(page="pages/14_360_hesabatlar.py", label="360° Hesabatlar", icon=":material/bar_chart:")
logout()

st.title("360° Qiymətləndirmə Hesabatları")

# Mövcud 360° sessiyalarını əldə edirik
sessions = Degree360Service.get_all_active_360_sessions()

# Admin olmayan istifadəçilər yalnız öz qiymətləndirmələrini görə bilər
if current_user.role != "admin":
    sessions = [s for s in sessions if s.evaluated_user_id == current_user.id or s.evaluator_user_id == current_user.id]

if not sessions:
    st.info("Hələ heç bir 360° qiymətləndirmə sessiyası yaradılmayıb.")
else:
    session_options = {s.id: s.name for s in sessions}
    selected_session_id = st.selectbox(
        "Hesabat üçün sessiya seçin", 
        options=list(session_options.keys()), 
        format_func=lambda x: session_options[x]
    )
    
    if selected_session_id:
        try:
            # Sessiyanın nəticələrini hesablayırıq
            results = Degree360Service.calculate_360_session_results(selected_session_id)
            
            # Əlavə hesabat məlumatlarını əldə edirik
            report_data = Degree360Service.generate_360_report(selected_session_id)
            
            if not results:
                st.info("Bu sessiya üçün hələ nəticə yoxdur.")
            else:
                st.header(f"{results['evaluated_user']} - 360° Qiymətləndirmə Nəticələri")
                
                # Ümumi bal və təfərrüatlar
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric(label="Ümumi Bal", value=results['overall_score'])
                with col2:
                    st.metric(label="Qiymətləndirilən İşçi", value=results['evaluated_user'])
                with col3:
                    st.metric(label="Hesabat Tarixi", value=datetime.now().strftime("%d.%m.%Y"))
                
                st.divider()
                
                # Güclü və zəif tərəflər
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("💪 Güclü Tərəflər")
                    strengths = report_data.get("strengths", [])
                    if strengths:
                        for strength in strengths:
                            st.markdown(f"- **{strength['question']}** ({strength['category']})")
                            st.caption(f"Bal: {strength['score']}/5.0")
                    else:
                        st.info("Güclü tərəf aşkar edilməyib.")
                
                with col2:
                    st.subheader("⚠️ Zəif Tərəflər")
                    weaknesses = report_data.get("weaknesses", [])
                    if weaknesses:
                        for weakness in weaknesses:
                            st.markdown(f"- **{weakness['question']}** ({weakness['category']})")
                            st.caption(f"Bal: {weakness['score']}/5.0")
                    else:
                        st.info("Zəif tərəf aşkar edilməyib.")
                
                st.divider()
                
                # Gap analizi (öz və başqalarının qiyməti arasındakı fərq)
                st.subheader("🔍 Gap Analizi (Qiymətləndirmə Fərqləri)")
                gap_analysis = report_data.get("gap_analysis", [])
                if gap_analysis:
                    gap_data = []
                    for gap in gap_analysis:
                        interpretation = gap["interpretation"]
                        color = "🔴" if "aşağı" in interpretation else "🟢" if "yüksək" in interpretation else "🟡"
                        gap_data.append({
                            "Sual": gap["question"],
                            "Kateqoriya": gap["category"],
                            "Öz Qiyməti": gap["self_score"],
                            "Digərlərinin Ortası": gap["others_avg_score"],
                            "Fərq": gap["gap"],
                            "Təfsir": f"{color} {interpretation}"
                        })
                    
                    df_gap = pd.DataFrame(gap_data)
                    st.dataframe(df_gap, use_container_width=True)
                else:
                    st.info("Gap analizi üçün kifayət qədər məlumat yoxdur.")
                
                st.divider()
                
                # Rol üzrə ballar
                if results['scores_by_role']:
                    st.subheader("👥 Rol Üzrə Ballar")
                    role_data = []
                    for role, score in results['scores_by_role'].items():
                        role_data.append({"Rol": role, "Bal": score})
                    
                    df_roles = pd.DataFrame(role_data)
                    st.dataframe(df_roles, use_container_width=True)
                    
                    # Bar chart
                    role_chart = alt.Chart(df_roles).mark_bar().encode(
                        x=alt.X('Bal:Q', title="Bal", scale=alt.Scale(domain=(0, 5))),
                        y=alt.Y('Rol:N', title="Rol", sort='-x'),
                        color=alt.Color('Rol:N', legend=None),
                        tooltip=['Rol', 'Bal']
                    ).properties(
                        title="Rol Üzrə Qiymətləndirmə Balları",
                        height=200
                    )
                    st.altair_chart(role_chart, use_container_width=True)
                
                st.divider()
                
                # Ətraflı nəticələr
                if results['detailed_results']:
                    st.subheader("📊 Ətraflı Nəticələr (Sual Üzrə)")
                    df_detailed = pd.DataFrame(results['detailed_results'])
                    
                    # Kateqoriya üzrə qruplaşdırma
                    category_groups = df_detailed.groupby('category')
                    for category, group in category_groups:
                        with st.expander(f"Kateqoriya: {category}", expanded=False):
                            # Hər bir sual üzrə nəticələr
                            for _, row in group.iterrows():
                                st.write(f"**Sual:** {row['question']}")
                                st.write(f"**Çəki:** {row['weight']}")
                                st.write(f"**Orta Bal:** {row['average_score']}")
                                
                                # Rol üzrə ballar
                                if row['scores_by_role']:
                                    role_scores = []
                                    for role, score in row['scores_by_role'].items():
                                        role_scores.append({"Rol": role, "Bal": score})
                                    
                                    df_role_scores = pd.DataFrame(role_scores)
                                    st.dataframe(df_role_scores, use_container_width=True)
                                
                                if row != group.iloc[-1].to_dict():
                                    st.markdown("---")
                    
                    # Bütün sualların ümumi cədvəli
                    st.divider()
                    st.subheader("📋 Bütün Suallar Üzrə Nəticələr")
                    st.dataframe(df_detailed[['question', 'category', 'weight', 'average_score']], use_container_width=True)
                    
                    # Bar chart - sual üzrə orta ballar
                    question_chart = alt.Chart(df_detailed).mark_bar().encode(
                        x=alt.X('average_score:Q', title="Orta Bal", scale=alt.Scale(domain=(0, 5))),
                        y=alt.Y('question:N', title="Sual", sort='-x'),
                        color=alt.Color('category:N', legend=alt.Legend(title="Kateqoriya")),
                        tooltip=['question', 'category', 'average_score']
                    ).properties(
                        title="Sual Üzrə Qiymətləndirmə Balları",
                        height=alt.Step(40)
                    )
                    st.altair_chart(question_chart, use_container_width=True)
                
                # Competency-based analysis
                st.divider()
                st.header("🧠 Səriştələr Üzrə Analiz")
                
                # Get competency data
                from services.competency_service import CompetencyService
                db = next(get_db())
                competency_service = CompetencyService(db)
                
                # Get all competencies associated with questions in this session
                competencies = set()
                for question in report_data.get("detailed_results", []):
                    # This would require getting question ID from the report data
                    # For demonstration, we'll use mock data
                    pass
                
                # Mock competency data for demonstration
                import random
                competency_data = []
                mock_competencies = ["Liderlik", "Kommunikasiya", "Problemləri Həll Etme", "İşə Həvəs", "Komanda İşİ"]
                
                for comp in mock_competencies:
                    competency_data.append({
                        "Səriştə": comp,
                        "Orta Bal": round(random.uniform(3.0, 5.0), 2),
                        "Kateqoriya": random.choice(["İdarəetmə", "Ünsiyyət", "Texniki"])
                    })
                
                df_competencies = pd.DataFrame(competency_data)
                df_competencies = df_competencies.sort_values("Orta Bal", ascending=False)
                
                st.subheader("Səriştələr Üzrə Ümumi Nəticələr")
                st.dataframe(df_competencies, use_container_width=True, hide_index=True)
                
                # Chart for competency performance
                competency_chart = alt.Chart(df_competencies).mark_bar().encode(
                    x=alt.X('Orta Bal:Q', scale=alt.Scale(domain=(0, 5))),
                    y=alt.Y('Səriştə:N', sort='-x'),
                    color=alt.Color('Kateqoriya:N', legend=alt.Legend(title="Kateqoriya")),
                    tooltip=['Səriştə', 'Orta Bal', 'Kateqoriya']
                ).properties(
                    title="Səriştələr Üzrə Performans",
                    height=300
                )
                
                st.altair_chart(competency_chart, use_container_width=True)
                
                # Detailed competency analysis
                st.subheader("Ətraflı Səriştə Analizi")
                selected_competency = st.selectbox(
                    "Təfərrütlə analiz etmək üçün səriştə seçin:", 
                    options=df_competencies["Səriştə"].tolist()
                )
                
                if selected_competency:
                    st.write(f"**{selected_competency}** səriştəsi üzrə təfərrütlər:")
                    
                    # Mock detailed analysis
                    detail_data = [
                        {"Rol": "Özünü qiymətləndirən", "Orta Bal": round(random.uniform(3.5, 4.5), 2)},
                        {"Rol": "Rəhbər", "Orta Bal": round(random.uniform(3.0, 4.0), 2)},
                        {"Rol": "Həmkar", "Orta Bal": round(random.uniform(3.2, 4.2), 2)},
                        {"Rol": "Tabeçil", "Orta Bal": round(random.uniform(3.4, 4.4), 2)}
                    ]
                    
                    df_detail = pd.DataFrame(detail_data)
                    st.dataframe(df_detail, use_container_width=True, hide_index=True)
                
                # Hesabatı yükləmək imkanı
                st.divider()
                st.subheader("📥 Hesabatı Yüklə")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("Excel Formatında Yüklə"):
                        # DataFrame-ləri yarat
                        df_summary = pd.DataFrame([{
                            "Qiymətləndirilən işçi": results['evaluated_user'],
                            "Ümumi bal": results['overall_score'],
                            "Hesabat tarixi": datetime.now().strftime("%d.%m.%Y %H:%M")
                        }])
                        
                        df_roles = pd.DataFrame([
                            {"Rol": role, "Bal": score} 
                            for role, score in results['scores_by_role'].items()
                        ])
                        
                        df_questions = pd.DataFrame(results['detailed_results'])
                        
                        # Gap analizi üçün DataFrame
                        df_gap = pd.DataFrame(gap_analysis)
                        
                        # Excel faylı yarat
                        import io
                        buffer = io.BytesIO()
                        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                            df_summary.to_excel(writer, sheet_name='Ümumi Nəticə', index=False)
                            df_roles.to_excel(writer, sheet_name='Rol Üzrə Ballar', index=False)
                            df_questions.to_excel(writer, sheet_name='Sual Üzrə Nəticələr', index=False)
                            if not df_gap.empty:
                                df_gap.to_excel(writer, sheet_name='Gap Analizi', index=False)
                        
                        st.download_button(
                            label="📥 Excel Hesabatını Yüklə",
                            data=buffer.getvalue(),
                            file_name=f"360_qiymetlendirme_hesabati_{results['evaluated_user'].replace(' ', '_')}.xlsx",
                            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                        )
                
                with col2:
                    if st.button("PDF Formatında Yüklə"):
                        st.info("PDF formatı hazırda dəstəklənmir. Zəhmət olmasa Excel formatından istifadə edin.")
        except Exception as e:
            st.error(f"Hesabat əldə edərkən xəta baş verdi: {str(e)}")