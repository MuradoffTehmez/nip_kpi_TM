import streamlit as st
from streamlit_cookies_controller import CookieController
controller = CookieController()

from sqlalchemy import select, insert
from database import get_db

from data.months_in_azeri import evaluation_types

from models.user import User
from models.indicator import Indicator
from models.user_profile import UserProfile
from models.performance import Performance

import io
import pandas as pd


def check_login():
    """Centralized login check for all pages"""
    if 'user_id' not in st.session_state:
        st.warning("Bu səhifəyə baxmaq üçün sistemə daxil olmalısınız.")
        st.link_button("Giriş səhifəsi", "/")
        st.stop()
    
    with get_db() as session:
        user = session.query(User).where(User.id == st.session_state['user_id'], User.is_active == True).scalar()
        if not user:
            st.error("İstifadəçi tapılmadı və ya deaktiv edilib.")
            st.stop()
        return user


def get_subordinates(manager_id):
    """Get all subordinates for a manager"""
    with get_db() as session:
        subordinates = session.query(User).filter(User.manager_id == manager_id, User.is_active == True).all()
        return subordinates


def check_upcoming_evaluations():
    """Check for evaluations that are approaching deadlines"""
    from models.kpi import Evaluation, EvaluationPeriod
    from datetime import datetime, timedelta
    
    with get_db() as session:
        # Find evaluations that are due in the next 7 days
        upcoming_evaluations = session.query(Evaluation, EvaluationPeriod, User).join(
            EvaluationPeriod, Evaluation.period_id == EvaluationPeriod.id
        ).join(
            User, Evaluation.evaluated_user_id == User.id
        ).filter(
            EvaluationPeriod.end_date >= datetime.now().date(),
            EvaluationPeriod.end_date <= (datetime.now() + timedelta(days=7)).date(),
            Evaluation.status == "PENDING"
        ).all()
        
        return upcoming_evaluations


def show_notifications():
    """Show notifications to the user"""
    from models.kpi import Evaluation, EvaluationPeriod
    from datetime import datetime, timedelta
    
    # Check for upcoming evaluations
    upcoming_evals = check_upcoming_evaluations()
    
    if upcoming_evals:
        st.sidebar.warning("⚠️ Yakınlaşan Qiymətləndirmələr")
        for eval, period, user in upcoming_evals:
            days_until_due = (period.end_date - datetime.now().date()).days
            if days_until_due == 0:
                st.sidebar.warning(f"Bugün son tarix: {period.name} qiymətləndirməsi")
            else:
                st.sidebar.warning(f"{days_until_due} gün sonra son tarix: {period.name} qiymətləndirməsi")


def download_guide_doc_file():
    with st.sidebar:
        with open('./data/qiymətləndirmə.docx', 'rb') as f:
            st.download_button(label="Qiymətləndirmə təlimatı",
                data=f,
                file_name="Qiymətləndirmə təlimatı.docx",
                icon="📥"
            )


def logout():
    with st.sidebar:
        st.divider()
        if st.button(label="Çıxış", icon=":material/logout:"):
            st.query_params["logout"] = "true"
            st.switch_page("main.py")
            
@st.dialog("Uğurlu əməliyyat!")
def popup_successful_operation():
    if st.button(label="", icon=":material/thumb_up:"):
        st.rerun()


