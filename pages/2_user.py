import streamlit as st
import pandas as pd
from streamlit_cookies_controller import CookieController
controller = CookieController()

st.set_page_config(layout="wide")

from sqlalchemy import select
from database import get_db
from utils.utils import download_guide_doc_file, logout, to_excel, to_excel_formatted_report
from data.months_in_azeri import evaluation_types

from models.user import User
from models.indicator import Indicator
from models.user_profile import UserProfile
from models.performance import Performance


st.sidebar.page_link(page="./pages/2_user.py", label="Nəticələrim", icon=":material/analytics:")
download_guide_doc_file()

user_id = controller.get("user_id")

if not user_id:
    st.markdown("Zəhmət olmasa, nəticələrə baxmaq üçün giriş edin.")
    st.stop()

with get_db() as session:
    years = sorted(list(set(session.scalars(select(Performance.evaluation_year).where(Performance.user_id==user_id)).all())), reverse=True)
    user_performance_data = session.execute(select(
        Performance.user_id, Performance.indicator_id, Performance.evaluation_month, 
        Performance.evaluation_year, Performance.points, Performance.weighted_points
    ).where(Performance.user_id==user_id)).fetchall()
    
    indicators_from_db = session.query(Indicator.id, Indicator.description, Indicator.weight).all()
    indicator_id_map = {id: (desc, w) for id, desc, w in indicators_from_db}
    
    current_user_name = session.query(UserProfile.full_name).where(UserProfile.user_id == user_id).scalar()

if len(user_performance_data) > 0:
    st.subheader("Ümumi Nəticələr")
    cols = st.columns(5)
    with cols[0]:
        years_chosen = st.multiselect(label="İl:", options=years, default=None)
        if not years_chosen: years_chosen = years
    with cols[1]:
        months = sorted(list(set(session.scalars(select(Performance.evaluation_month).where(Performance.user_id==user_id, Performance.evaluation_year.in_(years_chosen))).all())))
        months_chosen = st.multiselect(label="Qiymətləndirmə növü:", options=months, default=None)
        if not months_chosen: months_chosen = months

    user_id_name_map = dict(session.execute(select(UserProfile.user_id, UserProfile.full_name)).fetchall())
    indicator_description_map = {id: desc for id, desc, w in indicators_from_db}

    df = pd.DataFrame(data=user_performance_data)
    df["user_id"] = df["user_id"].map(user_id_name_map)
    df["indicator_id"] = df["indicator_id"].map(indicator_description_map)
    df = df[(df["evaluation_year"].isin(years_chosen)) & (df["evaluation_month"].isin(months_chosen))]

    grouped_df = df.groupby(by=["user_id", "evaluation_month", "evaluation_year"], as_index=False).agg({"weighted_points": "sum"})
    st.dataframe(data=grouped_df, hide_index=True, column_config={"user_id": st.column_config.TextColumn(label="Əməkdaş", width=200), "evaluation_month": st.column_config.TextColumn(label="Qiymətləndirmə növü", width=80), "evaluation_year": st.column_config.NumberColumn(label="İl", width=30), "weighted_points": st.column_config.NumberColumn(label="Yekun bal", width=30)})

    st.divider()
    st.subheader("Performansın Zamanla Dəyişimi")
    if not grouped_df.empty and len(grouped_df) > 1:
        df_for_chart = grouped_df.copy()
        df_for_chart['evaluation_month'] = pd.Categorical(df_for_chart['evaluation_month'], categories=evaluation_types, ordered=True)
        df_for_chart = df_for_chart.sort_values(by=['evaluation_year', 'evaluation_month'])
        df_for_chart['Dövr'] = df_for_chart['evaluation_year'].astype(str) + ' - ' + df_for_chart['evaluation_month'].astype(str)
        df_for_chart = df_for_chart.set_index('Dövr')
        chart_data = df_for_chart[['weighted_points']].rename(columns={'weighted_points': 'Yekun Bal'})
        st.line_chart(chart_data)
    else:
        st.info("Performans qrafikini göstərmək üçün ən azı iki fərqli dövr üzrə məlumat olmalıdır.")
    
    st.divider()
    st.subheader("Formatlı Fərdi Hesabat Yüklə")
    
    report_cols_user = st.columns(2)
    with report_cols_user[0]:
        user_report_year = st.selectbox("Hesabat üçün il seçin:", options=years, index=None, key="user_report_year")
    
    if user_report_year:
        user_available_months = sorted(list(set(session.scalars(
            select(Performance.evaluation_month).where(Performance.user_id == user_id, Performance.evaluation_year == user_report_year)
        ).all())))
        with report_cols_user[1]:
            user_report_month = st.selectbox("Hesabat üçün qiymətləndirmə növü seçin:", options=user_available_months, index=None, key="user_report_month")

        if user_report_month:
            user_perf_records = session.query(
                Performance.indicator_id, Performance.points, Performance.weighted_points
            ).where(
                Performance.user_id == user_id,
                Performance.evaluation_year == user_report_year,
                Performance.evaluation_month == user_report_month
            ).all()

            if user_perf_records:
                user_report_data = []
                total_score = 0
                for i, record in enumerate(user_perf_records):
                    indicator_id, points, weighted_points = record
                    desc, weight = indicator_id_map.get(indicator_id, ("?", 0))
                    user_report_data.append({
                        "S/N": i + 1, "Fəaliyyət üzrə": desc, "Ümumi qiymət": points,
                        "Yekun qiymətin faiz bölgüsü": int(weight * 100), "Yekun nəticə faizlə": weighted_points
                    })
                    total_score += weighted_points
                
                user_report_data.append({
                    "S/N": "", "Fəaliyyət üzrə": "Qiymətləndirilmə üzrə yekun nəticə",
                    "Ümumi qiymət": "", "Yekun qiymətin faiz bölgüsü": "", "Yekun nəticə faizlə": round(total_score, 2)
                })
                user_report_df = pd.DataFrame(user_report_data)
                
                user_eval_period = f"{user_report_month} {user_report_year}"
                excel_data_user_formatted = to_excel_formatted_report(
                    df=user_report_df.fillna(''),
                    employee_name=current_user_name,
                    evaluation_period=user_eval_period
                )
                st.download_button(
                    label="📥 Formatlı Hesabatı Yüklə",
                    data=excel_data_user_formatted,
                    file_name=f"formalashesabat_{current_user_name}.xlsx",
                    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )

    st.divider()
    if st.toggle("Bütün nəticələrimə detallı bax"):
        st.dataframe(data=df, hide_index=True, column_config={"user_id": st.column_config.TextColumn(label="Əməkdaş", width=200), "indicator_id": st.column_config.TextColumn(label="Göstərici", width="large"), "evaluation_month": st.column_config.TextColumn(label="Qiymətləndirmə növü", width=80), "evaluation_year": st.column_config.NumberColumn(label="İl", width=30), "points": st.column_config.NumberColumn(label="Bal", width=30), "weighted_points": st.column_config.NumberColumn(label="Yekun bal", width=30)})
        if not df.empty:
            excel_data_user_raw = to_excel(df)
            st.download_button(label="📥 Detallı siyahını yüklə", data=excel_data_user_raw, file_name=f'neticelerim_detalli_{user_id}.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

else:
    st.markdown("***:red[Sizin üçün heç bir qiymətləndirmə məlumatı tapılmadı!]***")

logout()