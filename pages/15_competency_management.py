# pages/15_competency_management.py

import streamlit as st
st.set_page_config(layout="wide")

from database import get_db
from services.competency_service import CompetencyService
from utils.utils import check_login, logout, show_notifications
import pandas as pd

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
st.sidebar.page_link(page="pages/15_competency_management.py", label="Səriştələr", icon=":material/school:")
logout()

st.title("Səriştələrin İdarə Edilməsi")

# Verilənlər bazası bağlantısı
db = next(get_db())
competency_service = CompetencyService(db)

# Səhifələmə
tab1, tab2, tab3 = st.tabs(["Bütün Səriştələr", "Yeni Səriştə Yarat", "Səriştələri Redaktə Et"])

with tab1:
    st.subheader("Mövcud Səriştələr")
    
    # Bütün səriştələri əldə edin
    competencies = competency_service.get_all_competencies()
    
    if not competencies:
        st.info("Hələ heç bir səriştə yaradılmayıb.")
    else:
        # Səriştələri cədvəl şəklində göstərin
        competency_data = []
        for competency in competencies:
            competency_data.append({
                "ID": competency.id,
                "Ad": competency.name,
                "Kateqoriya": competency.category or "Təyin edilməyib",
                "Təsvir": competency.description or "Təsvir yoxdur"
            })
        
        df = pd.DataFrame(competency_data)
        st.dataframe(df, use_container_width=True, hide_index=True)

with tab2:
    st.subheader("Yeni Səriştə Yarat")
    
    with st.form("new_competency_form"):
        name = st.text_input("Səriştə Adı")
        category = st.text_input("Kateqoriya")
        description = st.text_area("Təsvir")
        
        submitted = st.form_submit_button("Yarat")
        
        if submitted:
            if name:
                try:
                    competency = competency_service.create_competency(
                        name=name,
                        description=description,
                        category=category
                    )
                    st.success(f"Səriştə uğurla yaradıldı: {competency.name}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Səriştə yaradılarkən xəta baş verdi: {str(e)}")
            else:
                st.warning("Zəhmət olmasa səriştə adını daxil edin.")

with tab3:
    st.subheader("Səriştələri Redaktə Et")
    
    # Bütün səriştələri seçin
    competencies = competency_service.get_all_competencies()
    
    if not competencies:
        st.info("Hələ heç bir səriştə yaradılmayıb.")
    else:
        competency_options = {f"{c.name} ({c.category or 'Kateqoriyasız'})": c.id for c in competencies}
        selected_competency_name = st.selectbox("Redaktə etmək üçün səriştə seçin:", options=list(competency_options.keys()))
        
        if selected_competency_name:
            selected_competency_id = competency_options[selected_competency_name]
            competency = competency_service.get_competency_by_id(selected_competency_id)
            
            if competency:
                with st.form("edit_competency_form"):
                    name = st.text_input("Səriştə Adı", value=competency.name)
                    category = st.text_input("Kateqoriya", value=competency.category or "")
                    description = st.text_area("Təsvir", value=competency.description or "")
                    
                    submitted = st.form_submit_button("Yenilə")
                    
                    if submitted:
                        try:
                            updated_competency = competency_service.update_competency(
                                competency_id=competency.id,
                                name=name,
                                description=description,
                                category=category
                            )
                            st.success(f"Səriştə uğurla yeniləndi: {updated_competency.name}")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Səriştə yenilənərkən xəta baş verdi: {str(e)}")
                
                # Səriştəni silmək
                if st.button("Səriştəni Sil", type="primary"):
                    try:
                        if competency_service.delete_competency(competency.id):
                            st.success("Səriştə uğurla silindi.")
                            st.rerun()
                        else:
                            st.error("Səriştə silinərkən xəta baş verdi.")
                    except Exception as e:
                        st.error(f"Səriştə silinərkən xəta baş verdi: {str(e)}")