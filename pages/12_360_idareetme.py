# pages/12_360_idareetme.py

import streamlit as st
st.set_page_config(layout="wide")

import pandas as pd
from datetime import date
from database import get_db
from services.degree360_service import Degree360Service
from services.user_service import UserService
from utils.utils import check_login, logout, show_notifications
from models.degree360 import Degree360ParticipantRole

# Təhlükəsizlik yoxlaması
current_user = check_login()
if current_user.role != "admin":
    st.error("Bu səhifəyə giriş üçün icazəniz yoxdur.")
    st.stop()

# Sidebar menyusu
st.sidebar.page_link(page="pages/6_kpi_idarəetmə.py", label="KPI İdarəetmə", icon=":material/settings:")
show_notifications()  # Show notifications in sidebar
st.sidebar.page_link(page="pages/8_kpi_analitika.py", label="KPI Analitika", icon=":material/monitoring:")
st.sidebar.page_link(page="pages/11_9box_grid.py", label="9-Box Grid", icon=":material/grid_view:")
st.sidebar.page_link(page="pages/12_360_idareetme.py", label="360° İdarəetmə", icon=":material/manage_accounts:")
logout()

st.title("360° Qiymətləndirmə İdarəetmə Paneli")

# Tabs
tab1, tab2, tab3 = st.tabs(["Yeni Sessiya Yarat", "Mövcud Sessiyalar", "İştirakçılar"])

with tab1:
    st.header("Yeni 360° Qiymətləndirmə Sessiyası Yarat")
    
    with st.form("new_360_session_form"):
        session_name = st.text_input("Sessiyanın adı", placeholder="Məsələn, 2025-ci il 360° Qiymətləndirməsi")
        
        # Qiymətləndiriləcək işçini seç
        all_users = UserService.get_all_active_users()
        user_options = {u.id: u.get_full_name() for u in all_users}
        evaluated_user_id = st.selectbox(
            "Qiymətləndiriləcək işçi", 
            options=list(user_options.keys()), 
            format_func=lambda x: user_options[x]
        )
        
        # Sessiyanı yaradan rəhbəri seç (özünü də daxil et)
        evaluator_user_options = {u.id: u.get_full_name() for u in all_users}
        evaluator_user_id = st.selectbox(
            "Sessiyanı yaradan rəhbər", 
            options=list(evaluator_user_options.keys()), 
            format_func=lambda x: evaluator_user_options[x],
            index=list(evaluator_user_options.keys()).index(current_user.id) if current_user.id in evaluator_user_options else 0
        )
        
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Başlama tarixi", value=date.today())
        with col2:
            end_date = st.date_input("Bitmə tarixi", value=date.today().replace(year=date.today().year + 1))
        
        submitted = st.form_submit_button("Sessiyanı Yarat")
        if submitted and session_name and evaluated_user_id and evaluator_user_id:
            if start_date >= end_date:
                st.error("Bitmə tarixi başlama tarixindən sonra olmalıdır.")
            else:
                try:
                    new_session = Degree360Service.create_360_session(
                        name=session_name,
                        evaluated_user_id=evaluated_user_id,
                        evaluator_user_id=evaluator_user_id,
                        start_date=start_date,
                        end_date=end_date
                    )
                    st.success(f"Yeni 360° Qiymətləndirmə Sessiyası (#{new_session.id}) uğurla yaradıldı!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Sessiya yaratma zamanı xəta baş verdi: {str(e)}")

