import streamlit as st
from streamlit_cookies_controller import CookieController
from database import get_db
from models.user import User

# Səhifənin ilkin konfiqurasiyası
st.set_page_config(layout="centered", page_title="KPI Sistemi - Giriş")

controller = CookieController()

# Çıxış siqnalını yoxlamaq üçün məntiq
if st.query_params.get("logout") == "true":
    controller.set("user_id", None, max_age=0)
    st.query_params.clear()
    st.rerun()

# Cookie vasitəsilə avtomatik giriş məntiqi
user_id_from_cookie = controller.get("user_id")
if user_id_from_cookie:
    with get_db() as session:
        user = session.query(User).where(User.id == user_id_from_cookie, User.is_active == True).scalar()
        if user:
            if user.role == "admin":
                st.switch_page(page="pages/1_admin.py")
            elif user.role == "user":
                st.switch_page(page="pages/2_user.py")
            st.stop()


st.image("https://www.nif.gov.az/themes/custom/nif/logo.svg", width=300)
st.title("NİF - Fəaliyyətin Qiymətləndirilməsi Portalı")
st.write("Davam etmək üçün zəhmət olmasa, sistemə daxil olun.")

with st.container(border=True):
    username = st.text_input(
        label="İstifadəçi adı",
        placeholder="İstifadəçi adınızı daxil edin"
    )
    password = st.text_input(
        label="Şifrə",
        type="password",
        placeholder="Şifrənizi daxil edin"
    )
    remember_me = st.checkbox("Məni xatırla")
    st.markdown("---")

    if st.button("Daxil ol", type="primary", use_container_width=True):
        if username and password:
            with get_db() as session:
                user: User = session.query(User).where(User.username == username, User.is_active == True).scalar()
                
                if user and user.verify_password(password):
                    st.session_state['user_id'] = user.id
                    if remember_me:
                        max_age = 30 * 24 * 60 * 60
                        controller.set("user_id", user.id, max_age=max_age)
                    else:
                        controller.set("user_id", user.id)

                    if user.role == "admin":
                        st.switch_page(page="pages/1_admin.py")
                    elif user.role == "user":
                        st.switch_page(page="pages/2_user.py")
                else:
                    st.error("İstifadəçi adı və ya şifrə yanlışdır!")
        else:
            st.warning("Zəhmət olmasa, bütün xanaları doldurun!")