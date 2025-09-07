# pages/6_kpi_idarəetmə.py

import streamlit as st
import datetime
from sqlalchemy import func
from database import get_db
from models.user import User
from models.kpi import EvaluationPeriod, Question, Evaluation, EvaluationStatus
from utils.utils import check_login, show_notifications
from services.notification_service import NotificationService

st.set_page_config(layout="wide", page_title="KPI İdarəetmə")

# Təhlükəsizlik yoxlaması
current_user = check_login()

with get_db() as session:
    if current_user.role != 'admin':
        st.error("Bu səhifəyə giriş üçün icazəniz yoxdur.")
        st.stop()

st.sidebar.page_link(page="pages/6_kpi_idarəetmə.py", label="KPI İdarəetmə", icon=":material/settings:")
show_notifications()  # Show notifications in sidebar

st.title("KPI Modulunun İdarə Edilməsi")

tab1, tab2, tab3 = st.tabs(["Qiymətləndirmə Dövrləri", "Suallar", "İstifadəçilər"])

with tab1:
    st.header("Qiymətləndirmə Dövrlərinin İdarə Edilməsi")
    
    with st.expander("➕ Yeni Dövr Yarat", expanded=False):
        with st.form("yeni_dovr_form", clear_on_submit=True):
            period_name = st.text_input("Dövrün adı", placeholder="Məsələn, 2025 - I Rüblük")
            start_date = st.date_input("Başlama tarixi", datetime.date.today())
            end_date = st.date_input("Bitmə tarixi", datetime.date.today() + datetime.timedelta(days=30))
            
            submitted = st.form_submit_button("Dövrü Yarat və Tapşırıqları Təyin Et")
            if submitted and period_name:
                try:
                    with get_db() as session:
                        new_period = EvaluationPeriod(name=period_name, start_date=start_date, end_date=end_date)
                        session.add(new_period)
                        session.flush() # ID-ni almaq üçün

                        users = session.query(User).filter(User.is_active == True).all()
                        for user in users:
                            # Hər istifadəçi üçün özünüqiymətləndirmə tapşırığı
                            self_evaluation = Evaluation(
                                period_id=new_period.id,
                                evaluated_user_id=user.id,
                                evaluator_user_id=user.id,
                                status=EvaluationStatus.PENDING
                            )
                            session.add(self_evaluation)
                        
                        session.commit()
                        
                        # İstifadəçilərə bildiriş göndəririk
                        for user in users:
                            NotificationService.create_notification(
                                user_id=user.id,
                                message=f"Yeni qiymətləndirmə dövrü '{period_name}' yaradıldı. Qiymətləndirmə formunu doldurun."
                            )
                            
                        st.success(f"'{period_name}' dövrü və {len(users)} özünüqiymətləndirmə tapşırığı yaradıldı!")
                        st.rerun()
                except Exception as e:
                    st.error(f"Dövr yaratma zamanı xəta baş verdi: {str(e)}")

    st.markdown("---")
    st.subheader("📊 Mövcud Dövrlər")
    try:
        with get_db() as session:
            periods = session.query(EvaluationPeriod).order_by(EvaluationPeriod.start_date.desc()).all()
            if not periods:
                st.info("Heç bir qiymətləndirmə dövrü yaradılmayıb.")
            else:
                for p in periods:
                    with st.container(border=True):
                        st.subheader(p.name)
                        st.caption(f"Tarix aralığı: {p.start_date.strftime('%d.%m.%Y')} - {p.end_date.strftime('%d.%m.%Y')}")
    except Exception as e:
        st.error(f"Dövrləri yükləyərkən xəta baş verdi: {str(e)}")

with tab2:
    st.header("Sualların İdarə Edilməsi")
    
    # Aktiv sualların çəkilərinin cəmini göstər
    with get_db() as session:
        total_weight_query = session.query(func.sum(Question.weight)).filter(Question.is_active == True)
        current_total_weight = total_weight_query.scalar() or 0.0

        st.warning(f"Diqqət: Aktiv sualların çəkilərinin cəmi 1.0 (100%) olmalıdır. Hazırkı cəm: {current_total_weight:.2f}")
        if abs(current_total_weight - 1.0) > 0.001:
            st.error("Çəkilərin cəmi 1.0 deyil! Zəhmət olmasa, sualları redaktə edərək cəmi 1.0-a bərabərləşdirin.")

    with st.expander("➕ Yeni Sual Əlavə Et", expanded=False):
        with st.form("yeni_sual_form", clear_on_submit=True):
            q_text = st.text_area("Sualın mətni")
            q_category = st.text_input("Kateqoriya", value="Ümumi")
            q_weight = st.number_input("Çəkisi (məsələn, 0.5)", min_value=0.0, max_value=1.0, step=0.01, format="%.2f", value=0.1)
            q_submitted = st.form_submit_button("Əlavə et")
            if q_submitted and q_text:
                try:
                    with get_db() as session:
                        # Yeni sual əlavə etməzdən əvvəl çəki cəmini yoxlayırıq
                        total_weight_query = session.query(func.sum(Question.weight)).filter(Question.is_active == True)
                        current_total_weight = total_weight_query.scalar() or 0.0
                        
                        if current_total_weight + q_weight > 1.0:
                            st.error(f"Yeni sual əlavə etmək mümkün deyil! Cəm {current_total_weight + q_weight:.2f} olacaq, lakin maksimum 1.0 ola bilər.")
                        else:
                            new_question = Question(text=q_text, category=q_category, weight=q_weight)
                            session.add(new_question)
                            session.commit()
                            st.success("Yeni sual əlavə edildi!")
                            st.rerun()
                except Exception as e:
                    st.error(f"Sual əlavə edərkən xəta baş verdi: {str(e)}")

    st.markdown("---")
    st.subheader("❓ Mövcud Suallar")
    try:
        with get_db() as session:
            questions = session.query(Question).all()
            st.dataframe(
                [{"ID": q.id, "Kateqoriya": q.category, "Sual": q.text, "Çəki": q.weight, "Aktiv": q.is_active} for q in questions],
                use_container_width=True
            )
    except Exception as e:
        st.error(f"Sualları yükləyərkən xəta baş verdi: {str(e)}")

with tab3:
    st.header("İstifadəçilər")
    try:
        with get_db() as session:
            users = session.query(User).all()
            st.dataframe(
                [{"ID": u.id, "Ad Soyad": u.get_full_name(), "İstifadəçi adı": u.username, "Rol": u.role, "Aktiv": u.is_active} for u in users],
                use_container_width=True
            )
    except Exception as e:
        st.error(f"İstifadəçiləri yükləyərkən xəta baş verdi: {str(e)}")