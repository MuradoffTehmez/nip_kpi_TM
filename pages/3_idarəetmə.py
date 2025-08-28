import streamlit as st
import pandas as pd
from sqlalchemy import select
from database import get_db
from models.user import User
from models.user_profile import UserProfile
from utils.utils import download_guide_doc_file, logout

# Səhifənin enli formatda olması üçün konfiqurasiya
st.set_page_config(layout="wide")

# --- Kənar Panel (Sidebar) ---
st.sidebar.page_link(page="pages/1_admin.py", label="Qiymətləndirmə", icon=":material/grading:")
st.sidebar.page_link(page="pages/3_idarəetmə.py", label="İdarəetmə", icon=":material/settings:")
download_guide_doc_file()
logout()
# --- Kənar Panelin Sonu ---

st.title("İdarəetmə Paneli")
st.divider()

st.header("İstifadəçi İdarəetməsi")

try:
    with get_db() as session:
        # User və UserProfile cədvəllərini birləşdirərək bütün məlumatları alırıq
        users_query = session.query(
            User.id,
            User.username,
            UserProfile.full_name,
            UserProfile.position,
            User.role,
            User.is_active
        ).join(UserProfile, User.id == UserProfile.user_id).order_by(User.id)

        users_data = users_query.all()

        if users_data:
            # Məlumatları anlaşılan adlarla DataFrame-ə çeviririk
            df_users = pd.DataFrame(users_data, columns=[
                "ID", "İstifadəçi Adı", "Tam Adı", "Vəzifəsi", "Rolu", "Aktivdir"
            ])
            
            st.info("Aşağıdakı cədvəldə mövcud istifadəçilər göstərilib. Növbəti addımda redaktə və yeni istifadəçi yaratmaq funksiyalarını əlavə edəcəyik.")
            # Cədvəli ekranda göstəririk
            st.dataframe(df_users, use_container_width=True)
        else:
            st.warning("Verilənlər bazasında heç bir istifadəçi tapılmadı.")

except Exception as e:
    st.error(f"Verilənlər bazasından məlumatları çəkərkən xəta baş verdi: {e}")