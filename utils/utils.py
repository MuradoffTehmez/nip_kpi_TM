# muradofftehmez/nip_kpi_tm/utils/utils.py

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
            controller.set("user_id", None)
            st.switch_page(page="main.py")


@st.dialog("Uğurlu əməliyyat!")
def popup_successful_operation():
    if st.button(label="", icon=":material/thumb_up:"):
        st.rerun()


def add_data():
    with get_db() as session:
        fullnames = list(set(session.scalars(select(UserProfile.full_name).join(User, UserProfile.user_id==User.id).where(User.role!="admin", User.is_active==True)).all()))
        indicator_descriptions = session.scalars(select(Indicator.description)).all()


        cols = st.columns(5)
        with cols[0]:
            fullname_to_evaluate = st.selectbox(label="Əməkdaş:", options=fullnames, index=None)
        with cols[1]:
            year_to_evaluate = st.selectbox(label="İl:", options=[2024, 2025], index=None)
        with cols[2]:
            month_to_evaluate = st.selectbox(label="Qiymətləndirmə növü:", options=evaluation_types, index=None)


        if fullname_to_evaluate and year_to_evaluate and month_to_evaluate:
            user_id_to_evaluate = session.query(UserProfile.user_id).where(UserProfile.full_name==fullname_to_evaluate).scalar()

            performance_data_by_user = session.execute(select(Performance.user_id, Performance.evaluation_year, Performance.evaluation_month)).fetchall()
            performance_data_exists = (user_id_to_evaluate, year_to_evaluate, month_to_evaluate) in performance_data_by_user
            if performance_data_exists:
                st.divider()
                st.markdown("***:red[Seçdiyiniz əməkdaşın qeyd etdiyiniz tarix üzrə qiymətləndirməsi artıq mövcuddur!]***")
            else:
                performance_data = []
                with st.container(border=True):
                    data = {}
                    st.subheader(f"{indicator_descriptions[0]}:")

                    cols = st.columns(4)
                    with cols[3]:
                        indicator_id = session.execute(select(Indicator.id).where(Indicator.description==indicator_descriptions[0])).scalar()
                        task_accomplishment_point = st.number_input(label="", min_value=2, max_value=5, value=None)

                        if task_accomplishment_point:
                            data["user_id"] = user_id_to_evaluate
                            data["indicator_id"] = indicator_id
                            data["points"] = task_accomplishment_point
                            data["weighted_points"] = task_accomplishment_point * 0.5
                            data["evaluation_year"] = year_to_evaluate
                            data["evaluation_month"] = month_to_evaluate
                            performance_data.append(data)


                with st.container(border=True):
                    data = {}
                    st.subheader(f"{indicator_descriptions[1]}:")

                    cols = st.columns(4)
                    with cols[3]:
                        indicator_id = session.execute(select(Indicator.id).where(Indicator.description==indicator_descriptions[1])).scalar()
                        criterion_point = st.number_input(label=f" ", min_value=2, max_value=5, value=None)

                        if criterion_point:
                            data["user_id"] = user_id_to_evaluate
                            data["indicator_id"] = indicator_id
                            data["points"] = criterion_point
                            data["weighted_points"] = criterion_point * 0.4
                            data["evaluation_year"] = year_to_evaluate
                            data["evaluation_month"] = month_to_evaluate
                            performance_data.append(data)


                with st.container(border=True):
                    data = {}
                    st.subheader(f"{indicator_descriptions[2]}:")

                    cols = st.columns(4)
                    with cols[3]:
                        indicator_id = session.execute(select(Indicator.id).where(Indicator.description==indicator_descriptions[2])).scalar()
                        working_discipline_point = st.number_input(label=f"   ", min_value=2, max_value=5, value=None)

                        if working_discipline_point:
                            data["user_id"] = user_id_to_evaluate
                            data["indicator_id"] = indicator_id
                            data["points"] = working_discipline_point
                            data["weighted_points"] = working_discipline_point * 0.1
                            data["evaluation_year"] = year_to_evaluate
                            data["evaluation_month"] = month_to_evaluate
                            performance_data.append(data)
                
                add_data_enabled = task_accomplishment_point and criterion_point and working_discipline_point

                if st.button(label="Əlavə et", icon=":material/add_circle:", disabled=not add_data_enabled):
                    with get_db() as conn:
                        conn.execute(
                            insert(Performance),
                                performance_data,
                        )
                        conn.commit()
                
                    popup_successful_operation()

def to_excel(df: pd.DataFrame):
    """
    Pandas DataFrame-i qəbul edir və onu Excel faylı kimi
    yaddaşda (in-memory) bayt formatına çevirir.
    """
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Performance_Hesabat')
    writer.close()
    processed_data = output.getvalue()
    return processed_data
