import streamlit as st
st.set_page_config(layout="wide")
import pandas as pd
import plotly.express as px
from streamlit_cookies_controller import CookieController
from sqlalchemy import select
from database import get_db
from utils.utils import download_guide_doc_file, logout, to_excel, to_excel_formatted_report, get_styled_table_html
from data.months_in_azeri import evaluation_types
from models.user import User
from models.indicator import Indicator
from models.user_profile import UserProfile
from models.performance import Performance

st.sidebar.page_link(page="pages/2_user.py", label="Nəticələrim", icon=":material/analytics:")
download_guide_doc_file()
logout()

controller = CookieController()
user_id = controller.get("user_id")

if not user_id:
    st.error("Zəhmət olmasa, nəticələrə baxmaq üçün sistemə daxil olun.")
    st.page_link("main.py", label="Giriş Səhifəsinə Qayıt", icon="🏠")
    st.stop()

@st.cache_data
def load_user_data(user_id):
    with get_db() as session:
        user_performance_data = session.execute(select(
            Performance.indicator_id, Performance.evaluation_month,
            Performance.evaluation_year, Performance.points, Performance.weighted_points
        ).where(Performance.user_id == user_id)).fetchall()

        indicators_from_db = session.query(Indicator.id, Indicator.description, Indicator.weight).all()
        indicator_id_map = {id: (desc, w) for id, desc, w in indicators_from_db}
        current_user_name = session.query(UserProfile.full_name).where(UserProfile.user_id == user_id).scalar()

        if not user_performance_data:
            return None, None, None

        df = pd.DataFrame(user_performance_data, columns=["indicator_id", "evaluation_month", "evaluation_year", "points", "weighted_points"])
        indicator_description_map = {id: desc for id, desc, w in indicators_from_db}
        df["Göstərici"] = df["indicator_id"].map(indicator_description_map)
        
        df = df.rename(columns={
            "evaluation_month": "Qiymətləndirmə növü", "evaluation_year": "İl",
            "points": "Bal", "weighted_points": "Yekun Bal"
        })
        
        return df.copy(), indicator_id_map, current_user_name

df_performance, indicator_id_map, current_user_name = load_user_data(user_id)

st.title(f"Xoş gəldiniz, {current_user_name}!")
st.subheader("Şəxsi Fəaliyyət Nəticələriniz")
st.divider()

if df_performance is None:
    st.warning("Sizin üçün heç bir qiymətləndirmə məlumatı tapılmadı!")
    st.stop()

tab1, tab2, tab3 = st.tabs(["📊 Ümumi Nəticələr", "📈 Performans Qrafikləri", "📥 Hesabat Yüklə"])

with tab1:
    st.header("Yekun Nəticələr (Dövrlər Üzrə)")
    
    years = sorted(df_performance['İl'].unique(), reverse=True)
    months = sorted(df_performance['Qiymətləndirmə növü'].unique())
    
    col1, col2 = st.columns(2)
    with col1:
        years_chosen = st.multiselect(label="İl:", options=years, default=years)
    with col2:
        months_chosen = st.multiselect(label="Qiymətləndirmə növü:", options=months, default=months)
    
    filtered_df = df_performance[(df_performance["İl"].isin(years_chosen)) & (df_performance["Qiymətləndirmə növü"].isin(months_chosen))]

    if not filtered_df.empty:
        grouped_df = filtered_df.groupby(by=["Qiymətləndirmə növü", "İl"], as_index=False).agg({"Yekun Bal": "sum"})
        
        grouped_formatters = {"Yekun Bal": "{:.2f}"}
        grouped_alignments = {'left': ['Qiymətləndirmə növü'], 'center': ['İl', 'Yekun Bal']}
        grouped_html = get_styled_table_html(grouped_df, formatters=grouped_formatters, alignments=grouped_alignments)
        st.markdown(grouped_html, unsafe_allow_html=True)
        
        st.divider()
        if st.toggle("Bütün nəticələrimə detallı bax"):
            detail_formatters = {"Yekun Bal": "{:.2f}"}
            detail_alignments = {'left': ['Göstərici', 'Qiymətləndirmə növü'], 'center': ['İl', 'Bal', 'Yekun Bal']}
            detail_html = get_styled_table_html(filtered_df[['Göstərici', "Qiymətləndirmə növü", "İl", "Bal", "Yekun Bal"]], formatters=detail_formatters, alignments=detail_alignments)
            st.markdown(detail_html, unsafe_allow_html=True)
    else:
        st.warning("Filtrə uyğun nəticə tapılmadı.")

