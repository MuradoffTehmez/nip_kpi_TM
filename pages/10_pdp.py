# pages/10_pdp.py

import streamlit as st
st.set_page_config(layout="wide")

import pandas as pd
from datetime import date
from database import get_db
from services.pdp_service import PDPService
from services.kpi_service import KpiService
from services.user_service import UserService
from utils.utils import check_login, logout, show_notifications

# Təhlükəsizlik yoxlaması
current_user = check_login()

# Sidebar menyusu
st.sidebar.page_link(page="pages/2_user.py", label="Şəxsi Panel", icon=":material/person:")
show_notifications()  # Show notifications in sidebar
st.sidebar.page_link(page="pages/6_kpi_idarəetmə.py", label="KPI İdarəetmə", icon=":material/manage_accounts:")
st.sidebar.page_link(page="pages/8_kpi_analitika.py", label="KPI Analitika", icon=":material/monitoring:")
st.sidebar.page_link(page="pages/10_pdp.py", label="Fərdi İnkişaf Planı", icon=":material/checklist:")
logout()

st.title("Fərdi İnkişaf Planı (FİP)")

# İstifadəçinin bütün FİP-lərini əldə edirik
plans = PDPService.get_development_plans_for_user(current_user.id)

if not plans:
    st.info("Hələ heç bir Fərdi İnkişaf Planı yaradılmayıb.")
else:
    # Planları göstərmək
    for plan in plans:
        with st.expander(f"Plan #{plan.id} - Status: {plan.status}", expanded=False):
            st.write(f"**Qiymətləndirmə:** {plan.evaluation.period.name}")
            if plan.manager:
                st.write(f"**Menecer:** {plan.manager.get_full_name()}")
            
            # Plan hədəflərini əldə edirik
            items = PDPService.get_plan_items_for_plan(plan.id)
            
            if not items:
                st.info("Bu plan üçün hələ heç bir hədəf əlavə edilməyib.")
            else:
                # Hədəfləri cədvəl şəklində göstərmək
                items_data = []
                for item in items:
                    items_data.append({
                        "ID": item.id,
                        "Hədəf": item.goal,
                        "Addımlar": item.actions_to_take,
                        "Son tarix": item.deadline.strftime('%d.%m.%Y'),
                        "İnkişaf (%)": item.progress,
                        "Status": item.status,
                        "Tamamlandı": "✅" if item.is_completed else "❌"
                    })
                
                df_items = pd.DataFrame(items_data)
                st.dataframe(df_items, use_container_width=True)
                
                # Hər bir hədəf üçün detallı baxış
                for item in items:
                    with st.expander(f"Hədəf: {item.goal}", expanded=False):
                        st.write(f"**Addımlar:** {item.actions_to_take}")
                        st.write(f"**Son tarix:** {item.deadline.strftime('%d.%m.%Y')}")
                        
                        # İnkişaf slayderi
                        progress = st.slider(
                            "İnkişaf (%)", 
                            min_value=0, 
                            max_value=100, 
                            value=item.progress, 
                            key=f"progress_slider_{item.id}"
                        )
                        
                        # Status dropdown
                        status_options = ["Başlanmayıb", "Davam edir", "Tamamlanıb"]
                        status = st.selectbox(
                            "Status", 
                            options=status_options, 
                            index=status_options.index(item.status) if item.status in status_options else 0,
                            key=f"status_select_{item.id}"
                        )
                        
                        # Yeniləmək düyməsi
                        if st.button("Yenilə", key=f"update_button_{item.id}"):
                            PDPService.update_plan_item_progress(item.id, progress, status)
                            st.success("Hədəf yeniləndi!")
                            st.rerun()
                        
                        # Şərhlər bölməsi
                        st.subheader("Şərhlər")
                        comments = PDPService.get_comments_for_plan_item(item.id)
                        if comments:
                            for comment in comments:
                                author = UserService.get_user_by_id(comment.author_id)
                                st.markdown(f"**{author.get_full_name() if author else 'Naməlum'}** - {comment.created_at.strftime('%d.%m.%Y %H:%M')}")
                                st.markdown(f"> {comment.comment_text}")
                                st.markdown("---")
                        else:
                            st.info("Hələ heç bir şərh yoxdur.")
                        
                        # Yeni şərh əlavə etmək
                        with st.form(f"comment_form_{item.id}"):
                            comment_text = st.text_area("Şərh əlavə edin")
                            submitted = st.form_submit_button("Şərh Əlavə Et")
                            if submitted and comment_text:
                                PDPService.add_comment_to_plan_item(item.id, current_user.id, comment_text)
                                st.success("Şərh əlavə edildi!")
                                st.rerun()
            
            # Yeni hədəf əlavə etmək
            st.divider()
            st.subheader("Yeni Hədəf Əlavə Et")
            
            with st.form(f"new_item_form_{plan.id}"):
                goal = st.text_input("Hədəf")
                actions = st.text_area("Atılacaq addımlar")
                deadline = st.date_input("Son tarix", value=date.today())
                
                submitted = st.form_submit_button("Əlavə Et")
                if submitted and goal and actions:
                    PDPService.create_plan_item(
                        plan_id=plan.id,
                        goal=goal,
                        actions_to_take=actions,
                        deadline=deadline
                    )
                    st.success("Hədəf uğurla əlavə edildi!")
                    st.rerun()

# Yeni FİP yaratmaq
st.divider()
st.subheader("Yeni Fərdi İnkişaf Planı Yarat")

# Qiymətləndirmə dövrlərini əldə edirik
periods = KpiService.get_all_evaluation_periods()

if not periods:
    st.info("Hələ heç bir qiymətləndirmə dövrü yaradılmayıb.")
else:
    period_options = [p.name for p in periods]
    selected_period_name = st.selectbox("Qiymətləndirmə dövrünü seçin:", options=period_options, index=0)
    selected_period = next((p for p in periods if p.name == selected_period_name), None)
    
    if selected_period:
        # Bu dövr üçün qiymətləndirmələri əldə edirik
        with get_db() as session:
            from models.kpi import Evaluation
            evaluations = session.query(Evaluation).filter(
                Evaluation.period_id == selected_period.id,
                Evaluation.evaluated_user_id == current_user.id
            ).all()
            
            if not evaluations:
                st.warning("Bu dövr üçün qiymətləndirməniz yoxdur.")
            else:
                # Qiymətləndirməni seçmək
                eval_options = [f"{e.period.name} - Qiymətləndirən: {UserService.get_user_by_id(e.evaluator_user_id).get_full_name()}" for e in evaluations]
                selected_eval_index = st.selectbox("Qiymətləndirmə seçin:", options=eval_options, index=0)
                selected_eval = evaluations[eval_options.index(selected_eval_index)]
                
                if st.button("FİP Yarat"):
                    # Yeni FİP yaradırıq
                    plan = PDPService.create_development_plan(
                        user_id=current_user.id,
                        evaluation_id=selected_eval.id,
                        manager_id=selected_eval.evaluator_user_id
                    )
                    st.success(f"Yeni Fərdi İnkişaf Planı (#{plan.id}) uğurla yaradıldı!")
                    st.rerun()