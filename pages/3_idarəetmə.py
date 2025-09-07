import streamlit as st
st.set_page_config(layout="wide")

import pandas as pd
from sqlalchemy import select, update, func
from database import get_db
from models.user import User
from models.user_profile import UserProfile
from models.indicator import Indicator
from utils.utils import download_guide_doc_file, logout, check_login, show_notifications

current_user = check_login()
if current_user.role != "admin":
    st.error("Bu səhifəyə giriş üçün icazəniz yoxdur.")
    st.stop()

st.sidebar.page_link(page="pages/1_admin.py", label="Qiymətləndirmə", icon=":material/grading:")
show_notifications()  # Show notifications in sidebar
st.sidebar.page_link(page="pages/3_idarəetmə.py", label="İdarəetmə", icon=":material/settings:")
st.sidebar.page_link(page="pages/4_analitika.py", label="Analitika", icon=":material/monitoring:")
download_guide_doc_file()
logout()


st.sidebar.page_link(page="pages/1_admin.py", label="Qiymətləndirmə", icon=":material/grading:")
st.sidebar.page_link(page="pages/3_idarəetmə.py", label="İdarəetmə", icon=":material/settings:")
st.sidebar.page_link(page="pages/4_analitika.py", label="Analitika", icon=":material/monitoring:")
download_guide_doc_file()
logout()

st.title("İdarəetmə Paneli")
st.divider()

tab1, tab2 = st.tabs(["👤 İstifadəçi İdarəetməsi", "⚙️ Göstərici İdarəetməsi"])
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
                managers = session.query(User).filter(User.is_active == True, User.id != None).all()
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
                    changed_rows = original_df.merge(edited_df, on='ID', suffixes=('_orig', '_new')).query(
                        '`İstifadəçi Adı_orig` != `İstifadəçi Adı_new` or `Tam Adı_orig` != `Tam Adı_new` or '
                        '`Vəzifəsi_orig` != `Vəzifəsi_new` or `Rolu_orig` != `Rolu_new` or `Aktivdir_orig` != `Aktivdir_new`'
                    )
                    if not changed_rows.empty:
                        with get_db() as update_session:
                            update_session.query(User).filter(User.id == user_id).update({
                                'username': row['İstifadəçi Adı_new'], 'role': row['Rolu_new'], 'is_active': row['Aktivdir_new'], 'manager_id': row['Rəhbəri_new'] if row['Rəhbəri_new'] else None
                            })
                                update_session.query(UserProfile).filter(UserProfile.user_id == user_id).update({
                                    'full_name': row['Tam Adı_new'], 'position': row['Vəzifəsi_new']
                                })
                            update_session.commit()
                        st.success(f"{len(changed_rows)} istifadəçinin məlumatları uğurla yeniləndi!")
                        del st.session_state['original_users_df']
                        st.rerun()
                    else:
                        st.warning("Heç bir dəyişiklik edilməyib.")
    except Exception as e:
        st.error(f"İstifadəçilərlə işləyərkən xəta baş verdi: {e}")

with tab2:
    try:
        with get_db() as session:
            total_weight_query = session.query(func.sum(Indicator.weight)).filter(Indicator.is_active == True)
            current_total_weight = total_weight_query.scalar() or 0.0

            st.warning(f"Diqqət: Aktiv göstəricilərin çəkilərinin cəmi 1.0 (100%) olmalıdır. Hazırkı cəm: {current_total_weight:.2f}")
            if current_total_weight != 1.0:
                st.error("Çəkilərin cəmi 1.0 deyil! Zəhmət olmasa, göstəriciləri redaktə edərək cəmi 1.0-a bərabərləşdirin.")

        with st.expander("➕ Yeni Göstərici Yarat"):
            with st.form("new_indicator_form", clear_on_submit=True):
                description = st.text_area("Göstəricinin Təsviri")
                weight = st.number_input("Çəkisi (məsələn, 0.5)", min_value=0.0, max_value=1.0, step=0.01, format="%.2f")
                
                submitted_indicator = st.form_submit_button("Yeni Göstərici Yarat")
                if submitted_indicator:
                    if description and weight > 0:
                        with get_db() as session:
                            new_indicator = Indicator(description=description, weight=weight, is_active=True)
                            session.add(new_indicator)
                            session.commit()
                            st.success(f"'{description}' adlı yeni göstərici uğurla yaradıldı!")
                            st.rerun()
                    else:
                        st.warning("Zəhmət olmasa, bütün xanaları doldurun.")

        st.subheader("Mövcud Göstəricilər")
        with get_db() as session:
            indicators = session.query(Indicator).order_by(Indicator.id).all()
            if indicators:
                df_indicators = pd.DataFrame(
                    [{'ID': ind.id, 'Təsvir': ind.description, 'Çəkisi': ind.weight, 'Aktivdir': ind.is_active} for ind in indicators]
                )
                if 'original_indicators_df' not in st.session_state:
                    st.session_state['original_indicators_df'] = df_indicators.copy()
                
                edited_indicators_df = st.data_editor(
                    df_indicators, use_container_width=True, hide_index=True, key="indicator_editor",
                    column_config={
                        "ID": st.column_config.NumberColumn(disabled=True),
                        "Təsvir": st.column_config.TextColumn(width="large"),
                        "Çəkisi": st.column_config.NumberColumn(format="%.2f", step=0.01),
                        "Aktivdir": st.column_config.CheckboxColumn()
                    }
                )

                if st.button("Göstəriciləri Yadda Saxla"):
                    new_total_weight = edited_indicators_df[edited_indicators_df['Aktivdir'] == True]['Çəkisi'].sum()
                    if abs(new_total_weight - 1.0) > 0.001:
                        st.error(f"Yadda saxlamaq mümkün deyil! Aktiv göstəricilərin yeni cəmi {new_total_weight:.2f} olur. Cəm 1.0 olmalıdır.")
                    else:
                        original_indicators_df = st.session_state.original_indicators_df
                        changed_rows = original_indicators_df.merge(edited_indicators_df, on='ID', suffixes=('_orig', '_new')).query(
                            '`Təsvir_orig` != `Təsvir_new` or `Çəkisi_orig` != `Çəkisi_new` or `Aktivdir_orig` != `Aktivdir_new`'
                        )
                        if not changed_rows.empty:
                            with get_db() as update_session:
                                for index, row in changed_rows.iterrows():
                                    update_session.query(Indicator).filter(Indicator.id == row['ID']).update({
                                        'description': row['Təsvir_new'], 'weight': row['Çəkisi_new'], 'is_active': row['Aktivdir_new']
                                    })
                                update_session.commit()
                            st.success(f"{len(changed_rows)} göstəricinin məlumatları uğurla yeniləndi!")
                            del st.session_state['original_indicators_df']
                            st.rerun()
                        else:
                            st.warning("Heç bir dəyişiklik edilməyib.")

    except Exception as e:
        st.error(f"Göstəricilərlə işləyərkən xəta baş verdi: {e}")