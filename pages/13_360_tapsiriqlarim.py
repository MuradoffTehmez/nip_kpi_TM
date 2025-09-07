# pages/13_360_tapsiriqlarim.py

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

# Sidebar menyusu
st.sidebar.page_link(page="pages/2_user.py", label="Şəxsi Panel", icon=":material/person:")
show_notifications()  # Show notifications in sidebar
st.sidebar.page_link(page="pages/13_360_tapsiriqlarim.py", label="360° Tapşırıqlarım", icon=":material/task:")
logout()

st.title(f"360° Qiymətləndirmə Tapşırıqlarım - Xoş gəldiniz, {current_user.get_full_name()}!")

# İstifadəçinin iştirak etdiyi bütün 360° sessiyaları əldə edirik
sessions = Degree360Service.get_360_sessions_for_user(current_user.id)

if not sessions:
    st.info("Hələ heç bir 360° qiymətləndirmə tapşırığınız yoxdur.")
else:
    pending_sessions = []
    completed_sessions = []
    
    for session in sessions:
        # İstifadəçinin bu sessiyada iştirakçı olub-olmadığını yoxlayırıq
        participants = Degree360Service.get_participants_for_360_session(session.id)
        user_participation = [p for p in participants if p.evaluator_user_id == current_user.id]
        
        if user_participation:
            for participation in user_participation:
                session_info = {
                    "session": session,
                    "participation": participation,
                    "evaluated_user": session.evaluated_user.get_full_name(),
                    "role": participation.role.value,
                    "status": participation.status
                }
                
                if participation.status == "PENDING":
                    pending_sessions.append(session_info)
                elif participation.status == "COMPLETED":
                    completed_sessions.append(session_info)
    
    # Gözləyən tapşırıqlar
    if pending_sessions:
        st.header("Gözləyən Tapşırıqlar")
        
        # Vaxtı yaxınlaşan tapşırıqlar üçün xəbərdarlıq
        upcoming_deadlines = []
        for session_info in pending_sessions:
            session = session_info["session"]
            days_until_deadline = (session.end_date - date.today()).days
            if days_until_deadline <= 3:
                upcoming_deadlines.append({
                    "session_name": session.name,
                    "evaluated_user": session_info["evaluated_user"],
                    "days_left": days_until_deadline
                })
        
        if upcoming_deadlines:
            st.warning("⚠️ Aşağıdakı tapşırıqların bitməsinə az bir zaman qalıb:")
            for deadline in upcoming_deadlines:
                st.write(f"- **{deadline['session_name']}** ({deadline['evaluated_user']}) - {deadline['days_left']} gün qalıb")
            st.divider()
        
        for session_info in pending_sessions:
            session = session_info["session"]
            participation = session_info["participation"]
            evaluated_user = session_info["evaluated_user"]
            role = session_info["role"]
            
            with st.expander(f"{session.name} - Qiymətləndirilən: {evaluated_user} ({role})", expanded=False):
                st.write(f"**Başlama tarixi:** {session.start_date.strftime('%d.%m.%Y')}")
                st.write(f"**Bitmə tarixi:** {session.end_date.strftime('%d.%m.%Y')}")
                
                # Vaxt qalığı göstər
                days_until_deadline = (session.end_date - date.today()).days
                if days_until_deadline <= 3:
                    st.error(f"⚠️ Bitməyə {days_until_deadline} gün qalıb!")
                elif days_until_deadline <= 7:
                    st.warning(f"⚠️ Bitməyə {days_until_deadline} gün qalıb")
                
                # Sessiyanın suallarını əldə edirik
                questions = Degree360Service.get_questions_for_360_session(session.id)
                
                if not questions:
                    st.info("Bu sessiya üçün hələ sual əlavə edilməyib.")
                else:
                    # Sual kateqoriyalarına görə qruplaşdır
                    categories = {}
                    for question in questions:
                        category = question.category
                        if category not in categories:
                            categories[category] = []
                        categories[category].append(question)
                    
                    # Cavabları əldə edirik (əgər varsa)
                    existing_answers = Degree360Service.get_answers_for_360_participant(participation.id)
                    answer_dict = {a.question_id: a for a in existing_answers}
                    
                    # Cavab forması
                    with st.form(f"answer_form_{participation.id}"):
                        answers_data = {}
                        
                        # Kateqoriya üzrə sualları göstər
                        for category, category_questions in categories.items():
                            st.subheader(f"Kateqoriya: {category}")
                            st.markdown("---")
                            
                            for question in category_questions:
                                st.markdown(f"**{question.text}**")
                                st.caption(f"Çəki: {question.weight}")
                                
                                # Əgər cavab artıq verilibsə, onu göstər
                                existing_answer = answer_dict.get(question.id)
                                score = st.slider(
                                    "Bal", 
                                    1, 5, 
                                    value=existing_answer.score if existing_answer else 3, 
                                    key=f"score_{question.id}_{participation.id}",
                                    help="1 - Çox zəif, 5 - Əla"
                                )
                                comment = st.text_area(
                                    "Şərh (vacib deyil)", 
                                    value=existing_answer.comment if existing_answer else "",
                                    key=f"comment_{question.id}_{participation.id}",
                                    placeholder="Fikirlərinizi əlavə edin..."
                                )
                                
                                answers_data[question.id] = {"score": score, "comment": comment}
                                
                                if question != category_questions[-1] or category != list(categories.keys())[-1]:
                                    st.markdown("---")
                        
                        submitted = st.form_submit_button("Cavabları Yadda Saxla", use_container_width=True, type="primary")
                        if submitted:
                            try:
                                # Cavabları formatla
                                formatted_answers = [
                                    {
                                        "question_id": q_id,
                                        "score": ans["score"],
                                        "comment": ans["comment"]
                                    }
                                    for q_id, ans in answers_data.items()
                                ]
                                
                                # Cavabları təsdiqlə
                                Degree360Service.submit_answers_for_360_participant(
                                    participant_id=participation.id,
                                    answers=formatted_answers
                                )
                                
                                st.success("Cavablarınız uğurla yadda saxlanıldı!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Cavabları yadda saxlayarkən xəta baş verdi: {str(e)}")
    else:
        st.info("Hal-hazırda tamamlanmalı 360° qiymətləndirmə tapşırığınız yoxdur.")
    
    st.divider()
    
    # Tamamlanmış tapşırıqlar
    if completed_sessions:
        st.header("Tamamlanmış Tapşırıqlar")
        
        completed_data = []
        for session_info in completed_sessions:
            session = session_info["session"]
            evaluated_user = session_info["evaluated_user"]
            role = session_info["role"]
            
            completed_data.append({
                "Sessiya": session.name,
                "Qiymətləndirilən": evaluated_user,
                "Rol": role,
                "Tarix": session.end_date.strftime('%d.%m.%Y')
            })
        
        df_completed = pd.DataFrame(completed_data)
        st.dataframe(df_completed, use_container_width=True)
        
        # Hesabat səhifəsinə keçid
        st.info("Tamamlanmış 360° qiymətləndirmələrin ətraflı hesabatlarını görmək üçün aşağıdakı düyməyə klikləyin:")
        if st.button("360° Hesabatlar", type="primary"):
            st.switch_page("pages/14_360_hesabatlar.py")
    else:
        st.info("Hələ heç bir 360° qiymətləndirmə tapşırığını tamamlamısınız.")