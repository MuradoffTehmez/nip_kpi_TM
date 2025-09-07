# pages/3_idarəetmə.py

import streamlit as st
st.set_page_config(layout="wide")

import pandas as pd
from sqlalchemy import select, update, func
from database import get_db
from models.user import User
from models.user_profile import UserProfile
from utils.utils import download_guide_doc_file, logout, check_login, show_notifications
from services.user_service import UserService

current_user = check_login()
if current_user.role != "admin":
    st.error("Bu səhifəyə giriş üçün icazəniz yoxdur.")
    st.stop()

st.sidebar.page_link(page="pages/1_admin.py", label="Qiymətləndirmə", icon=":material/grading:")
show_notifications()  # Show notifications in sidebar
st.sidebar.page_link(page="pages/3_idarəetmə.py", label="İdarəetmə", icon=":material/settings:")
st.sidebar.page_link(page="pages/6_kpi_idarəetmə.py", label="KPI İdarəetmə", icon=":material/manage_accounts:")
st.sidebar.page_link(page="pages/8_kpi_analitika.py", label="KPI Analitika", icon=":material/monitoring:")
download_guide_doc_file()
logout()

st.title("İdarəetmə Paneli")
st.divider()

tab1, tab2 = st.tabs(["👤 İstifadəçi İdarəetməsi", "⚙️ Sual İdarəetməsi"])
with tab1:
    with st.expander("➕ Yeni İstifadəçi Yarat"):
        with st.form("new_user_form", clear_on_submit=True):
            st.subheader("Yeni İstifadəçinin Məlumatları")
            col1, col2 = st.columns(2)
            with col1:
                new_username = st.text_input("İstifadəçi Adı (login üçün)")
                new_password = st.text_input("Şifrə", type="password")
                new_role = st.selectbox("Rolu", ["user", "admin"])
            with col2:
                new_full_name = st.text_input("Tam Adı (Ad, Soyad)")
                new_position = st.text_input("Vəzifəsi")
                new_department = st.text_input("Şöbə")
                # Get list of potential managers (other active users)
                managers = UserService.get_all_active_users()
                manager_options = {user.id: f"{user.get_full_name()} ({user.username})" for user in managers}
                manager_options[None] = "Rəhbər yoxdur"
                new_manager_id = st.selectbox("Rəhbəri", options=manager_options, format_func=lambda x: manager_options[x])
            submitted = st.form_submit_button("Yeni İstifadəçini Yarat")
            if submitted:
                if not all([new_username, new_password, new_role, new_full_name, new_position]):
                    st.warning("Zəhmət olmasa, bütün xanaları doldurun.")
                else:
                    with get_db() as session:
                        existing_user = session.query(User).filter(User.username == new_username).first()
                        if existing_user:
                            st.error(f"'{new_username}' adlı istifadəçi artıq mövcuddur. Fərqli ad seçin.")
                        else:
                            user_to_add = User(username=new_username, role=new_role, manager_id=new_manager_id if new_manager_id else None)
                            user_to_add.set_password(new_password)
                            session.add(user_to_add)
                            session.commit()
                            session.refresh(user_to_add)
                            profile_to_add = UserProfile(user_id=user_to_add.id, full_name=new_full_name, position=new_position, department=new_department if new_department else None)
                            session.add(profile_to_add)
                            session.commit()
                            st.success(f"İstifadəçi '{new_full_name}' uğurla yaradıldı!")
                            st.rerun()

    st.subheader("Mövcud İstifadəçilər")
    try:
        with get_db() as session:
            users_query = session.query(
                User.id, User.username, UserProfile.full_name,
                UserProfile.position, User.role, User.is_active, User.manager_id, UserProfile.department
            ).join(UserProfile, User.id == UserProfile.user_id).order_by(User.id)
            users_data = users_query.all()
            if users_data:
                # Get all users for manager selection
                all_users = session.query(UserProfile).all()
                user_name_map = {profile.user_id: profile.full_name for profile in all_users}
                user_name_map[None] = "Rəhbər yoxdur"
                
                # Format data for display
                formatted_users_data = []
                for user_row in users_data:
                    user_id, username, full_name, position, role, is_active, manager_id, department = user_row
                    manager_name = user_name_map.get(manager_id, "Naməlum")
                    formatted_users_data.append((user_id, username, full_name, position, role, is_active, manager_name, department if department else ""))
                
                df_users = pd.DataFrame(formatted_users_data, columns=[
                    "ID", "İstifadəçi Adı", "Tam Adı", "Vəzifəsi", "Rolu", "Aktivdir", "Rəhbəri", "Şöbə"
                ])
                if 'original_users_df' not in st.session_state:
                    st.session_state['original_users_df'] = df_users.copy()
                edited_df = st.data_editor(
                    df_users, use_container_width=True, hide_index=True, key="user_editor",
                    column_config={
                        "ID": st.column_config.NumberColumn("ID", disabled=True),
                        "Rolu": st.column_config.SelectboxColumn("Rolu", options=["user", "admin", "manager"]),
                        "Aktivdir": st.column_config.CheckboxColumn("Aktivdir")
                    }
                )
                if st.button("İstifadəçiləri Yadda Saxla"):
                    # Bu hissəni daha düzgün şəkildə yazmaq lazımdır
                    st.warning("İstifadəçiləri redaktə etmə funksionallığı hazırda tam işləmir.")
    except Exception as e:
        st.error(f"İstifadəçilərlə işləyərkən xəta baş verdi: {e}")

