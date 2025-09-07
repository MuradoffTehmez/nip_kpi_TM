# pages/2_user.py

import streamlit as st
st.set_page_config(layout="wide")

import pandas as pd
import altair as alt
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

# Sidebar menyusu
st.sidebar.page_link(page="pages/2_user.py", label="Şəxsi Panel", icon=":material/person:")
show_notifications()  # Show notifications in sidebar
download_guide_doc_file()
logout()

st.title(f"Xoş gəldiniz, {current_user.get_full_name()}!")

# Tab-lər
tab1, tab2, tab3 = st.tabs(["📋 Mənim Tapşırıqlarım", "📊 Mənim Nəticələrim", "🎯 Fərdi İnkişaf Planım"])

# Tab 1: Mənim Tapşırıqlarım
with tab1:
    st.header("Mənim Tapşırıqlarım")
    
    # Gözləmədə olan qiymətləndirmələri əldə edirik
    pending_evaluations = KpiService.get_pending_evaluations_for_user(current_user.id)
    
    if not pending_evaluations:
        st.success("Hazırda tamamlanmalı KPI tapşırığınız yoxdur.")
    else:
        st.info(f"Tamamlanmalı {len(pending_evaluations)} tapşırığınız var.")
        for eval in pending_evaluations:
            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                with col1:
                    if eval.evaluated_user_id == current_user.id:
                        st.subheader("Özünüqiymətləndirmə")
                    else:
                        evaluated_user = UserService.get_user_by_id(eval.evaluated_user_id)
                        st.subheader(f"Qiymətləndirilən: {evaluated_user.get_full_name() if evaluated_user else 'Naməlum'}")
                    st.caption(f"Dövr: {eval.period.name} | Son tarix: {eval.period.end_date.strftime('%d.%m.%Y')}")
                with col2:
                    if st.button("Başla", key=f"eval_{eval.id}", use_container_width=True, type="primary"):
                        st.switch_page(f"pages/5_qiymetlendirme_formu.py?evaluation_id={eval.id}")

# Tab 2: Mənim Nəticələrim
with tab2:
    st.header("Mənim Nəticələrim")
    
    # İstifadəçinin tamamladığı qiymətləndirmələri əldə edirik
    completed_evaluations = KpiService.get_completed_evaluations_for_user(current_user.id)
    
    if not completed_evaluations:
        st.info("Hələ heç bir qiymətləndirmə tamamlamısınız.")
    else:
        # Performans trendini əldə edirik
        trend_data = KpiService.get_user_performance_trend(current_user.id)
        
        if trend_data:
            df_trend = pd.DataFrame(trend_data)
            df_trend = df_trend.rename(columns={
                "period_name": "Dövr",
                "score": "Yekun Bal"
            })
            
            # Xətt qrafiki üçün trend
            if len(df_trend) > 1:
                trend_chart = alt.Chart(df_trend).mark_line(point=True).encode(
                    x=alt.X('Dövr:N', title="Dövr", sort=None),
                    y=alt.Y('Yekun Bal:Q', title="Yekun Bal"),
                    tooltip=['Dövr', 'Yekun Bal']
                ).properties(
                    title="Performansınızın Zamanla Dəyişməsi",
                    height=400
                )
                st.altair_chart(trend_chart, use_container_width=True)
            else:
                st.info("Trend qrafikini göstərmək üçün ən azı iki fərqli dövr üzrə nəticə olmalıdır.")
            
            # Dövrlər üzrə nəticələr cədvəli
            st.subheader("Dövrlər Üzrə Nəticələr")
            st.dataframe(
                df_trend,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Dövr": st.column_config.TextColumn(width=200),
                    "Yekun Bal": st.column_config.NumberColumn(format="%.2f")
                }
            )
        else:
            st.info("Performans trend məlumatı mövcud deyil.")

# Tab 3: Fərdi İnkişaf Planım (gələcəkdə əlavə ediləcək)
with tab3:
    st.header("Fərdi İnkişaf Planım")
    st.info("Bu bölmə gələcəkdə Fərdi İnkişaf Planı (FİP) modulu ilə zənginləşdiriləcək.")
    st.image("https://images.unsplash.com/photo-1517245386807-bb43f82c33c4?auto=format&fit=crop&w=800&q=80", caption="Fərdi İnkişaf Planı", use_column_width=True)