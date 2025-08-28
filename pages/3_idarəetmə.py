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

# --- Yeni İstifadəçi Yaratmaq Bölməsi ---
with st.expander("➕ Yeni İstifadəçi Yarat"):
    with st.form("new_user_form", clear_on_submit=True):
        st.subheader("Yeni İstifadəçinin Məlumatları")
        
        col1, col2 = st.columns(2)
        with col1:
            # Giriş məlumatları
            new_username = st.text_input("İstifadəçi Adı (login üçün)")
            new_password = st.text_input("Şifrə", type="password")
            new_role = st.selectbox("Rolu", ["user", "admin"])
        
        with col2:
            # Profil məlumatları
            new_full_name = st.text_input("Tam Adı (Ad, Soyad)")
            new_position = st.text_input("Vəzifəsi")

        submitted = st.form_submit_button("Yeni İstifadəçini Yarat")

        if submitted:
            # Bütün xanaların dolu olub-olmadığını yoxlayırıq
            if not all([new_username, new_password, new_role, new_full_name, new_position]):
                st.warning("Zəhmət olmasa, bütün xanaları doldurun.")
            else:
                with get_db() as session:
                    # Eyni istifadəçi adının mövcud olub-olmadığını yoxlayırıq
                    existing_user = session.query(User).filter(User.username == new_username).first()
                    if existing_user:
                        st.error(f"'{new_username}' adlı istifadəçi artıq mövcuddur. Fərqli ad seçin.")
                    else:
                        # Əvvəlcə "user" cədvəlinə əlavə edirik
                        user_to_add = User(
                            username=new_username,
                            password=new_password, # Qeyd: Şifrə hələ də açıq mətn şəklindədir
                            role=new_role
                        )
                        session.add(user_to_add)
                        session.commit()
                        session.refresh(user_to_add) # Yeni yaranan istifadəçinin ID-sini almaq üçün

                        # Sonra "user_profile" cədvəlinə əlavə edirik
                        profile_to_add = UserProfile(
                            user_id=user_to_add.id,
                            full_name=new_full_name,
                            position=new_position
                        )
                        session.add(profile_to_add)
                        session.commit()

                        st.success(f"İstifadəçi '{new_full_name}' uğurla yaradıldı!")
                        # st.rerun() # Səhifənin avtomatik yenilənməsi üçün (istəyə bağlı)

st.divider()

# --- Mövcud İstifadəçilər Bölməsi ---
st.header("Mövcud İstifadəçilər")

try:
    with get_db() as session:
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
            df_users = pd.DataFrame(users_data, columns=[
                "ID", "İstifadəçi Adı", "Tam Adı", "Vəzifəsi", "Rolu", "Aktivdir"
            ])
            st.dataframe(df_users, use_container_width=True)
        else:
            st.warning("Verilənlər bazasında heç bir istifadəçi tapılmadı.")

except Exception as e:
    st.error(f"Verilənlər bazasından məlumatları çəkərkən xəta baş verdi: {e}")