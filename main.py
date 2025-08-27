import streamlit as st
from streamlit_cookies_controller import CookieController
controller = CookieController()

st.set_page_config(layout="centered")

from database import get_db

from models.user import User


st.sidebar.page_link(page="main.py", label="Giriş", icon=":material/login:")


username = st.text_input(label="İstifadəçi adı:", value=None)
password = st.text_input(label="Şifrə:", type="password", value=None)


if st.button(label="Daxil ol", icon=":material/login:"):
    with get_db() as session:
        user: User = session.query(User).where(User.username==username, User.password==password, User.is_active==True).scalar()
        
        if user:
            controller.set("user_id", user.id)
            if user.role == "admin":
                st.switch_page(page="./pages/1_admin.py")
            elif user.role == "user":
                st.switch_page(page="./pages/2_user.py")
        else:
            username_true = session.query(User.username).where(User.username==username, User.is_active==True).scalar()
            if username_true:
                st.markdown("***:red[Şifrə yanlışdır!]***")
            else:
                st.markdown("***:red[İstifadəçi adı yanlışdır!]***")