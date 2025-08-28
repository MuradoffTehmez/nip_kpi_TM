import streamlit as st
import pandas as pd
from sqlalchemy import select, update
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
            new_username = st.text_input("İstifadəçi Adı (login üçün)")
            new_password = st.text_input("Şifrə", type="password")
            new_role = st.selectbox("Rolu", ["user", "admin"])
        
        with col2:
            new_full_name = st.text_input("Tam Adı (Ad, Soyad)")
            new_position = st.text_input("Vəzifəsi")

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
                        user_to_add = User(username=new_username, password=new_password, role=new_role)
                        session.add(user_to_add)
                        session.commit()
                        session.refresh(user_to_add)

                        profile_to_add = UserProfile(user_id=user_to_add.id, full_name=new_full_name, position=new_position)
                        session.add(profile_to_add)
                        session.commit()

                        st.success(f"İstifadəçi '{new_full_name}' uğurla yaradıldı!")
                        st.rerun()

st.divider()

# --- Mövcud İstifadəçiləri Redaktə Etmək Bölməsi ---
st.header("Mövcud İstifadəçilər")

try:
    with get_db() as session:
        users_query = session.query(
            User.id, User.username, UserProfile.full_name,
            UserProfile.position, User.role, User.is_active
        ).join(UserProfile, User.id == UserProfile.user_id).order_by(User.id)

        users_data = users_query.all()

        if users_data:
            df_users = pd.DataFrame(users_data, columns=[
                "ID", "İstifadəçi Adı", "Tam Adı", "Vəzifəsi", "Rolu", "Aktivdir"
            ])
            
            # st.data_editor-dan gələn dəyişiklikləri yadda saxlamaq üçün orijinal cədvəli yaddaşda saxlayırıq
            if 'original_users_df' not in st.session_state:
                st.session_state['original_users_df'] = df_users.copy()

            st.info("Məlumatları redaktə etmək üçün cədvəldəki xanalara iki dəfə klikləyin. Dəyişiklikləri tətbiq etmək üçün 'Yadda Saxla' düyməsinə basın.")

            edited_df = st.data_editor(
                df_users,
                use_container_width=True,
                hide_index=True,
                key="user_editor",
                column_config={
                    "ID": st.column_config.NumberColumn("ID", disabled=True),
                    "Rolu": st.column_config.SelectboxColumn("Rolu", options=["user", "admin"]),
                    "Aktivdir": st.column_config.CheckboxColumn("Aktivdir")
                }
            )

            if st.button("Dəyişiklikləri Yadda Saxla"):
                original_df = st.session_state.original_users_df
                # Dəyişmiş sətirləri tapmaq üçün cədvəlləri müqayisə edirik
                changed_rows = original_df.merge(edited_df, on='ID', suffixes=('_orig', '_new')).query(
                    '`İstifadəçi Adı_orig` != `İstifadəçi Adı_new` or '
                    '`Tam Adı_orig` != `Tam Adı_new` or '
                    '`Vəzifəsi_orig` != `Vəzifəsi_new` or '
                    '`Rolu_orig` != `Rolu_new` or '
                    '`Aktivdir_orig` != `Aktivdir_new`'
                )

                if not changed_rows.empty:
                    with get_db() as update_session:
                        for index, row in changed_rows.iterrows():
                            user_id = row['ID']
                            # User cədvəli üçün yeniləmələr
                            update_session.query(User).filter(User.id == user_id).update({
                                'username': row['İstifadəçi Adı_new'],
                                'role': row['Rolu_new'],
                                'is_active': row['Aktivdir_new']
                            })
                            # UserProfile cədvəli üçün yeniləmələr
                            update_session.query(UserProfile).filter(UserProfile.user_id == user_id).update({
                                'full_name': row['Tam Adı_new'],
                                'position': row['Vəzifəsi_new']
                            })
                        update_session.commit()
                    st.success(f"{len(changed_rows)} istifadəçinin məlumatları uğurla yeniləndi!")
                    # Səhifəni yeniləyərək ən son məlumatları göstəririk
                    del st.session_state['original_users_df']
                    st.rerun()
                else:
                    st.warning("Heç bir dəyişiklik edilməyib.")

except Exception as e:
    st.error(f"Verilənlər bazasından məlumatları çəkərkən xəta baş verdi: {e}")