with tab2:
    st.header("Mövcud 360° Qiymətləndirmə Sessiyaları")
    
    sessions = Degree360Service.get_all_active_360_sessions()
    
    if not sessions:
        st.info("Hələ heç bir 360° qiymətləndirmə sessiyası yaradılmayıb.")
    else:
        for session in sessions:
            with st.expander(f"{session.name} - Qiymətləndirilən: {session.evaluated_user.get_full_name()}", expanded=False):
                st.write(f"**Başlama tarixi:** {session.start_date.strftime('%d.%m.%Y')}")
                st.write(f"**Bitmə tarixi:** {session.end_date.strftime('%d.%m.%Y')}")
                st.write(f"**Status:** {session.status}")
                st.write(f"**Sessiyanı yaradan:** {session.evaluator_user.get_full_name()}")
                
                # İştirakçılar siyahısı
                participants = Degree360Service.get_participants_for_360_session(session.id)
                if participants:
                    participant_data = []
                    for p in participants:
                        participant_data.append({
                            "İştirakçı": p.evaluator_user.get_full_name(),
                            "Rol": p.role.value,
                            "Status": p.status
                        })
                    df_participants = pd.DataFrame(participant_data)
                    st.dataframe(df_participants, use_container_width=True)
                else:
                    st.info("Bu sessiyaya hələ heç bir iştirakçı əlavə edilməyib.")
                
                # Sessiyanı idarəetmə düymələri
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("İştirakçı Əlavə Et", key=f"add_participant_{session.id}"):
                        st.session_state[f"show_add_participant_{session.id}"] = True
                        st.rerun()
                with col2:
                    if st.button("Sual Əlavə Et", key=f"add_question_{session.id}"):
                        st.session_state[f"show_add_question_{session.id}"] = True
                        st.rerun()
                with col3:
                    if st.button("Nəticələri Göstər", key=f"show_results_{session.id}"):
                        st.session_state[f"show_results_{session.id}"] = True
                        st.rerun()
                
                # İştirakçı əlavə etmə forması
                if st.session_state.get(f"show_add_participant_{session.id}", False):
                    with st.form(f"add_participant_form_{session.id}"):
                        st.subheader("İştirakçı Əlavə Et")
                        participant_user_options = {u.id: u.get_full_name() for u in all_users}
                        participant_user_id = st.selectbox(
                            "İştirakçı seçin", 
                            options=list(participant_user_options.keys()), 
                            format_func=lambda x: participant_user_options[x],
                            key=f"participant_user_{session.id}"
                        )
                        
                        role_options = [role.value for role in Degree360ParticipantRole]
                        role = st.selectbox(
                            "Rol", 
                            options=role_options,
                            key=f"participant_role_{session.id}"
                        )
                        
                        submitted = st.form_submit_button("Əlavə Et")
                        if submitted and participant_user_id:
                            try:
                                # Rolu enum-a çevir
                                role_enum = Degree360ParticipantRole(role)
                                Degree360Service.add_participant_to_360_session(
                                    session_id=session.id,
                                    evaluator_user_id=participant_user_id,
                                    role=role_enum
                                )
                                st.success("İştirakçı uğurla əlavə edildi!")
                                del st.session_state[f"show_add_participant_{session.id}"]
                                st.rerun()
                            except Exception as e:
                                st.error(f"İştirakçı əlavə edərkən xəta baş verdi: {str(e)}")
                
                # Sual əlavə etmə forması
                if st.session_state.get(f"show_add_question_{session.id}", False):
                    with st.form(f"add_question_form_{session.id}"):
                        st.subheader("Sual Əlavə Et")
                        question_text = st.text_area("Sualın mətni")
                        question_category = st.text_input("Kateqoriya", value="Ümumi")
                        question_weight = st.slider("Çəki", min_value=1, max_value=5, value=1)
                        
                        submitted = st.form_submit_button("Əlavə Et")
                        if submitted and question_text:
                            try:
                                Degree360Service.add_question_to_360_session(
                                    session_id=session.id,
                                    text=question_text,
                                    category=question_category,
                                    weight=question_weight
                                )
                                st.success("Sual uğurla əlavə edildi!")
                                del st.session_state[f"show_add_question_{session.id}"]
                                st.rerun()
                            except Exception as e:
                                st.error(f"Sual əlavə edərkən xəta baş verdi: {str(e)}")
                
                # Nəticələri göstərmə
                if st.session_state.get(f"show_results_{session.id}", False):
                    try:
                        results = Degree360Service.calculate_360_session_results(session.id)
                        if results:
                            st.subheader("Nəticələr")
                            st.write(f"**Qiymətləndirilən işçi:** {results['evaluated_user']}")
                            st.write(f"**Ümumi bal:** {results['overall_score']}")
                            
                            # Rol üzrə ballar
                            if results['scores_by_role']:
                                st.write("**Rol üzrə ballar:**")
                                for role, score in results['scores_by_role'].items():
                                    st.write(f"- {role}: {score}")
                            
                            # Ətraflı nəticələr
                            if results['detailed_results']:
                                st.write("**Ətraflı nəticələr:**")
                                df_detailed = pd.DataFrame(results['detailed_results'])
                                st.dataframe(df_detailed, use_container_width=True)
                        else:
                            st.info("Bu sessiya üçün hələ nəticə yoxdur.")
                    except Exception as e:
                        st.error(f"Nəticələri əldə edərkən xəta baş verdi: {str(e)}")

with tab3:
    st.header("Bütün İştirakçılar")
    
    # Bütün iştirakçıları əldə et
    with get_db() as session:
        from models.degree360 import Degree360Participant
        participants = session.query(Degree360Participant).all()
        
        if not participants:
            st.info("Hələ heç bir iştirakçı yoxdur.")
        else:
            participant_data = []
            for p in participants:
                participant_data.append({
                    "İştirakçı": p.evaluator_user.get_full_name(),
                    "Rol": p.role.value,
                    "Status": p.status,
                    "Sessiya": p.session.name if p.session else "Naməlum"
                })
            df_participants = pd.DataFrame(participant_data)
            st.dataframe(df_participants, use_container_width=True)