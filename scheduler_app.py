# MAMA NGINA UNIVERSITY COLLEGE
# AUTOMATED CLASS SCHEDULER & DASHBOARD


import streamlit as st
import pulp
import pandas as pd
import plotly.express as px


# 1. PAGE CONFIGURATION
st.set_page_config(
    page_title="MNUC Scheduler",
    layout="wide"
)

st.title("Mama Ngina University College: Smart Scheduler")
st.markdown("Optimization-driven scheduling for the School of Pure & Applied Sciences.")


# 2. DATA SETUP (The "Database")
@st.cache_data
def load_data():
    # A. Rooms
    rooms = {
        'Lab_1': 40,    'Lab_2': 40,
        'Hall_A': 100,  'Hall_B': 100,
        'Room_C': 60,   'Room_D': 60
    }

    # B. Time Slots
    # We map specific hours for the Gantt Chart visualization
    time_map = {
        '08:00-10:00': {'start': '08:00', 'end': '10:00', 'duration': 2},
        '11:00-13:00': {'start': '11:00', 'end': '13:00', 'duration': 2},
        '14:00-17:00': {'start': '14:00', 'end': '17:00', 'duration': 3}
    }
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']
    slots = list(time_map.keys())

    # C. Lecturers
    lecturers = [
        'Dr. Wanjiku (CS)', 'Prof. Omondi (IT)', 'Mr. Kamau (Math/CS)', 
        'Dr. Chebet (Stats)', 'Mrs. Njoroge (Library Sc)',
        'Prof. Hassan (Env Sci)', 'Dr. Akinyi (Hosp)', 'Mr. Juma (Env Health)', 
        'Ms. Otieno (Comm Dev)', 'Dr. Koech (Climate)'
    ]

    # D. Courses
    events_data = [
        {'Course': 'COM 110: Intro to Programming', 'Group': 'BSc CS Y1', 'Lecturer': 'Dr. Wanjiku (CS)', 'Size': 80, 'Dept': 'Computing'},
        {'Course': 'COM 220: Data Structures',       'Group': 'BSc CS Y2', 'Lecturer': 'Dr. Wanjiku (CS)', 'Size': 75, 'Dept': 'Computing'},
        {'Course': 'BIT 111: Fund. of IT',          'Group': 'BIT Y1',    'Lecturer': 'Prof. Omondi (IT)', 'Size': 85, 'Dept': 'Computing'},
        {'Course': 'BIT 212: Database Systems',     'Group': 'BIT Y2',    'Lecturer': 'Prof. Omondi (IT)', 'Size': 80, 'Dept': 'Computing'},
        {'Course': 'MAT 101: Calculus I',           'Group': 'BSc MathCS Y1', 'Lecturer': 'Mr. Kamau (Math/CS)', 'Size': 60, 'Dept': 'Computing'},
        {'Course': 'COM 301: Algorithms',           'Group': 'BSc MathCS Y3', 'Lecturer': 'Mr. Kamau (Math/CS)', 'Size': 50, 'Dept': 'Computing'},
        {'Course': 'STA 102: Probability I',        'Group': 'BSc StatProg Y1', 'Lecturer': 'Dr. Chebet (Stats)', 'Size': 65, 'Dept': 'Computing'},
        {'Course': 'STA 305: Regression Analysis',  'Group': 'BSc StatProg Y3', 'Lecturer': 'Dr. Chebet (Stats)', 'Size': 55, 'Dept': 'Computing'},
        {'Course': 'LIS 101: Info & Society',       'Group': 'BLIS Y1',   'Lecturer': 'Mrs. Njoroge (Library Sc)', 'Size': 50, 'Dept': 'Computing'},
        {'Course': 'HTM 100: Intro to Hospitality', 'Group': 'BSc Hosp Y1', 'Lecturer': 'Dr. Akinyi (Hosp)', 'Size': 70, 'Dept': 'Environment'},
        {'Course': 'HTM 210: Food Production',      'Group': 'BSc Hosp Y2', 'Lecturer': 'Dr. Akinyi (Hosp)', 'Size': 65, 'Dept': 'Environment'},
        {'Course': 'EVH 101: Public Health',        'Group': 'BSc EnvHealth Y1', 'Lecturer': 'Mr. Juma (Env Health)', 'Size': 55, 'Dept': 'Environment'},
        {'Course': 'ECD 105: Community Dev',        'Group': 'BSc EnvCom Y1', 'Lecturer': 'Ms. Otieno (Comm Dev)', 'Size': 60, 'Dept': 'Environment'},
        {'Course': 'ENS 201: Ecology',              'Group': 'BSc EnvSci Y2', 'Lecturer': 'Prof. Hassan (Env Sci)', 'Size': 55, 'Dept': 'Environment'},
        {'Course': 'ENS 401: Env Impact Assess',    'Group': 'BSc EnvSci Y4', 'Lecturer': 'Prof. Hassan (Env Sci)', 'Size': 40, 'Dept': 'Environment'},
        {'Course': 'CRM 101: Resource Mgmt',        'Group': 'BSc CRM Y1',    'Lecturer': 'Ms. Otieno (Comm Dev)', 'Size': 50, 'Dept': 'Environment'},
        {'Course': 'MES 501: Climate Modeling',     'Group': 'MSc Climate Y1', 'Lecturer': 'Dr. Koech (Climate)', 'Size': 20, 'Dept': 'Environment'},
        {'Course': 'UCI 101: Foundations of Knowledge', 'Group': 'All Y1', 'Lecturer': 'Mrs. Njoroge (Library Sc)', 'Size': 100, 'Dept': 'Common'}
    ]
    
    df = pd.DataFrame(events_data)
    # Create unique EventID
    df['EventID'] = df['Course'] + "_" + df['Group']
    return rooms, days, slots, time_map, lecturers, df

