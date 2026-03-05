from flask import Flask, render_template, request, redirect, session, Response
import sqlite3
from datetime import date

app = Flask(__name__)
app.secret_key = "attendance_secret"

# ---------------- DATABASE CONNECTION ----------------
def db():
    conn = sqlite3.connect("attendance.db")
    conn.row_factory = sqlite3.Row
    return conn

# ---------------- DATABASE SETUP ----------------
conn = db()
cur = conn.cursor()

# USERS
cur.execute("""
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT,
    role TEXT
)
""")

# STUDENTS
cur.execute("""
CREATE TABLE IF NOT EXISTS students(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    roll TEXT UNIQUE,
    name TEXT,
    parent_phone TEXT
)
""")

# ATTENDANCE
cur.execute("""
CREATE TABLE IF NOT EXISTS attendance(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    roll TEXT,
    date TEXT,
    status TEXT
)
""")

# LEAVES
cur.execute("""
CREATE TABLE IF NOT EXISTS leaves(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    roll TEXT,
    leave_type TEXT,
    from_date TEXT,
    to_date TEXT,
    reason TEXT,
    status TEXT
)
""")

# SUBJECTS
cur.execute("""
CREATE TABLE IF NOT EXISTS subjects(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_code TEXT,
    subject_name TEXT,
    teacher TEXT
)
""")

# SUBJECT ATTENDANCE
cur.execute("""
CREATE TABLE IF NOT EXISTS subject_attendance(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    roll TEXT,
    subject_code TEXT,
    date TEXT,
    status TEXT
)
""")

conn.commit()
conn.close()

# ---------------- LOGIN ----------------
@app.route("/", methods=["GET","POST"])
def login():

    msg=""
    if request.method=="POST":
        username=request.form["username"]
        password=request.form["password"]

        conn=db()
        cur=conn.cursor()
        cur.execute("SELECT role FROM users WHERE username=? AND password=?",(username,password))
        user=cur.fetchone()
        conn.close()

        if user:
            session["user"]=username
            session["role"]=user["role"]

            if user["role"]=="student":
                return redirect("/student")
            else:
                return redirect("/teacher")
        else:
            msg="Invalid Username or Password"

    return render_template("login.html",msg=msg)

# ---------------- STUDENT DASHBOARD ----------------
@app.route("/student")
def student():

    if "user" not in session or session["role"]!="student":
        return redirect("/")

    roll=session["user"]

    conn=db()
    cur=conn.cursor()

    cur.execute("SELECT name FROM students WHERE roll=?",(roll,))
    row=cur.fetchone()
    name=row["name"] if row else "Student"

    cur.execute("SELECT COUNT(*) FROM subject_attendance WHERE roll=?",(roll,))
    total=cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM subject_attendance WHERE roll=? AND status='Present'",(roll,))
    present=cur.fetchone()[0]

    absent=total-present
    percent=int((present/total)*100) if total>0 else 0
    status="Good" if percent>=75 else "Warning" if percent>=50 else "Low"

    conn.close()

    return render_template("student_dashboard.html",
                           roll=roll,
                           name=name,
                           total=total,
                           present=present,
                           absent=absent,
                           percent=percent,
                           status=status)

# ---------------- STUDENT ANALYTICS ----------------
@app.route("/student-analytics")
def student_analytics():

    if "user" not in session or session["role"]!="student":
        return redirect("/")

    roll=session["user"]
    conn=db()
    cur=conn.cursor()

    cur.execute("SELECT COUNT(*) FROM subject_attendance WHERE roll=?",(roll,))
    total=cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM subject_attendance WHERE roll=? AND status='Present'",(roll,))
    present=cur.fetchone()[0]

    absent=total-present
    percent=int((present/total)*100) if total>0 else 0

    # Monthly
    cur.execute("""
        SELECT substr(date,1,7),
               COUNT(*),
               COALESCE(SUM(CASE WHEN status='Present' THEN 1 ELSE 0 END),0)
        FROM subject_attendance
        WHERE roll=?
        GROUP BY substr(date,1,7)
        ORDER BY substr(date,1,7)
    """,(roll,))

    data=cur.fetchall()

    months=[]
    monthly_percent=[]

    for r in data:
        m=r[0]
        t=r[1]
        p=r[2]
        per=int((p/t)*100) if t>0 else 0
        months.append(m)
        monthly_percent.append(per)

    conn.close()

    return render_template("student_analytics.html",
                           total=total,
                           present=present,
                           absent=absent,
                           percent=percent,
                           months=months,
                           monthly_percent=monthly_percent)