with tab2:
    st.header("Performansın Vizual Analizi")
    st.subheader("Performansın Zamanla Dəyişimi (Xətt Qrafiki)")
    
    line_chart_df = df_performance.groupby(by=["Qiymətləndirmə növü", "İl"], as_index=False).agg({"Yekun Bal": "sum"})
    if not line_chart_df.empty and len(line_chart_df) > 1:
        line_chart_df['Qiymətləndirmə növü'] = pd.Categorical(line_chart_df['Qiymətləndirmə növü'], categories=evaluation_types, ordered=True)
        line_chart_df = line_chart_df.sort_values(by=['İl', 'Qiymətləndirmə növü'])
        line_chart_df['Dövr'] = line_chart_df['İl'].astype(str) + ' - ' + line_chart_df['Qiymətləndirmə növü'].astype(str)
        line_chart_df = line_chart_df.set_index('Dövr')
        st.line_chart(line_chart_df[['Yekun Bal']])
    else:
        st.info("Xətt qrafikini göstərmək üçün ən azı iki fərqli dövr üzrə nəticə olmalıdır.")

    st.divider()
    st.subheader("Performansın Meyarlar Üzrə Analizi (Radar Qrafiki)")
    
    radar_col1, radar_col2 = st.columns(2)
    with radar_col1:
        radar_year = st.selectbox("Radar qrafiki üçün il seçin:", options=years, key="radar_year")
    with radar_col2:
        radar_months = sorted(df_performance[df_performance['İl'] == radar_year]['Qiymətləndirmə növü'].unique())
        radar_month = st.selectbox("Radar qrafiki üçün qiymətləndirmə növü seçin:", options=radar_months, key="radar_month")
    
    if radar_year and radar_month:
        radar_df = df_performance[(df_performance['İl'] == radar_year) & (df_performance['Qiymətləndirmə növü'] == radar_month)]
        
        if not radar_df.empty:
            fig = px.line_polar(radar_df, r='Bal', theta='Göstərici', line_close=True,
                                title=f"{radar_year} - {radar_month} üzrə Nəticələrin Təhlili",
                                range_r=[0, 5], markers=True)
            fig.update_traces(fill='toself')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Seçilmiş dövr üçün radar qrafiki qurmaq mümkün deyil.")

with tab3:
    st.header("Formatlı Fərdi Hesabat Yüklə")
    
    report_cols_user = st.columns(2)
    with report_cols_user[0]:
        user_report_year = st.selectbox("Hesabat üçün il seçin:", options=years, index=None, key="user_report_year")
    
    if user_report_year:
        user_available_months = sorted(df_performance[df_performance['İl'] == user_report_year]['Qiymətləndirmə növü'].unique())
        with report_cols_user[1]:
            user_report_month = st.selectbox("Hesabat üçün qiymətləndirmə növü seçin:", options=user_available_months, index=None, key="user_report_month")

        if user_report_month:
            user_perf_records_df = df_performance[
                (df_performance['İl'] == user_report_year) & 
                (df_performance['Qiymətləndirmə növü'] == user_report_month)
            ]

            if not user_perf_records_df.empty:
                report_data = []
                for i, row in user_perf_records_df.iterrows():
                    indicator_id = row['indicator_id']
                    _, weight = indicator_id_map.get(indicator_id, ("?", 0))
                    report_data.append({
                        "S/N": len(report_data) + 1,
                        "Fəaliyyət üzrə": row['Göstərici'],
                        "Ümumi qiymət": row['Bal'],
                        "Yekun qiymətin faiz bölgüsü": int(weight * 100),
                        "Yekun nəticə faizlə": row['Yekun Bal']
                    })
                
                total_score = user_perf_records_df['Yekun Bal'].sum()
                report_data.append({
                    "S/N": "", "Fəaliyyət üzrə": "Qiymətləndirilmə üzrə yekun nəticə",
                    "Ümumi qiymət": "", "Yekun qiymətin faiz bölgüsü": "", "Yekun nəticə faizlə": round(total_score, 2)
                })
                user_report_df = pd.DataFrame(report_data)

                user_report_df_styled = user_report_df.rename(columns={
                    "Ümumi qiymət": "Ümumi qiymət (2,3,4,5)",
                    "Yekun qiymətin faiz bölgüsü": "Yekun qiymətin faiz bölgüsü (50,40,10)"
                })
                
                user_eval_period = f"{user_report_month} {user_report_year}"
                excel_data_user_formatted = to_excel_formatted_report(
                    df=user_report_df_styled.fillna(''),
                    employee_name=current_user_name,
                    evaluation_period=user_eval_period
                )
                st.download_button(
                    label="📥 Formatlı Hesabatı Yüklə",
                    data=excel_data_user_formatted,
                    file_name=f"formalashesabat_{current_user_name}.xlsx",
                    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )