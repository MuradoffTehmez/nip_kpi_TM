# pages/1_admin.py

import streamlit as st
st.set_page_config(layout="wide")

import pandas as pd
from database import get_db
from services.kpi_service import KpiService
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
if current_user.role != "admin":
    st.error("Bu səhifəyə giriş üçün icazəniz yoxdur.")
    st.stop()

# Sidebar menyusu
st.sidebar.page_link(page="pages/1_admin.py", label="Qiymətləndirmə", icon=":material/grading:")
show_notifications()  # Show notifications in sidebar
st.sidebar.page_link(page="pages/3_idarəetmə.py", label="İdarəetmə", icon=":material/settings:")
st.sidebar.page_link(page="pages/6_kpi_idarəetmə.py", label="KPI İdarəetmə", icon=":material/manage_accounts:")
st.sidebar.page_link(page="pages/8_kpi_analitika.py", label="KPI Analitika", icon=":material/monitoring:")
download_guide_doc_file()
logout()

st.title("Qiymətləndirmə İdarəetmə Paneli")

# Qiymətləndirmə dövrlərini əldə edirik
periods = KpiService.get_all_evaluation_periods()

if not periods:
    st.info("Hələ heç bir qiymətləndirmə dövrü yaradılmayıb.")
else:
    # Dövr seçimi
    period_options = [p.name for p in periods]
    selected_period_name = st.selectbox("Qiymətləndirmə dövrünü seçin:", options=period_options, index=0)
    selected_period = next((p for p in periods if p.name == selected_period_name), None)

    if selected_period:
        period_id = selected_period.id
        st.subheader(f"Seçilmiş Dövr: {selected_period.name}")
        st.caption(f"Tarix aralığı: {selected_period.start_date.strftime('%d.%m.%Y')} - {selected_period.end_date.strftime('%d.%m.%Y')}")

        # Qiymətləndirmələri əldə edirik
        with get_db() as session:
            from models.kpi import Evaluation, EvaluationStatus
            from models.user import User
            
            evaluations = session.query(Evaluation).filter(Evaluation.period_id == period_id).all()
            
            if not evaluations:
                st.info("Bu dövr üçün hələ qiymətləndirmə yaradılmayıb.")
            else:
                # Qiymətləndirmə məlumatlarını hazırlayırıq
                eval_data = []
                for eval in evaluations:
                    evaluated_user = UserService.get_user_by_id(eval.evaluated_user_id)
                    evaluator_user = UserService.get_user_by_id(eval.evaluator_user_id)
                    
                    eval_data.append({
                        "id": eval.id,
                        "evaluated_user": evaluated_user.get_full_name() if evaluated_user else "Naməlum",
                        "evaluator_user": evaluator_user.get_full_name() if evaluator_user else "Naməlum",
                        "status": eval.status.value,
                        "end_date": selected_period.end_date.strftime('%d.%m.%Y')
                    })
                
                df_evaluations = pd.DataFrame(eval_data)
                df_evaluations = df_evaluations.rename(columns={
                    "evaluated_user": "Qiymətləndirilən",
                    "evaluator_user": "Qiymətləndirən",
                    "status": "Status",
                    "end_date": "Son Tarix"
                })
                
                # Statusa görə rəngləmə
                def highlight_status(s):
                    if s["Status"] == "GÖZLƏMƏDƏ":
                        return ['background-color: #fff3cd'] * len(s)
                    elif s["Status"] == "TAMAMLANMIŞ":
                        return ['background-color: #d4edda'] * len(s)
                    else:
                        return [''] * len(s)
                
                st.dataframe(
                    df_evaluations.style.apply(highlight_status, axis=1),
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "id": st.column_config.NumberColumn(label="#", width=50),
                        "Qiymətləndirilən": st.column_config.TextColumn(width=200),
                        "Qiymətləndirən": st.column_config.TextColumn(width=200),
                        "Status": st.column_config.TextColumn(width=120),
                        "Son Tarix": st.column_config.TextColumn(width=100)
                    }
                )
                
                # Hesabat yaratma funksionallığı
                st.divider()
                st.subheader("Hesabat Yarat")
                
                # İstifadəçi seçimi üçün dropdown
                user_options = [u.get_full_name() for u in UserService.get_all_active_users() if u.role != "admin"]
                selected_user_name = st.selectbox("Hesabat üçün işçi seçin:", options=user_options, index=0)
                
                if st.button("Hesabat Yarat"):
                    # Seçilmiş istifadəçinin ID-sini tapırıq
                    selected_user = next((u for u in UserService.get_all_active_users() if u.get_full_name() == selected_user_name), None)
                    if selected_user:
                        # İstifadəçinin bu dövrdə qiymətləndirilməsini tapırıq
                        user_evaluations = [e for e in evaluations if e.evaluated_user_id == selected_user.id]
                        
                        if not user_evaluations:
                            st.warning(f"{selected_user_name} bu dövr üçün qiymətləndirilməyib.")
                        else:
                            # Qiymətləndirmənin yekun balını hesablayırıq
                            scores = [KpiService.calculate_evaluation_score(e.id) for e in user_evaluations]
                            avg_score = sum(scores) / len(scores) if scores else 0
                            
                            # Hesabat məlumatlarını hazırlayırıq (sadələşdirilmiş format)
                            report_data = [{
                                "S/N": 1,
                                "Fəaliyyət üzrə": "Ümumi Performans",
                                "Ümumi qiymət (2,3,4,5)": round(avg_score, 2),
                                "Yekun qiymətin faiz bölgüsü (50,40,10)": 100,
                                "Yekun nəticə faizlə": round(avg_score, 2),
                            }]
                            
                            # Yekun nəticə sətri
                            report_data.append({
                                "S/N": "",
                                "Fəaliyyət üzrə": "Qiymətləndirilmə üzrə yekun nəticə",
                                "Ümumi qiymət (2,3,4,5)": "",
                                "Yekun qiymətin faiz bölgüsü (50,40,10)": "",
                                "Yekun nəticə faizlə": round(avg_score, 2),
                            })
                            
                            report_df = pd.DataFrame(report_data)
                            
                            # Hesabatı göstəririk
                            st.markdown("---")
                            st.subheader("İşçilərin xidməti fəaliyyətinin qiymətləndirilməsi Forması")
                            st.text("Naxçıvan İpoteka Fondu ASC")
                            st.text(f'Əmək fəaliyyətinin qiymətləndirilməsi aparılan işçi: {selected_user_name}')
                            
                            report_formatters = {"Yekun nəticə faizlə": "{:.2f}"}
                            report_alignments = {
                                'center': ['S/N', 'Ümumi qiymət (2,3,4,5)', 'Yekun qiymətin faiz bölgüsü (50,40,10)'],
                                'left': ['Fəaliyyət üzrə']
                            }
                            
                            html_table = get_styled_table_html(report_df.fillna(''), formatters=report_formatters, alignments=report_alignments)
                            st.markdown(html_table, unsafe_allow_html=True)
                            
                            # Excel export
                            excel_report = to_excel_formatted_report(
                                df=report_df.fillna(''), 
                                employee_name=selected_user_name,
                                evaluation_period=selected_period.name
                            )
                            st.download_button(
                                label="📥 Formatlı Hesabatı Yüklə",
                                data=excel_report,
                                file_name=f"formalashesabat_{selected_user_name}_{selected_period.name}.xlsx",
                                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                            )