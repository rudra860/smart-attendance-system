import sqlite3

students = [
("230301130001","Adyasha Sahoo"),
("230301130002","Satyabrata Sahoo"),
("230301130003","Biswajit Pattanaik"),
("230301130004","Ashish Kumar"),
("230301130005","Subham Narayana Martha"),
("230301130006","Priyansu Pritam Khatei"),
("230301130007","Ajoy Kumar Tiwari"),
("230301130008","Mausam Mohanta"),
("230301130010","Rudra Narayan Moharana"),
("230301130011","Prachi Priyadarsini Kar"),
("230301130012","Ashribad Sarangi"),
("230301130013","Iseeta Saumyardarshini"),
("230301130014","Devendran Mudlier"),
("230301130015","Vaibhav Kumar Patro"),
("230301130016","Deepti Mayee Panda"),
("230301130017","Bhabani Sankar Dash"),
("230301130018","Subhashree Sahoo"),
("230301130021","Soumya Ranjan Dash"),
("230301130022","Biswajit Patra"),
("230301130023","Bikash Kumar Swain"),
("230301130024","Subhransu Patra"),
("230301130025","E Rudra Narayana Patro"),
("230301130026","Hitesh Raj Garada"),
("230301131027","Kaibalya Mohanty"),
("230301131028","Rohit Jambhulkar"),
("230301132029","Itimayee Mohapatra"),
("230301132030","Rudransh Jena"),
("230301120110","Bishnu Prasad Debata"),
("230301120371","Prince Kushwaha"),
("230301120481","Puja Mohanty"),
("230301120186","Shyamant Kumar")
]

conn = sqlite3.connect("attendance.db")
cur = conn.cursor()

# 🔴 CLEAN OLD DATA (IMPORTANT)
cur.execute("DELETE FROM users")
cur.execute("DELETE FROM students")
cur.execute("DELETE FROM leaves")
cur.execute("DELETE FROM attendance")

# 🔵 INSERT STUDENTS
for reg, name in students:
    cur.execute(
        "INSERT INTO users (username,password,role) VALUES (?,?,?)",
        (reg, "123", "student")
    )
    cur.execute(
        "INSERT INTO students (roll,name) VALUES (?,?)",
        (reg, name)
    )

# 🔵 INSERT TEACHER (ONLY ONCE)
cur.execute(
    "INSERT INTO users (username,password,role) VALUES (?,?,?)",
    ("teacher", "123", "teacher")
)

conn.commit()
conn.close()

print("✅ DATABASE SETUP COMPLETE – NO DUPLICATES")