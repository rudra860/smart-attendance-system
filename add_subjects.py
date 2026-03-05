import sqlite3

subjects = [
("CUTM1016","JOB READINESS","teacher"),
("CUES2053","PROJECT","teacher"),
("CUTM1603","DATA STRUCTURES","teacher"),
("CUTM3037","E-VEHICLE ASSEMBLY AND SERVICE TECHNOLOGY","teacher"),
("CUTM1049","ANTENNA DESIGN AND ANALYSIS","teacher"),
("CUTM1043","NETWORK ANALYSIS","teacher"),
("CUTM1021","DESIGN THINKING","teacher"),
("CUTM1020","ROBOTIC AUTOMATION WITH ROS AND C++","teacher")
]

conn = sqlite3.connect("attendance.db")
cur = conn.cursor()

for s in subjects:
    cur.execute(
        "INSERT INTO subjects(subject_code,subject_name,teacher) VALUES(?,?,?)",
        s
    )

conn.commit()
conn.close()

print("✅ Subjects Added Successfully")