with tab2:
    try:
        from models.kpi import Question
        with get_db() as session:
            total_weight_query = session.query(func.sum(Question.weight)).filter(Question.is_active == True)
            current_total_weight = total_weight_query.scalar() or 0.0

            st.warning(f"Diqqət: Aktiv sualların çəkilərinin cəmi 1.0 (100%) olmalıdır. Hazırkı cəm: {current_total_weight:.2f}")
            if abs(current_total_weight - 1.0) > 0.001:
                st.error("Çəkilərin cəmi 1.0 deyil! Zəhmət olmasa, sualları redaktə edərək cəmi 1.0-a bərabərləşdirin.")

        with st.expander("➕ Yeni Sual Yarat"):
            with st.form("new_question_form", clear_on_submit=True):
                text = st.text_area("Sualın mətni")
                category = st.text_input("Kateqoriya", value="Ümumi")
                weight = st.number_input("Çəkisi (məsələn, 0.5)", min_value=0.0, max_value=1.0, step=0.01, format="%.2f")
                
                submitted_question = st.form_submit_button("Yeni Sual Yarat")
                if submitted_question:
                    if text and weight > 0:
                        with get_db() as session:
                            new_question = Question(text=text, category=category, weight=weight, is_active=True)
                            session.add(new_question)
                            session.commit()
                            st.success(f"Yeni sual uğurla yaradıldı!")
                            st.rerun()
                    else:
                        st.warning("Zəhmət olmasa, bütün xanaları doldurun.")

        st.subheader("Mövcud Suallar")
        with get_db() as session:
            questions = session.query(Question).order_by(Question.id).all()
            if questions:
                df_questions = pd.DataFrame(
                    [{'ID': q.id, 'Sual': q.text, 'Kateqoriya': q.category, 'Çəkisi': q.weight, 'Aktivdir': q.is_active} for q in questions]
                )
                if 'original_questions_df' not in st.session_state:
                    st.session_state['original_questions_df'] = df_questions.copy()
                
                edited_questions_df = st.data_editor(
                    df_questions, use_container_width=True, hide_index=True, key="question_editor",
                    column_config={
                        "ID": st.column_config.NumberColumn(disabled=True),
                        "Sual": st.column_config.TextColumn(width="large"),
                        "Çəkisi": st.column_config.NumberColumn(format="%.2f", step=0.01),
                        "Aktivdir": st.column_config.CheckboxColumn()
                    }
                )

                if st.button("Sualları Yadda Saxla"):
                    new_total_weight = edited_questions_df[edited_questions_df['Aktivdir'] == True]['Çəkisi'].sum()
                    if abs(new_total_weight - 1.0) > 0.001:
                        st.error(f"Yadda saxlamaq mümkün deyil! Aktiv sualların yeni cəmi {new_total_weight:.2f} olur. Cəm 1.0 olmalıdır.")
                    else:
                        original_questions_df = st.session_state.original_questions_df
                        # Dəyişiklikləri yoxlamaq və yeniləmək üçün daha mürəkkəb məntiq lazımdır
                        st.warning("Sualları redaktə etmə funksionallığı hazırda tam işləmir.")
                        
    except Exception as e:
        st.error(f"Suallarla işləyərkən xəta baş verdi: {e}")