import pandas as pd
import random

# --- CONFIGURATION ---
TOTAL_UNITS = 144
MAX_LOAD = 6  # Global max (Full-Time limit)

# 1. LECTURER LIST (48 identified from MNUC Document)
lecturers = [
    "Dr. Abraham Matheka", "Dr. Catherine Mukunga", "Dr. Collins Oduor", "Dr. David Kaimenyi",
    "Dr. Elijah Maseno", "Dr. Ephantus Mwangi", "Dr. Jimrise Ochwach", "Dr. Joab Onyango",
    "Dr. John Achola", "Dr. John Kung'u", "Dr. Julius Murumba", "Dr. Keziah Gakahu",
    "Dr. Peter Muiruri", "Dr. Peter Murage", "Dr. Peter Mwangi", "Dr. Roy Kiogora",
    "Dr. Ruth Wambua", "Dr. Simon Ndicu", "Dr. Victor Aliata", "Mr. Boniface Mwangi",
    "Mr. Dan Ojwang", "Mr. Evariste Ntaho", "Mr. Gogo Otieno Kevin", "Mr. Gordon Agutu",
    "Mr. Harun Kamau", "Mr. Jackson Kamiri", "Mr. John Kinyanjui", "Mr. Joshua Mueke",
    "Mr. Patrick Berengu", "Ms. Dorothy Kathambi", "Ms. Esther Wambui", "Ms. Norah Njoki",
    "Prof. Winfred Mutuku", "Dr. Albert Kariuki", "Dr. Ann Rintari", "Dr Benjamin Kinyili",
    "Dr. Dancan Shiradula", "Dr. Jane Gachambi", "Dr. John Gitau", "Dr. Kipkosigei Bitok",
    "Dr. Leonora Lutiali", "Dr. Michael Murimi", "Dr. Paul Mwangi", "Dr. Sylivia Mukenyia",
    "Dr. Vincent Maranga", "Ms. Ann Adoyo", "Ms. Mary Wanjau", "Ms. Purity Mureithi"
]

# 2. GENERATE 144 UNITS
prefixes = ['SCO', 'SMA', 'SIT', 'HTM', 'SST', 'UCU', 'ECD', 'HSC']
units = []
for i in range(1, TOTAL_UNITS + 1):
    prefix = random.choice(prefixes)
    code = f"{prefix} {100 + i}"
    title = f"Unit {i} {prefix} Topic"
    # Mix of Student Groups
    group = random.choice(['BSc CS Y1', 'BSc CS Y2', 'BSc CS Y3', 'BSc CS Y4',
                           'BIT Y1', 'BIT Y2', 'BIT Y3', 'BIT Y4',
                           'BSc Math Y1', 'BSc Math Y2', 'BSc Hosp Y1', 'BSc Env Y1'])
    units.append({'Code': code, 'Title': title, 'Group': group})

# 3. ASSIGN UNITS TO LECTURERS
assignments = []
lec_counts = {lec: 0 for lec in lecturers}

# Shuffle units to ensure random distribution
random.shuffle(units)

for unit in units:
    # Filter lecturers who have not hit the max load of 6
    eligible = [l for l in lecturers if lec_counts[l] < MAX_LOAD]
    
    if not eligible:
        # Fallback (should not be reached with 144 units / 48 lecs = 3 avg)
        eligible = lecturers
        
    lecturer = random.choice(eligible)
    lec_counts[lecturer] += 1
    
    # Determine Status (Logic: <=2 is PT, >2 is FT)
    status = "Full-Time" if lec_counts[lecturer] > 2 else "Part-Time"
    
    # A. Physical Class (2 Hours)
    assignments.append({
        'EventID': f"{unit['Code']}_Phys",
        'CourseCode': unit['Code'],
        'CourseTitle': unit['Title'],
        'Group': unit['Group'],
        'Lecturer': lecturer,
        'LecturerStatus': status,
        'Size': random.choice([50, 60, 80, 100]),
        'Dept': 'SPAS',
        'SessionType': 'Physical',
        'Duration': 2
    })
    
    # B. Online Class (1 Hour)
    assignments.append({
        'EventID': f"{unit['Code']}_Onl",
        'CourseCode': unit['Code'],
        'CourseTitle': unit['Title'],
        'Group': unit['Group'],
        'Lecturer': lecturer,
        'LecturerStatus': status,
        'Size': 1000, # Unlimited capacity
        'Dept': 'SPAS',
        'SessionType': 'Online',
        'Duration': 1
    })

# Export
df = pd.DataFrame(assignments)
df.to_csv('mnuc_large_dataset.csv', index=False)
print(f"✅ Generated {len(df)} events (Physical & Online) for {TOTAL_UNITS} units.")