import streamlit as st
from streamlit_cookies_controller import CookieController

st.set_page_config(layout="wide")

st.title("Cookie Test və Təmizləmə Səhifəsi")
st.warning("Bu səhifə yalnız test məqsədlidir. Problem həll olunduqdan sonra silinəcək.")
st.divider()

controller = CookieController()

st.subheader("Hazırkı Cookie Vəziyyəti")
user_id = controller.get("user_id")
st.write(f"Cookie-də saxlanan 'user_id' dəyəri: **{user_id}**")

st.divider()

st.subheader("Test Əməliyyatları")

if st.button("Cookie-ni Düzgün Üsulla Sil"):
    controller.set("user_id", None, max_age=0)
    st.success("'controller.set(\"user_id\", None, max_age=0)' əmri icra edildi!")
    st.rerun()