def add_data():
    try:
        with get_db() as session:
            fullnames = sorted(list(set(session.scalars(
                select(UserProfile.full_name)
                .join(User, UserProfile.user_id == User.id)
                .where(User.role != "admin", User.is_active == True)
            ).all())))
            
            active_indicators = session.query(Indicator).filter(Indicator.is_active == True).all()

            cols = st.columns(3)
            with cols[0]:
                fullname_to_evaluate = st.selectbox(label="Əməkdaş:", options=fullnames, index=None)
            with cols[1]:
                year_to_evaluate = st.selectbox(label="İl:", options=[2024, 2025, 2026], index=None)
            with cols[2]:
                month_to_evaluate = st.selectbox(label="Qiymətləndirmə növü:", options=evaluation_types, index=None)
            
            if fullname_to_evaluate and year_to_evaluate and month_to_evaluate:
                user_id_to_evaluate = session.query(UserProfile.user_id).where(UserProfile.full_name == fullname_to_evaluate).scalar()
                
                existing_performance = session.query(Performance).filter(
                    Performance.user_id == user_id_to_evaluate,
                    Performance.evaluation_year == year_to_evaluate,
                    Performance.evaluation_month == month_to_evaluate
                ).first()

                if existing_performance:
                    st.divider()
                    st.error("***Seçdiyiniz əməkdaşın qeyd etdiyiniz dövr üzrə qiymətləndirməsi artıq mövcuddur!***")
                else:
                    st.divider()
                    st.subheader(f"'{fullname_to_evaluate}' üçün balları daxil edin:")

                    with st.form("new_performance_form"):
                        points_data = {}
                        for indicator in active_indicators:
                            points_data[indicator.id] = st.number_input(
                                label=f"**{indicator.description}** (Çəkisi: {indicator.weight * 100:.0f}%)",
                                min_value=2, max_value=5, value=None, key=f"points_{indicator.id}"
                            )

                        submitted = st.form_submit_button("Qiymətləndirməni Əlavə Et")

                        if submitted:
                            if any(point is None for point in points_data.values()):
                                st.warning("Zəhmət olmasa, bütün göstəricilər üçün bal daxil edin.")
                            else:
                                try:
                                    performance_records_to_add = []
                                    for indicator in active_indicators:
                                        points = points_data[indicator.id]
                                        weighted_points = points * indicator.weight
                                        
                                        performance_records_to_add.append({
                                            "user_id": user_id_to_evaluate,
                                            "indicator_id": indicator.id,
                                            "evaluation_year": year_to_evaluate,
                                            "evaluation_month": month_to_evaluate,
                                            "points": points,
                                            "weighted_points": weighted_points
                                        })
                                    
                                    session.execute(insert(Performance), performance_records_to_add)
                                    session.commit()
                                    st.success(f"'{fullname_to_evaluate}' üçün qiymətləndirmə uğurla əlavə edildi!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Qiymətləndirmə əlavə edərkən xəta baş verdi: {str(e)}")
    except Exception as e:
        st.error(f"Məlumat əlavə etmə formunu yükləyərkən xəta baş verdi: {str(e)}")


def to_excel(df: pd.DataFrame):
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Performance_Hesabat')
    writer.close()
    processed_data = output.getvalue()
    return processed_data


def to_excel_formatted_report(df: pd.DataFrame, employee_name: str, evaluation_period: str):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Hesabat', startrow=3)

        workbook = writer.book
        worksheet = writer.sheets['Hesabat']
        header_format = workbook.add_format({'bold': True, 'font_size': 12, 'align': 'center', 'valign': 'vcenter'})
        subheader_format = workbook.add_format({'bold': True, 'font_size': 11, 'align': 'left'})
        table_header_format = workbook.add_format({'bold': True, 'border': 1, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#DDEBF7', 'text_wrap': True})

        worksheet.merge_range('A1:E1', 'İşçilərin xidməti fəaliyyətinin qiymətləndirilməsi Forması', header_format)
        worksheet.merge_range('A2:E2', 'Naxçıvan İpoteka Fondu ASC', subheader_format)
        worksheet.merge_range('A3:E3', f'Əmək fəaliyyətinin qiymətləndirilməsi aparılan işçi: {employee_name}', subheader_format)

        for col_num, value in enumerate(df.columns.values):
            worksheet.write(3, col_num, value, table_header_format)
        
        worksheet.set_column('A:A', 5)   # S/N
        worksheet.set_column('B:B', 60)  # Fəaliyyət üzrə
        worksheet.set_column('C:C', 20)  # Ümumi qiymət
        worksheet.set_column('D:D', 25)  # Faiz bölgüsü
        worksheet.set_column('E:E', 20)  # Yekun nəticə

        footer_start_row = 4 + len(df) + 2
        worksheet.write(f'B{footer_start_row}', 'Qeyd: Qiymətləndirmə apardı İdarə Heyəti sədrinin müavini :')
        worksheet.write(f'E{footer_start_row}', 'R.Quliyev')
        worksheet.write(f'B{footer_start_row + 2}', 'İdarə Heyətinin sədri:')
        worksheet.write(f'E{footer_start_row + 2}', 'Y.Q.Vəliyev')

    processed_data = output.getvalue()
    return processed_data


def get_styled_table_html(df: pd.DataFrame, formatters: dict = None, alignments: dict = None):
    
    header_properties = list({
        'background-color': '#DDEBF7', 'color': 'black', 'font-weight': 'bold',
        'text-align': 'center', 'border': '1px solid #B0B0B0'
    }.items())
    
    cell_properties = list({
        'border': '1px solid #B0B0B0'
    }.items())
    
    styler = df.style.set_table_styles([
        {'selector': 'th', 'props': header_properties},
        {'selector': 'td', 'props': cell_properties}
    ])
    
    if formatters:
        styler.format(formatters, na_rep="")
    
    if alignments:
        for align, columns in alignments.items():
            styler.set_properties(subset=columns, **{'text-align': align})

    styler.hide(axis="index")
    return styler.to_html()