import streamlit as st, pandas as pd
from streamlit_cookies_controller import CookieController
controller = CookieController()

st.set_page_config(layout="wide")

from sqlalchemy import select
from database import get_db
from utils.utils import download_guide_doc_file, logout

from models.user import User
from models.indicator import Indicator
from models.user_profile import UserProfile
from models.performance import Performance


st.sidebar.page_link(page="./pages/2_user.py", label="Nəticələrim", icon=":material/analytics:")
download_guide_doc_file()

user_id = controller.get("user_id")

with get_db() as session:
    years = list(set(session.scalars(select(Performance.evaluation_year).where(Performance.user_id==user_id)).all()))
    user_performance_data = session.execute(select(Performance.user_id, Performance.indicator_id, Performance.evaluation_month, Performance.evaluation_year, Performance.points, Performance.weighted_points).where(Performance.user_id==user_id)).fetchall()
    

if len(user_performance_data) > 0:
    cols = st.columns(5)
    with cols[0]:
        years_chosen = st.multiselect(label="İl:", options=years, default=None)
        if not years_chosen:
            years_chosen = years
    with cols[1]:
        months = list(set(session.scalars(select(Performance.evaluation_month).where(Performance.user_id==user_id, Performance.evaluation_year.in_(years_chosen))).all()))

        months_chosen = st.multiselect(label="Qiymətləndirmə növü:", options=months, default=None)
        if not months_chosen:
            months_chosen = months


    st.divider()
    user_id_name_map = dict(session.execute(select(UserProfile.user_id, UserProfile.full_name)).fetchall())
    indicator_id_description_map = dict(session.execute(select(Indicator.id, Indicator.description)).fetchall())     

    df = pd.DataFrame(data=user_performance_data)
    df["user_id"] = df["user_id"].map(user_id_name_map)
    df["indicator_id"] = df["indicator_id"].map(indicator_id_description_map)
    df = df[(df["evaluation_year"].isin(years_chosen)) & (df["evaluation_month"].isin(months_chosen))]

    grouped_df = df.groupby(by=["user_id", "evaluation_month", "evaluation_year"], as_index=False).agg({"weighted_points": "sum"})


    st.dataframe(data=grouped_df, hide_index=True,
                column_config={
                    "user_id": st.column_config.TextColumn(label="Əməkdaş", width=200),
                    "evaluation_month": st.column_config.TextColumn(label="Qiymətləndirmə növü", width=80),
                    "evaluation_year": st.column_config.NumberColumn(label="İl", width=30),
                    "weighted_points": st.column_config.NumberColumn(label="Yekun bal", width=30),
                }
            )


    if st.toggle("detallı bax"):
        st.divider()
        st.dataframe(data=df, hide_index=True, 
                    column_config={
                        "user_id": st.column_config.TextColumn(label="Əməkdaş", width=200),
                        "indicator_id": st.column_config.TextColumn(label="Göstərici", width="large"),
                        "evaluation_month": st.column_config.TextColumn(label="Qiymətləndirmə növü", width=80),
                        "evaluation_year": st.column_config.NumberColumn(label="İl", width=30),
                        "points": st.column_config.NumberColumn(label="Bal", width=30),
                        "weighted_points": st.column_config.NumberColumn(label="Yekun bal", width=30),
                    }
                )
else:
    st.markdown("***:red[Məlumat tapılmadı!]***")


logout()