# Load Data
rooms, days, slots, time_map, lecturers, df_events = load_data()


# 3. SIDEBAR CONTROLS
st.sidebar.header("Scheduler Settings")

if st.sidebar.button("Run Optimization"):
    with st.spinner("Solving MILP Model... (This uses 4 Constraints)"):
        
        # 4. THE SOLVER ENGINE (MILP)
        
        model = pulp.LpProblem("MNUC_Scheduler", pulp.LpMinimize)
        x = {}

        # 4.1 Create Variables
        for idx, event in df_events.iterrows():
            e_id = event['EventID']
            # Sanitize e_id for solver (remove spaces/colons)
            e_id_clean = e_id.replace(" ", "_").replace(":", "")
            size = event['Size']
            
            for r, cap in rooms.items():
                if cap >= size: # Variable Constraint: Capacity
                    for d in days:
                        for s in slots:
                            # Use clean ID for the variable name
                            x[(e_id, r, d, s)] = pulp.LpVariable(f"x_{e_id_clean}_{r}_{d}_{s}", 0, 1, pulp.LpBinary)

        # 4.2 Constraints
        
        # C1: Once per week
        for e_id in df_events['EventID']:
            possible = [x[(e_id, r, d, s)] for r in rooms for d in days for s in slots if (e_id, r, d, s) in x]
            model += pulp.lpSum(possible) == 1, f"Once_{e_id.replace(' ','_').replace(':','')}"

        # C2: Room Conflict
        for r in rooms:
            for d in days:
                for s in slots:
                    room_usage = [x[(e_id, r, d, s)] for e_id in df_events['EventID'] if (e_id, r, d, s) in x]
                    model += pulp.lpSum(room_usage) <= 1, f"Room_{r}_{d}_{s}"

        # C3: Lecturer Availability
        for l in lecturers:
            prof_events = df_events[df_events['Lecturer'] == l]['EventID']
            for d in days:
                for s in slots:
                    prof_vars = [x[(e_id, r, d, s)] for e_id in prof_events for r in rooms if (e_id, r, d, s) in x]
                    model += pulp.lpSum(prof_vars) <= 1, f"Lec_{l.replace(' ','_').replace('.','')}_{d}_{s}"
        
        # C4: Student Group Conflict
        groups = df_events['Group'].unique()
        for g in groups:
            g_events = df_events[df_events['Group'] == g]['EventID']
            for d in days:
                for s in slots:
                    g_vars = [x[(e_id, r, d, s)] for e_id in g_events for r in rooms if (e_id, r, d, s) in x]
                    model += pulp.lpSum(g_vars) <= 1, f"Group_{g.replace(' ','_')}_{d}_{s}"

        # Solve
        status = model.solve()
        
        if pulp.LpStatus[status] == 'Optimal':
            st.sidebar.success("Optimization Successful!")
            
            # Extract Results
            results = []
            for key, var in x.items():
                if pulp.value(var) == 1:
                    (e_id, r, d, s) = key
                    details = df_events[df_events['EventID'] == e_id].iloc[0]
                    # Map Day to Date-like string for Gantt (using a dummy week)
                    day_map = {'Mon': '2023-01-02', 'Tue': '2023-01-03', 'Wed': '2023-01-04', 'Thu': '2023-01-05', 'Fri': '2023-01-06'}
                    
                    results.append({
                        'Day': d,
                        'Slot': s,
                        'Start': f"{day_map[d]} {time_map[s]['start']}",
                        'End': f"{day_map[d]} {time_map[s]['end']}",
                        'Course': details['Course'],
                        'Group': details['Group'],
                        'Room': r,
                        'Lecturer': details['Lecturer'],
                        'Department': details['Dept'],
                        'Size': details['Size']
                    })
            
            st.session_state['results'] = pd.DataFrame(results)
        else:
            st.error("Infeasible! Could not find a schedule constraints.")


