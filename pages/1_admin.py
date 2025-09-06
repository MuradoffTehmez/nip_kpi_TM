import streamlit as st
st.set_page_config(layout="wide")

import pandas as pd
import numpy as np
from streamlit_cookies_controller import CookieController
from sqlalchemy import select, update, delete
from database import get_db
from utils.utils import download_guide_doc_file, logout, add_data, popup_successful_operation, to_excel, to_excel_formatted_report, get_styled_table_html, check_login
from models.user import User
from models.indicator import Indicator
from models.user_profile import UserProfile
from models.performance import Performance

current_user = check_login()
if current_user.role != "admin":
    st.error("Bu səhifəyə giriş üçün icazəniz yoxdur.")
    st.stop()

controller = CookieController()

st.sidebar.page_link(page="pages/1_admin.py", label="Qiymətləndirmə", icon=":material/grading:")
st.sidebar.page_link(page="pages/3_idarəetmə.py", label="İdarəetmə", icon=":material/settings:")
st.sidebar.page_link(page="pages/4_analitika.py", label="Analitika", icon=":material/monitoring:")
st.sidebar.page_link(page="pages/9_debug.py", label="DEBUG SƏHİFƏSİ", icon="🐞")
download_guide_doc_file()
logout()

with get_db() as session:
    fullnames = sorted(list(set(session.scalars(select(UserProfile.full_name).join(User, UserProfile.user_id==User.id).where(User.role!="admin", User.is_active==True)).all())))
    
    indicators_from_db = session.query(Indicator.id, Indicator.description, Indicator.weight).all()
    indicator_descriptions = [desc for id, desc, w in indicators_from_db]
    indicator_id_map = {id: (desc, w) for id, desc, w in indicators_from_db}

    st.subheader("Fərdi Fəaliyyət Hesabatı Yarat")
    with st.expander("Hesabat üçün işçi və dövr seçin", expanded=True):
        
        def employee_changed():
            st.session_state.report_year = None
            st.session_state.report_month = None

        def year_changed():
            st.session_state.report_month = None

        report_fullname = st.selectbox(
            "İşçi seçin:", options=fullnames, index=None, key="report_employee", on_change=employee_changed
        )
        
        if st.session_state.get("report_employee"):
            report_user_id = session.query(UserProfile.user_id).where(UserProfile.full_name == st.session_state.report_employee).scalar()
            
            if report_user_id:
                available_years = sorted(list(set(session.scalars(
                    select(Performance.evaluation_year).where(Performance.user_id == report_user_id)
                ).all())), reverse=True)
                
                report_year_selection = st.selectbox(
                    "İl seçin:", options=available_years, index=None, key="report_year", on_change=year_changed
                )

                if st.session_state.get("report_year"):
                    available_months = sorted(list(set(session.scalars(
                        select(Performance.evaluation_month).where(
                            Performance.user_id == report_user_id, 
                            Performance.evaluation_year == st.session_state.report_year
                        )
                    ).all())))
                    
                    report_month_selection = st.selectbox(
                        "Qiymətləndirmə növü seçin:", options=available_months, index=None, key="report_month"
                    )

        if st.session_state.get("report_employee") and st.session_state.get("report_year") and st.session_state.get("report_month"):
            performance_records = session.query(
                Performance.indicator_id, Performance.points, Performance.weighted_points
            ).where(
                Performance.user_id == report_user_id,
                Performance.evaluation_year == st.session_state.report_year,
                Performance.evaluation_month == st.session_state.report_month
            ).all()

            if performance_records:
                report_data = []
                total_weighted_score = 0
                for i, record in enumerate(performance_records):
                    indicator_id, points, weighted_points = record
                    indicator_desc, indicator_weight = indicator_id_map.get(indicator_id, ("Naməlum", 0))
                    report_data.append({
                        "S/N": i + 1,
                        "Fəaliyyət üzrə": indicator_desc,
                        "Ümumi qiymət": points,
                        "Yekun qiymətin faiz bölgüsü": int(indicator_weight * 100),
                        "Yekun nəticə faizlə": weighted_points,
                    })
                    total_weighted_score += weighted_points
                
                report_data.append({
                    "S/N": "", "Fəaliyyət üzrə": "Qiymətləndirilmə üzrə yekun nəticə",
                    "Ümumi qiymət": "", "Yekun qiymətin faiz bölgüsü": "",
                    "Yekun nəticə faizlə": round(total_weighted_score, 2),
                })
                report_df = pd.DataFrame(report_data)

                report_df_styled = report_df.rename(columns={
                    "Ümumi qiymət": "Ümumi qiymət (2,3,4,5)",
                    "Yekun qiymətin faiz bölgüsü": "Yekun qiymətin faiz bölgüsü (50,40,10)"
                })

                st.markdown("---")
                
                st.subheader("İşçilərin xidməti fəaliyyətinin qiymətləndirilməsi Forması")
                st.text("Naxçıvan İpoteka Fondu ASC")
                st.text(f'Əmək fəaliyyətinin qiymətləndirilməsi aparılan işçi: {st.session_state.report_employee}')
                
                report_formatters = {"Yekun nəticə faizlə": "{:.2f}"}
                report_alignments = {
                    'center': ['S/N', 'Ümumi qiymət (2,3,4,5)', 'Yekun qiymətin faiz bölgüsü (50,40,10)'],
                    'left': ['Fəaliyyət üzrə']
                }
                
                html_table = get_styled_table_html(report_df_styled.fillna(''), formatters=report_formatters, alignments=report_alignments)
                st.markdown(html_table, unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)
                footer_col1, footer_col2 = st.columns([3, 1])
                with footer_col1:
                    st.text("Qeyd: Qiymətləndirmə apardı İdarə Heyəti sədrinin müavini :")
                    st.markdown("<br><br>", unsafe_allow_html=True)
                    st.text("İdarə Heyətinin sədri:")
                with footer_col2:
                    st.text("R.Quliyev")
                    st.markdown("<br><br>", unsafe_allow_html=True)
                    st.text("Y.Q.Vəliyev")
                st.markdown("<br>", unsafe_allow_html=True)
                
                evaluation_period_str = f"{st.session_state.report_month} {st.session_state.report_year}"
                
                excel_report = to_excel_formatted_report(
                    df=report_df_styled.fillna(''), 
                    employee_name=st.session_state.report_employee,
                    evaluation_period=evaluation_period_str
                )
                st.download_button(
                    label="📥 Formatlı Hesabatı Yüklə",
                    data=excel_report,
                    file_name=f"formalashesabat_{st.session_state.report_employee}.xlsx",
                    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
            else:
                st.warning("Seçilmiş dövr üçün məlumat tapılmadı.")
    st.divider()

    st.subheader("Bütün Qiymətləndirmələr (Toplu Baxış)")
    st.info("Bu cədvəl məlumatları redaktə etmək üçündür və xüsusi dizayna malik deyil.")
    performance_data = session.execute(select(Performance.id, Performance.user_id, Performance.indicator_id, Performance.evaluation_month, Performance.evaluation_year, Performance.points, Performance.weighted_points)).fetchall()
    if len(performance_data) > 0:
        cols = st.columns(5)
        with cols[0]:
            fullnames_chosen = st.multiselect(label="Əməkdaş:", options=fullnames, default=None)
            if not fullnames_chosen: fullnames_chosen = fullnames
            user_ids = session.scalars(select(UserProfile.user_id).where(UserProfile.full_name.in_(fullnames_chosen))).all()
        with cols[1]:
            indicators_chosen = st.multiselect(label="Göstərici:", options=indicator_descriptions, default=None)
            if not indicators_chosen: indicators_chosen = indicator_descriptions
            indicator_ids = session.scalars(select(Indicator.id).where(Indicator.description.in_(indicators_chosen))).all()
        with cols[2]:
            years = sorted(list(set(session.scalars(select(Performance.evaluation_year).where(Performance.user_id.in_(user_ids), Performance.indicator_id.in_(indicator_ids))).all())))
            years_chosen = st.multiselect(label="İl:", options=years, default=None)
            if not years_chosen: years_chosen = years
        with cols[3]:
            months = sorted(list(set(session.scalars(select(Performance.evaluation_month).where(Performance.evaluation_year.in_(years_chosen))).all())))
            months_chosen = st.multiselect(label="Qiymətləndirmə növü:", options=months, default=None)
            if not months_chosen: months_chosen = months
            
        user_id_name_map = dict(session.execute(select(UserProfile.user_id, UserProfile.full_name)).fetchall())
        indicator_id_description_map = {id: desc for id, desc, w in indicators_from_db}
        
        df_for_editor = pd.DataFrame(data=performance_data)
        df_for_editor["user_id"] = df_for_editor["user_id"].map(user_id_name_map)
        df_for_editor["indicator_id"] = df_for_editor["indicator_id"].map(indicator_id_description_map)
        df_for_editor = df_for_editor[(df_for_editor["user_id"].isin(fullnames_chosen)) & (df_for_editor["indicator_id"].isin(indicators_chosen)) & (df_for_editor["evaluation_year"].isin(years_chosen)) & (df_for_editor["evaluation_month"].isin(months_chosen))]
        df_for_editor["check_mark"] = False
        df_for_editor = df_for_editor[["check_mark", "id", "user_id", "indicator_id", "evaluation_month", "evaluation_year", "points", "weighted_points"]]
        
        df_to_export = pd.DataFrame(data=performance_data) 
        df_to_export = df_to_export[df_to_export['id'].isin(df_for_editor['id'])] 
        
        if not df_to_export.empty:
            df_to_export["user_id"] = df_to_export["user_id"].map(user_id_name_map)
            df_to_export["indicator_id"] = df_to_export["indicator_id"].map(indicator_id_description_map)

            df_to_export = df_to_export.rename(columns={
                "user_id": "Əməkdaş",
                "indicator_id": "Göstərici",
                "evaluation_month": "Qiymətləndirmə növü",
                "evaluation_year": "İl",
                "points": "Bal",
                "weighted_points": "Yekun Bal"
            })
            
            desired_order = ["Əməkdaş", "Qiymətləndirmə növü", "İl", "Göstərici", "Bal", "Yekun Bal"]
            df_to_export = df_to_export[desired_order]
            
            excel_data = to_excel(df_to_export)
            st.download_button(label="📥 Bütün siyahını Excel-ə yüklə", data=excel_data, file_name='performance_hesabat_toplu.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

        edited_df = st.data_editor(data=df_for_editor, hide_index=True, column_config={"check_mark": st.column_config.CheckboxColumn(label="", width=1), "id": st.column_config.NumberColumn(label="#id", width=1, disabled=True), "user_id": st.column_config.TextColumn(label="Əməkdaş", width=200, disabled=True), "indicator_id": st.column_config.TextColumn(label="Göstərici", width="large", disabled=True), "evaluation_month": st.column_config.TextColumn(label="Qiymətləndirmə növü", width=80, disabled=True), "evaluation_year": st.column_config.NumberColumn(label="İl", width=30, disabled=True), "points": st.column_config.NumberColumn(label="Bal", min_value=2, max_value=5, width=30), "weighted_points": st.column_config.NumberColumn(label="Yekun bal", width=30, disabled=True),})
        checked_ids = list(edited_df.loc[edited_df["check_mark"]==True, "id"])
        edited_data = {}
        for performance_id in checked_ids:
            current_value = edited_df.loc[edited_df["id"]==performance_id, "points"].iloc[0]
            previous_value = session.query(Performance.points).where(Performance.id==performance_id).scalar()
            if not np.isnan(current_value) and (current_value != previous_value):
                if performance_id not in edited_data: edited_data[performance_id] = {}
                edited_data[performance_id]["points"] = int(current_value)
                indicator_desc = edited_df.loc[edited_df["id"]==performance_id, "indicator_id"].iloc[0]
                weight_to_apply = 0.1
                for id, desc, w in indicators_from_db:
                    if desc == indicator_desc:
                        weight_to_apply = w
                        break
                edited_data[performance_id]["weighted_points"] = (float(current_value) * weight_to_apply)
        data_edited = len(edited_data) > 0
        data_to_delete = len(edited_df.loc[edited_df["check_mark"]==True]) > 0
        cols = st.columns(8)
        with cols[0]:
            if st.button(label="Dəyişdir", icon=":material/edit_note:", disabled=not data_edited):
                try:
                    for performance_id, values in edited_data.items():
                        with get_db() as conn:
                            conn.execute(update(Performance).where(Performance.id==performance_id).values(values))
                            conn.commit()
                    popup_successful_operation()
                except Exception as e:
                    st.error(f"Məlumatları yeniləyərkən xəta baş verdi: {str(e)}")
        @st.dialog("Silmək istədiyinizə əminsinizmi?")
        def popup_delete():
            button_cols = st.columns(6)
            with button_cols[0]:
                if st.button(label="Bəli"):
                    try:
                        ids_to_delete = list(edited_df.loc[edited_df["check_mark"]==True, "id"])
                        with get_db() as conn:
                            conn.execute(delete(Performance).where(Performance.id.in_(ids_to_delete)))
                            conn.commit()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Məlumatları silərkən xəta baş verdi: {str(e)}")
            with button_cols[1]:
                if st.button(label="Xeyr"): st.rerun()
        with cols[1]:
            if st.button(label="Sil", icon=":material/delete:", disabled=not data_to_delete): popup_delete()
        st.divider()
        if st.toggle(label="Yeni Qiymətləndirmə Daxil Et"):
            st.divider()
            add_data()
    else:
        add_data()