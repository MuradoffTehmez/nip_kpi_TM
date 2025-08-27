# muradofftehmez/nip_kpi_tm/pages/1_admin.py

import streamlit as st, pandas as pd, numpy as np
from streamlit_cookies_controller import CookieController
controller = CookieController()

st.set_page_config(layout="wide")

from sqlalchemy import select, update, delete
from database import get_db
from utils.utils import download_guide_doc_file, logout, add_data, popup_successful_operation, to_excel

from models.user import User
from models.indicator import Indicator
from models.user_profile import UserProfile
from models.performance import Performance


st.sidebar.page_link(page="./pages/1_admin.py", label="Qiymətləndirmə", icon=":material/grading:")
download_guide_doc_file()


with get_db() as session:
    fullnames = list(set(session.scalars(select(UserProfile.full_name).join(User, UserProfile.user_id==User.id).where(User.role!="admin", User.is_active==True)).all()))
    indicator_descriptions = session.scalars(select(Indicator.description)).all()


    performance_data = session.execute(select(Performance.id,
                                              Performance.user_id, Performance.indicator_id, 
                                              Performance.evaluation_month, Performance.evaluation_year, 
                                              Performance.points, Performance.weighted_points)).fetchall()
    if len(performance_data) > 0:
        cols = st.columns(5)
        with cols[0]:
            fullnames_chosen = st.multiselect(label="Əməkdaş:", options=fullnames, default=None)
            if not fullnames_chosen:
                fullnames_chosen = fullnames
            user_ids = session.scalars(select(UserProfile.user_id).where(UserProfile.full_name.in_(fullnames_chosen))).all()
        with cols[1]:
            indicators_chosen = st.multiselect(label="Göstərici:", options=indicator_descriptions, default=None)
            if not indicators_chosen:
                indicators_chosen = indicator_descriptions
            indicator_ids = session.scalars(select(Indicator.id).where(Indicator.description.in_(indicators_chosen))).all()
        with cols[2]:
            years = list(set(session.scalars(select(Performance.evaluation_year).where(Performance.user_id.in_(user_ids), Performance.indicator_id.in_(indicator_ids))).all()))
            years_chosen = st.multiselect(label="İl:", options=years, default=None)
            if not years_chosen:
                years_chosen = years
        with cols[3]:
            months = list(set(session.scalars(select(Performance.evaluation_month).where(Performance.evaluation_year.in_(years_chosen))).all()))

            months_chosen = st.multiselect(label="Qiymətləndirmə növü:", options=months, default=None)
            if not months_chosen:
                months_chosen = months


        user_id_name_map = dict(session.execute(select(UserProfile.user_id, UserProfile.full_name)).fetchall())
        indicator_id_description_map = dict(session.execute(select(Indicator.id, Indicator.description)).fetchall())     

        df = pd.DataFrame(data=performance_data)
        df["user_id"] = df["user_id"].map(user_id_name_map)
        df["indicator_id"] = df["indicator_id"].map(indicator_id_description_map)
        df = df[(df["user_id"].isin(fullnames_chosen)) & 
                (df["indicator_id"].isin(indicators_chosen)) & 
                (df["evaluation_year"].isin(years_chosen)) & 
                (df["evaluation_month"].isin(months_chosen))]
        df["check_mark"] = False
        df = df[[
                    "check_mark", "id", 
                    "user_id", "indicator_id",
                    "evaluation_month", "evaluation_year",
                    "points", "weighted_points"
                ]]

        
        # Yükləmə üçün UI-a xas sütunları cədvəldən çıxaraq
        df_to_export = df.drop(columns=['check_mark', 'id'])

        # Cədvəl boş deyilsə, yükləmə düyməsini göstər
        if not df_to_export.empty:
            excel_data = to_excel(df_to_export)
            st.download_button(
                label="📥 Excel-ə yüklə",
                data=excel_data,
                file_name='performance_hesabat.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        

        st.divider()
        edited_df = st.data_editor(data=df, hide_index=True, 
                    column_config={
                        "check_mark": st.column_config.CheckboxColumn(label="", width=1),
                        "id": st.column_config.NumberColumn(label="#id", width=1, disabled=True),
                        "user_id": st.column_config.TextColumn(label="Əməkdaş", width=200, disabled=True),
                        "indicator_id": st.column_config.TextColumn(label="Göstərici", width="large", disabled=True),
                        "evaluation_month": st.column_config.TextColumn(label="Qiymətləndirmə növü", width=80, disabled=True),
                        "evaluation_year": st.column_config.NumberColumn(label="İl", width=30, disabled=True),
                        "points": st.column_config.NumberColumn(label="Bal", min_value=2, max_value=5, width=30),
                        "weighted_points": st.column_config.NumberColumn(label="Yekun bal", width=30, disabled=True),
                    }
                )
                
        checked_ids = list(edited_df.loc[edited_df["check_mark"]==True, "id"])
        edited_data = {}
        for performance_id in checked_ids:
            current_value = edited_df.loc[edited_df["id"]==performance_id, "points"].iloc[0]
            previous_value = session.query(Performance.points).where(Performance.id==performance_id).scalar()

            if not np.isnan(current_value) and (current_value != previous_value):
                if performance_id not in edited_data:
                    edited_data[performance_id] = {}
                edited_data[performance_id]["points"] = int(current_value)

                indicator_desc = edited_df.loc[edited_df["id"]==performance_id, "indicator_id"].iloc[0]
                if indicator_desc == indicator_descriptions[0]:
                    edited_data[performance_id]["weighted_points"] = (float(current_value) * 0.5)
                elif indicator_desc == indicator_descriptions[1]:
                    edited_data[performance_id]["weighted_points"] = (float(current_value) * 0.4)
                elif indicator_desc == indicator_descriptions[2]:
                    edited_data[performance_id]["weighted_points"] = (float(current_value) * 0.1)   
        
        data_edited = len(edited_data) > 0
        data_to_delete = len(edited_df.loc[edited_df["check_mark"]==True]) > 0
        
        cols = st.columns(8)
        with cols[0]:
            if st.button(label="Dəyişdir", icon=":material/edit_note:", disabled=not data_edited):
                for performance_id, values in edited_data.items():
                    with get_db() as conn:
                        conn.execute(
                            update(Performance).where(Performance.id==performance_id).values(values)
                        )
                        conn.commit()
                popup_successful_operation()

        @st.dialog("Silmək istədiyinizə əminsinizmi?")
        def popup_delete():
            button_cols = st.columns(6)
            with button_cols[0]:
                if st.button(label="Bəli"):
                    ids_to_delete = list(edited_df.loc[edited_df["check_mark"]==True, "id"])
                    with get_db() as conn:
                        conn.execute(
                            delete(Performance).where(Performance.id.in_(ids_to_delete))
                        )
                        conn.commit()
                    st.rerun()
            with button_cols[1]:
                if st.button(label="Xeyr"):
                    st.rerun()
        with cols[1]:
            if st.button(label="Sil", icon=":material/delete:", disabled=not data_to_delete):
                popup_delete()

        st.divider()
        if st.toggle(label="qiymətləndir"):
            st.divider()
            add_data()
    else:
        add_data()

logout()