# 5. VISUALIZATION DASHBOARD
if 'results' in st.session_state:
    df_res = st.session_state['results']
    
    # --- TABS ---
    tab1, tab2, tab3 = st.tabs(["Master Schedule", "Room Analytics", "Lecturer Load"])
    
    # --- TAB 1: VISUAL TIMETABLE ---
    with tab1:
        st.subheader("Visual Timetable")
        
        # Filter Options
        filter_type = st.radio("View By:", ["Room", "Student Group", "Lecturer"], horizontal=True)
        
        if filter_type == "Room":
            selected_item = st.selectbox("Select Room", sorted(rooms.keys()))
            filtered_df = df_res[df_res['Room'] == selected_item]
            color_by = 'Course'
        elif filter_type == "Student Group":
            selected_item = st.selectbox("Select Group", sorted(df_events['Group'].unique()))
            filtered_df = df_res[df_res['Group'] == selected_item]
            color_by = 'Room'
        else:
            selected_item = st.selectbox("Select Lecturer", sorted(lecturers))
            filtered_df = df_res[df_res['Lecturer'] == selected_item]
            color_by = 'Room'

        if not filtered_df.empty:
            # GANTT CHART
            fig = px.timeline(
                filtered_df, 
                x_start="Start", 
                x_end="End", 
                y="Day", 
                color=color_by,
                hover_data=["Course", "Room", "Lecturer", "Slot"],
                title=f"Schedule for {selected_item}"
            )
            # Fix Axis to show Time only
            fig.layout.xaxis.type = 'date'
            fig.update_xaxes(tickformat="%H:%M")
            fig.update_yaxes(categoryorder='array', categoryarray=['Fri', 'Thu', 'Wed', 'Tue', 'Mon']) # Monday at top
            st.plotly_chart(fig, use_container_width=True)
            
            # Simple Table
            # FIXED LINE BELOW: Sort First, Then Select Columns
            st.dataframe(
                filtered_df.sort_values(by=['Day', 'Start'])[['Day', 'Slot', 'Course', 'Room', 'Lecturer']]
            )
        else:
            st.info("No classes scheduled for this selection.")

    # --- TAB 2: ROOM ANALYTICS ---
    with tab2:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Room Utilization (Count)")
            room_counts = df_res['Room'].value_counts().reset_index()
            room_counts.columns = ['Room', 'Classes Scheduled']
            fig_room = px.bar(room_counts, x='Room', y='Classes Scheduled', color='Classes Scheduled', color_continuous_scale='Viridis')
            st.plotly_chart(fig_room, use_container_width=True)

        with col2:
            st.markdown("### Capacity Efficiency")
            # Calculate Average Efficiency (Class Size / Room Cap)
            efficiency_data = []
            for r in rooms:
                classes_in_room = df_res[df_res['Room'] == r]
                if not classes_in_room.empty:
                    avg_eff = (classes_in_room['Size'].mean() / rooms[r]) * 100
                    efficiency_data.append({'Room': r, 'Efficiency %': avg_eff})
            
            df_eff = pd.DataFrame(efficiency_data)
            fig_eff = px.pie(df_eff, values='Efficiency %', names='Room', title='Avg Seat Occupancy %')
            st.plotly_chart(fig_eff, use_container_width=True)

    # --- TAB 3: LECTURER LOAD ---
    with tab3:
        st.markdown("### Lecturer Workload")
        lec_counts = df_res['Lecturer'].value_counts().reset_index()
        lec_counts.columns = ['Lecturer', 'Classes Taught']
        
        fig_lec = px.bar(lec_counts, y='Lecturer', x='Classes Taught', orientation='h', color='Classes Taught')
        st.plotly_chart(fig_lec, use_container_width=True)
        
        st.dataframe(df_res.groupby(['Lecturer', 'Department']).size().reset_index(name='Total Classes'))

else:
    st.info("Click 'Run Optimization' in the sidebar to generate the schedule!")
    
    # Show input data preview
    st.subheader("Current Dataset Preview")
    st.dataframe(df_events)