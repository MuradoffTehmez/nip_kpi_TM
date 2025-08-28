import streamlit as st
from streamlit_cookies_controller import CookieController
from database import get_db
from models.user import User

controller = CookieController()

user_id_from_cookie = controller.get("user_id")

if user_id_from_cookie:
    with get_db() as session:
        user = session.query(User).where(User.id == user_id_from_cookie, User.is_active == True).scalar()
        if user:
            if user.role == "admin":
                st.switch_page(page="./pages/1_admin.py")
            elif user.role == "user":
                st.switch_page(page="./pages/2_user.py")
            st.stop()

st.set_page_config(layout="centered")
st.sidebar.page_link(page="main.py", label="Giriş", icon=":material/login:")

st.title("Sistemə Giriş")

username = st.text_input(label="İstifadəçi adı:", value=None)
password = st.text_input(label="Şifrə:", type="password", value=None)

remember_me = st.checkbox("Məni xatırla")

if st.button(label="Daxil ol", icon=":material/login:"):
    if username and password:
        with get_db() as session:
            user: User = session.query(User).where(User.username == username, User.is_active == True).scalar()
            
            if user and user.password == password:
                
                if remember_me:
                    max_age = 30 * 24 * 60 * 60
                    controller.set("user_id", user.id, max_age=max_age)
                else:
                    controller.set("user_id", user.id)

                if user.role == "admin":
                    st.switch_page(page="./pages/1_admin.py")
                elif user.role == "user":
                    st.switch_page(page="./pages/2_user.py")
            else:
                st.error("İstifadəçi adı və ya şifrə yanlışdır!")
    else:
        st.warning("Zəhmət olmasa, hər iki sahəni doldurun!")