# ---------------- TEACHER DASHBOARD ----------------
@app.route("/teacher",methods=["GET","POST"])
def teacher():

    if "user" not in session or session["role"]!="teacher":
        return redirect("/")

    selected_date=request.form.get("date") or request.args.get("date") or str(date.today())
    subject_code=request.form.get("subject") or request.args.get("subject")

    conn=db()
    conn.row_factory=sqlite3.Row
    cur=conn.cursor()

    # ---------- LOAD SUBJECTS ----------
    cur.execute("SELECT subject_code,subject_name FROM subjects")
    subjects=cur.fetchall()

    # leave counts
    cur.execute("SELECT COUNT(*) FROM leaves WHERE status='Pending'")
    pending=cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM leaves WHERE status='Approved'")
    approved=cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM leaves WHERE status='Rejected'")
    rejected=cur.fetchone()[0]

    cur.execute("SELECT * FROM leaves ORDER BY id DESC")
    leaves=cur.fetchall()

    students_today=[]

    # ---------- LOAD STUDENTS ONLY AFTER SUBJECT SELECT ----------
    if subject_code:
        cur.execute("""
        SELECT s.roll,s.name,
               COALESCE(sa.status,'Not Marked') as status
        FROM students s
        LEFT JOIN subject_attendance sa
        ON s.roll=sa.roll AND sa.date=? AND sa.subject_code=?
        ORDER BY s.roll
        """,(selected_date,subject_code))

        students_today=cur.fetchall()

    conn.close()

    return render_template("teacher_dashboard.html",
                           leaves=leaves,
                           pending=pending,
                           approved=approved,
                           rejected=rejected,
                           students_today=students_today,
                           selected_date=selected_date,
                           subjects=subjects,
                           subject_code=subject_code)
# ---------------- MARK ATTENDANCE ----------------
@app.route("/mark/<roll>/<status>/<att_date>")
def mark_attendance(roll,status,att_date):

    if "user" not in session or session["role"]!="teacher":
        return redirect("/")

    conn=db()
    cur=conn.cursor()

    cur.execute("SELECT id FROM attendance WHERE roll=? AND date=?",(roll,att_date))
    row=cur.fetchone()

    if row:
        cur.execute("UPDATE attendance SET status=? WHERE id=?",(status,row[0]))
    else:
        cur.execute("INSERT INTO attendance (roll,date,status) VALUES (?,?,?)",(roll,att_date,status))

    # SMS simulation
    if status=="Absent":
        cur.execute("SELECT name,parent_phone FROM students WHERE roll=?",(roll,))
        student=cur.fetchone()
        if student and student["parent_phone"]:
            print(f"SMS -> {student['parent_phone']}: {student['name']} was ABSENT on {att_date}")

    conn.commit()
    conn.close()

    return redirect(f"/teacher?date={att_date}")

# ---------------- BULK ATTENDANCE ----------------
@app.route("/save-attendance",methods=["POST"])
def save_attendance():

    if "user" not in session or session["role"]!="teacher":
        return redirect("/")

    selected_date=request.form["date"]

    conn=db()
    cur=conn.cursor()

    cur.execute("SELECT roll FROM students")
    students=cur.fetchall()

    for s in students:
        roll=s["roll"]
        status="Present" if roll in request.form else "Absent"

        cur.execute("SELECT id FROM attendance WHERE roll=? AND date=?",(roll,selected_date))
        row=cur.fetchone()

        if row:
            cur.execute("UPDATE attendance SET status=? WHERE id=?",(status,row[0]))
        else:
            cur.execute("INSERT INTO attendance (roll,date,status) VALUES (?,?,?)",(roll,selected_date,status))

    conn.commit()
    conn.close()

    return redirect(f"/teacher?date={selected_date}")

