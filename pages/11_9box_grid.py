# pages/11_9box_grid.py

import streamlit as st
st.set_page_config(layout="wide")

import pandas as pd
import altair as alt
import numpy as np
from database import get_db
from services.kpi_service import KpiService
from services.user_service import UserService
from services.pdp_service import PDPService
from utils.utils import check_login, logout, show_notifications

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
logout()

st.title("İstedadların Təsnifatı (9-Box Grid)")

# Qiymətləndirmə dövrlərini əldə edirik
periods = KpiService.get_all_evaluation_periods()

if not periods:
    st.info("Hələ heç bir qiymətləndirmə dövrü yaradılmayıb.")
    st.stop()

period_options = [p.name for p in periods]
selected_period_name = st.selectbox("Qiymətləndirmə dövrünü seçin:", options=period_options, index=0)
selected_period = next((p for p in periods if p.name == selected_period_name), None)

if not selected_period:
    st.error("Seçilmiş dövr tapılmadı.")
    st.stop()

period_id = selected_period.id

st.divider()

# 9-Box Grid üçün məlumatları əldə edirik
# Bu nümunədə sadələşdirilmiş versiya göstərilir
# Real tətbiqdə burada KPI nəticələri və rəhbərin subyektiv qiymətləndirməsi əsasında hesablama aparılmalıdır

# Sadələşdirilmiş nümunə: 
# X oxu (Performans) - KPI nəticələri əsasında (0-5 arası)
# Y oxu (Potensial) - Rəhbərin qiymətləndirməsi əsasında (0-5 arası)

# Bu nümunədə hər bir işçi üçün təsadüfi qiymətlər yaradırıq
np.random.seed(42)  # Təkrarlanan nəticələr üçün sabit tohum
users = UserService.get_all_active_users()
grid_data = []

for user in users:
    # KPI nəticəsi (0-5 arası təsadüfi qiymət)
    kpi_score = np.random.uniform(2.0, 5.0)
    
    # Potensial (0-5 arası təsadüfi qiymət)
    potential_score = np.random.uniform(2.0, 5.0)
    
    grid_data.append({
        "id": user.id,
        "full_name": user.get_full_name(),
        "kpi_score": kpi_score,
        "potential_score": potential_score
    })

df_grid = pd.DataFrame(grid_data)

# 9-Box Grid matrisini yaradırıq
# X oxu (Performans): 3 qrup - Aşağı (0-2.5), Orta (2.5-3.5), Yüksək (3.5-5)
# Y oxu (Potensial): 3 qrup - Aşağı (0-2.5), Orta (2.5-3.5), Yüksək (3.5-5)

def categorize_performance(score):
    """Performans kateqoriyasını müəyyənləşdirir."""
    if score < 2.5:
        return "Aşağı Performans"
    elif 2.5 <= score <= 3.5:
        return "Orta Performans"
    else:
        return "Yüksək Performans"

def categorize_potential(score):
    """Potensial kateqoriyasını müəyyənləşdirir."""
    if score < 2.5:
        return "Aşağı Potensial"
    elif 2.5 <= score <= 3.5:
        return "Orta Potensial"
    else:
        return "Yüksək Potensial"

df_grid['performance_category'] = df_grid['kpi_score'].apply(categorize_performance)
df_grid['potential_category'] = df_grid['potential_score'].apply(categorize_potential)

# 9-Box Grid üçün vizuallaşdırma
st.header("9-Box Grid Matrisi")

# 9-Box Grid üçün Altair chart yaratmaq
# X oxu - Performans (soldan sağa: Aşağı -> Orta -> Yüksək)
# Y oxu - Potensial (aşağıdan yuxarı: Aşağı -> Orta -> Yüksək)

# Kateqoriyaların düzülüş sırası
performance_order = ["Aşağı Performans", "Orta Performans", "Yüksək Performans"]
potential_order = ["Aşağı Potensial", "Orta Potensial", "Yüksək Potensial"]

# Scatter plot yaratmaq
scatter = alt.Chart(df_grid).mark_circle(size=100).encode(
    x=alt.X('performance_category:N', 
            title='Performans (KPI Nəticələri)', 
            sort=performance_order),
    y=alt.Y('potential_category:N', 
            title='Potensial (Rəhbərin Qiymətləndirməsi)', 
            sort=potential_order),
    tooltip=['full_name:N', 'kpi_score:Q', 'potential_score:Q'],
    color=alt.Color('full_name:N', legend=None)
).properties(
    title='İşçilərin 9-Box Grid Üzrə Yerləşməsi',
    width=600,
    height=400
)

# Grid xətlərini əlavə edirik
vline1 = alt.Chart(pd.DataFrame({'x': ['Orta Performans']})).mark_rule(color='gray', strokeDash=[5,5]).encode(x='x:N')
vline2 = alt.Chart(pd.DataFrame({'x': ['Yüksək Performans']})).mark_rule(color='gray', strokeDash=[5,5]).encode(x='x:N')
hline1 = alt.Chart(pd.DataFrame({'y': ['Orta Potensial']})).mark_rule(color='gray', strokeDash=[5,5]).encode(y='y:N')
hline2 = alt.Chart(pd.DataFrame({'y': ['Yüksək Potensial']})).mark_rule(color='gray', strokeDash=[5,5]).encode(y='y:N')

chart = (scatter + vline1 + vline2 + hline1 + hline2)
st.altair_chart(chart, use_container_width=True)

# Cədvəl şəklində məlumatları göstərmək
st.divider()
st.header("Ətraflı Məlumat")

# Hər bir kateqoriyada olan işçiləri göstərmək
for potential_cat in potential_order:
    for performance_cat in performance_order:
        employees_in_box = df_grid[
            (df_grid['potential_category'] == potential_cat) & 
            (df_grid['performance_category'] == performance_cat)
        ]
        
        if not employees_in_box.empty:
            box_title = f"{potential_cat} / {performance_cat}"
            with st.expander(box_title, expanded=False):
                st.dataframe(
                    employees_in_box[['full_name', 'kpi_score', 'potential_score']].rename(columns={
                        'full_name': 'Əməkdaş',
                        'kpi_score': 'KPI Balı',
                        'potential_score': 'Potensial Balı'
                    }),
                    use_container_width=True
                )

# İşçilərin siyahısı və onların koordinatları
st.divider()
st.header("Bütün İşçilər")
st.dataframe(
    df_grid[['full_name', 'kpi_score', 'potential_score', 'performance_category', 'potential_category']].rename(columns={
        'full_name': 'Əməkdaş',
        'kpi_score': 'KPI Balı',
        'potential_score': 'Potensial Balı',
        'performance_category': 'Performans Kateqoriyası',
        'potential_category': 'Potensial Kateqoriyası'
    }),
    use_container_width=True
)

# Real tətbiqdə burada aşağıdakı funksionallıqlar əlavə edilə bilər:
# 1. Hər bir işçi üçün real KPI nəticələrini əldə etmək
# 2. Rəhbərlərin hər bir işçi üçün potensial qiymətləndirməsi əlavə etməsi üçün interfeys
# 3. 9-Box Grid-in interaktiv şəkildə yenilənməsi
# 4. Hər bir kvadrat üçün təkliflər (məsələn, "Yüksək Performans/Yüksək Potensial" üçün "Liderlikə Hazırlıq" və s.)