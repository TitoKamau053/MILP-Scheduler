import streamlit as st
import pulp
import pandas as pd
import plotly.express as px

# 1. PAGE CONFIGURATION
st.set_page_config(
    page_title="MNUC Scheduler", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Professional, Minimal CSS (Updated to be Dark Mode Compatible)
st.markdown("""
    <style>
    /* Remove white background constraint */
    .reportview-container { background: transparent; }
    .main .block-container { padding-top: 1rem; }
    
    /* Button Styling */
    .stButton>button {
        width: 100%; border-radius: 6px; height: 2.5em;
        background-color: #f0f2f6; color: #31333F; border: 1px solid #d6d6d8;
    }
    .stButton>button:hover {
        border-color: #0068c9; color: #0068c9; background-color: #ffffff;
    }
    
    /* Ensure text is readable in both modes */
    div[data-testid="stMetricValue"] { font-size: 1.8rem; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_data():
    rooms = {
        'Theatre Main': 300, 'Theatre Annex': 250,
        'Hall East': 150, 'Hall West': 150,
        'Lab CS1': 80, 'Lab CS2': 80, 'Lab Physics': 80,
        'Room A1': 60, 'Room A2': 60, 'Room B1': 60, 'Room B2': 60,
        'Room C1': 50, 'Room C2': 50, 'ONLINE': 9999
    }
    
    # Time Slots: 07:00 to 17:00 (Hours 7 to 16)
    hours = list(range(7, 17)) 
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']
    
    try:
        df = pd.read_csv("mnuc_large_dataset.csv")
    except FileNotFoundError:
        st.error("Dataset 'mnuc_large_dataset.csv' not found. Please run the generation script first.")
        st.stop()
        
    return rooms, days, hours, df

rooms_db, days_db, hours_db, df_events = load_data()

# --- SIDEBAR ---
st.sidebar.title("Configuration")
st.sidebar.caption("School of Pure & Applied Sciences")
st.sidebar.markdown("---")
st.sidebar.metric("Total Sessions", len(df_events))

if st.sidebar.button("Generate Schedule"):
    with st.spinner("Optimizing constraints..."):
        model = pulp.LpProblem("MNUC_Scheduler", pulp.LpMinimize)
        
        # 1. SETUP
        valid_starts = {}
        for idx, row in df_events.iterrows():
            eid = row['EventID']
            dur = row['Duration']
            is_online = (row['SessionType'] == 'Online')
            
            valid_starts[eid] = []
            eligible_rooms = ['ONLINE'] if is_online else [r for r in rooms_db if r != 'ONLINE' and rooms_db[r] >= row['Size']]
            
            for r in eligible_rooms:
                for d in days_db:
                    for h in [t for t in hours_db if t + dur <= 17]:
                        valid_starts[eid].append((r, d, h))
        
        # Variables
        x = pulp.LpVariable.dicts("x", ((e, r, d, h) for e in valid_starts for (r, d, h) in valid_starts[e]), cat='Binary')
        
        # 2. CONSTRAINTS
        # C1: Assign Once
        for eid in df_events['EventID']:
            if eid in valid_starts:
                model += pulp.lpSum(x[(eid, r, d, h)] for (r, d, h) in valid_starts[eid]) == 1
        
        # C2: Room Capacity
        for r in rooms_db:
            if r == 'ONLINE': continue
            for d in days_db:
                for t in hours_db:
                    active = []
                    for eid, row in df_events.iterrows():
                        if row['SessionType'] == 'Online': continue
                        dur = row['Duration']
                        if eid in valid_starts:
                            for (rv, dv, hv) in valid_starts[eid]:
                                if rv == r and dv == d and (t - dur + 1 <= hv <= t):
                                    active.append(x[(eid, rv, dv, hv)])
                    if active: model += pulp.lpSum(active) <= 1

        # C3: Lecturer Overlap
        for lec in df_events['Lecturer'].unique():
            lec_events = df_events[df_events['Lecturer'] == lec]
            for d in days_db:
                for t in hours_db:
                    active = []
                    for _, row in lec_events.iterrows():
                        eid = row['EventID']
                        dur = row['Duration']
                        if eid in valid_starts:
                            for (rv, dv, hv) in valid_starts[eid]:
                                if dv == d and (t - dur + 1 <= hv <= t):
                                    active.append(x[(eid, rv, dv, hv)])
                    if active: model += pulp.lpSum(active) <= 1

        # 3. SOLVE
        if model.solve():
            st.success("Optimization Complete")
            results = []
            base_dates = {'Mon':'2026-01-01', 'Tue':'2026-01-02', 'Wed':'2026-01-03', 'Thu':'2026-01-04', 'Fri':'2026-01-05'}
            
            for e in valid_starts:
                for (r, d, h) in valid_starts[e]:
                    if pulp.value(x[(e, r, d, h)]) == 1:
                        row = df_events[df_events['EventID'] == e].iloc[0]
                        start_time = f"{h:02d}:00"
                        end_time = f"{h+row['Duration']:02d}:00"
                        results.append({
                            'Day': d,
                            'Time Interval': f"{start_time} - {end_time}",
                            'Unit': row['CourseCode'],
                            'Title': row['CourseTitle'],
                            'Type': row['SessionType'],
                            'Room': r,
                            'Lecturer': row['Lecturer'],
                            'Group': row['Group'],
                            'Start_Hidden': f"{base_dates[d]} {start_time}", 
                            'End_Hidden': f"{base_dates[d]} {end_time}"
                        })
            
            df_res = pd.DataFrame(results)
            st.session_state['schedule_data'] = df_res
        else:
            st.error("Infeasible. Constraints too tight.")

# --- MAIN DASHBOARD ---
if 'schedule_data' in st.session_state:
    df_out = st.session_state['schedule_data']
    
    # METRICS
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Classes", len(df_out))
    c2.metric("Physical", len(df_out[df_out['Type']=='Physical']))
    c3.metric("Online", len(df_out[df_out['Type']=='Online']))
    c4.metric("Venue Utilized", df_out['Room'].nunique())

    # TABS
    tab1, tab2 = st.tabs(["Timeline View", "Table View"])
    
    with tab1:
        st.markdown("### Interactive Schedule")
        
        # CONTROLS
        c_view, c_day = st.columns([1, 1])
        with c_view:
            view_mode = st.selectbox("Group Rows By:", ["Room", "Lecturer", "Group"])
        with c_day:
            day_filter = st.selectbox("Filter Day:", ["Mon", "Tue", "Wed", "Thu", "Fri"])

        # DATA FILTERING
        plot_df = df_out.copy()
        if day_filter != "All Days":
            plot_df = plot_df[plot_df['Day'] == day_filter]

        # DYNAMIC HEIGHT
        n_rows = plot_df[view_mode].nunique()
        chart_height = max(500, n_rows * 40)

        # GANTT CHART
        fig = px.timeline(
            plot_df, 
            x_start="Start_Hidden", 
            x_end="End_Hidden", 
            y=view_mode,             
            color="Day",             
            text="Unit",
            hover_data=["Title", "Time Interval", "Room", "Group"],
            height=chart_height,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        
        # CLEAN LAYOUT (Updated to remove white background force)
        fig.update_xaxes(tickformat="%H:%M", title="Time (07:00 - 17:00)", side="top")
        fig.update_yaxes(autorange="reversed", title=None)
        
        # REMOVED: plot_bgcolor='white', showgrid=True settings
        # This allows Plotly to inherit the Streamlit theme (Dark/Light)
        fig.update_layout(
            margin=dict(l=10, r=10, t=50, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        st.plotly_chart(fig, width="stretch")
        
    with tab2:
        st.dataframe(
            df_out[['Day', 'Time Interval', 'Unit', 'Title', 'Room', 'Lecturer', 'Group']].sort_values(['Day', 'Time Interval']),
            hide_index=True,
            width="stretch"
        )

else:
    st.info("Click 'Generate Schedule' in the sidebar to start.")