# ---------------- APPLY LEAVE ----------------
@app.route("/leave",methods=["GET","POST"])
def leave():

    if "user" not in session or session["role"]!="student":
        return redirect("/")

    roll=session["user"]
    conn=db()
    cur=conn.cursor()

    if request.method=="POST":
        cur.execute("""
        INSERT INTO leaves(roll,leave_type,from_date,to_date,reason,status)
        VALUES(?,?,?,?,?,'Pending')
        """,(roll,
             request.form["leave_type"],
             request.form["from_date"],
             request.form["to_date"],
             request.form["reason"]))
        conn.commit()

    cur.execute("SELECT * FROM leaves WHERE roll=? ORDER BY id DESC",(roll,))
    history=cur.fetchall()
    conn.close()

    return render_template("leave.html",history=history,roll=roll)  
# ---------------- EXPORT CSV ----------------
@app.route("/export-attendance")
def export_attendance():

    if "user" not in session or session["role"]!="teacher":
        return redirect("/")

    conn=db()
    cur=conn.cursor()

    cur.execute("""
    SELECT s.roll,s.name,a.date,a.status
    FROM students s
    LEFT JOIN attendance a ON s.roll=a.roll
    ORDER BY s.roll,a.date
    """)
    rows=cur.fetchall()
    conn.close()

    def generate():
        yield "Roll,Name,Date,Status\n"
        for r in rows:
            yield f"{r[0]},{r[1]},{r[2]},{r[3]}\n"

    return Response(generate(),
                    mimetype="text/csv",
                    headers={"Content-Disposition":"attachment;filename=attendance.csv"})

# ---------------- CHANGE PASSWORD ----------------
@app.route("/change-password",methods=["GET","POST"])
def change_password():

    if "user" not in session or session["role"]!="student":
        return redirect("/")

    msg=""
    roll=session["user"]

    if request.method=="POST":
        old=request.form["old_password"]
        new=request.form["new_password"]
        confirm=request.form["confirm_password"]

        conn=db()
        cur=conn.cursor()

        cur.execute("SELECT * FROM users WHERE username=? AND password=?",(roll,old))
        user=cur.fetchone()

        if not user:
            msg="Old password incorrect"
        elif new!=confirm:
            msg="Passwords do not match"
        elif len(new)<4:
            msg="Password must be 4 characters"
        else:
            cur.execute("UPDATE users SET password=? WHERE username=?",(new,roll))
            conn.commit()
            msg="Password changed successfully"

        conn.close()

    return render_template("change_password.html",msg=msg)
# ---------------- SAVE SUBJECT ROUTE ----------------
@app.route("/save-subject-attendance",methods=["POST"])
def save_subject_attendance():

    if "user" not in session or session["role"]!="teacher":
        return redirect("/")

    selected_date=request.form["date"]
    subject_code=request.form["subject"]

    conn=db()
    cur=conn.cursor()

    # get all students
    cur.execute("SELECT roll FROM students")
    students=cur.fetchall()

    for s in students:
        roll=s[0]

        # checked = Present
        if roll in request.form:
            status="Present"
        else:
            status="Absent"

        # check existing
        cur.execute("""
        SELECT id FROM subject_attendance
        WHERE roll=? AND date=? AND subject_code=?
        """,(roll,selected_date,subject_code))

        row=cur.fetchone()

        if row:
            cur.execute("""
            UPDATE subject_attendance
            SET status=?
            WHERE id=?
            """,(status,row[0]))
        else:
            cur.execute("""
            INSERT INTO subject_attendance
            (roll,subject_code,date,status)
            VALUES(?,?,?,?)
            """,(roll,subject_code,selected_date,status))

    conn.commit()
    conn.close()

    return redirect(f"/teacher?date={selected_date}&subject={subject_code}")

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------------- RUN ----------------
if __name__=="__main__":
    app.run(debug=True)