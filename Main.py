import pandas as pd
import mysql.connector as sqlconn
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import hashlib

DB_CONFIG = {
    'host': 'localhost',
    'database': 'student',
    'user': 'root',
    'password': '*GodUssoopp123'
}

def get_connection():
    return sqlconn.connect(
        host=DB_CONFIG["host"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        database=DB_CONFIG["database"],
        port=DB_CONFIG.get("port", 3306)
    )

try:
    DB = get_connection()
    CUR = DB.cursor()
    print("Connected to database.")
except Exception as e:
    print("DB connection failed:", e)
    DB, CUR = None, None

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()    

def init_tables():
    CUR.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL
        )
    """)

    CUR.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INT PRIMARY KEY,
            sname VARCHAR(50),
            sclass VARCHAR(10),
            gender VARCHAR(10),
            house VARCHAR(20),
            attendance FLOAT
        )

    """)
    CUR.execute("""
        CREATE TABLE IF NOT EXISTS subjects (
            subject_id INT AUTO_INCREMENT PRIMARY KEY,
            subject_name VARCHAR(30)
        )
    """)

    CUR.execute("""
        CREATE TABLE IF NOT EXISTS exams (
            exam_id INT AUTO_INCREMENT PRIMARY KEY,
            exam_name VARCHAR(30),
            max_written FLOAT,
            max_practical FLOAT
        )
    """)

    CUR.execute("""
        CREATE TABLE IF NOT EXISTS marks (
            id INT,
            subject_id INT,
            exam_id INT,
            written FLOAT,
            practical FLOAT,
            total FLOAT,
            PRIMARY KEY (id, subject_id, exam_id),
            FOREIGN KEY (id) REFERENCES students(id) ON DELETE CASCADE,
            FOREIGN KEY (subject_id) REFERENCES subjects(subject_id) ON DELETE CASCADE,
            FOREIGN KEY (exam_id) REFERENCES exams(exam_id) ON DELETE CASCADE
        )
    """)

    DB.commit() 

init_tables()

def add_teacher(username, password):
    try:
        sql = "INSERT INTO users (username,password_hash) VALUES (%s,%s)"
        CUR.execute(sql, (username, hash_password(password)))
        DB.commit()
        print("Teacher added.")
    except:
        print("Username already exists.")

def login():
    CUR.execute("SELECT COUNT(*) FROM users")
    count = CUR.fetchone()[0]
    if count == 0:
        print("No teachers found. Creating first teacher.")
        username = input("Choose a username: ").strip()
        password = input("Choose a password: ").strip()
        add_teacher(username, password)
        print("First teacher created.")

    username = input("Username: ").strip()

    CUR.execute("SELECT password_hash FROM users WHERE username=%s", (username,))
    user = CUR.fetchone()

    if not user:
        print("invalid Username.")
        return False
        
    for attempt in range(3):

        password = input("Password: ").strip()
               
        if hash_password(password) == user[0]:
            print(f"Welcome, {username}")
            return True
        else:
            print("\nIncorrect Password")

            print("\n 1. Retry Password.")
            print(" 2. Go back to access menu")

            inv= int(input("\nEnter choice:"))
            if inv == 1:
                continue
            if inv == 2:
                return False
            else:
                print("Invalid choice.Try again.")
                continue

    print("Too many failed attempts.")
    return False

def insert_student():
    try:
        i = int(input("Enter ID: "))
        nm = input("Enter Name: ").upper()
        cl = input("Enter Class (e.g. XII-A): ").upper()
        g = input("Enter Gender: ").upper()
        h = input("Enter House: ").upper()
        att = float(input("Enter Attendance %: "))
        if att < 0 or att > 100:
            print("Attendance must be between 0-100%")
            return
        CUR.execute("INSERT INTO students VALUES (%s,%s,%s,%s,%s,%s)", (i, nm, cl, g, h, att))
        DB.commit()
        print("Student inserted.")
        
    except Exception as existing:
        print("Student ID already exists:", existing)

def insert_subject():
    subj = input("Enter Subject Name: ").upper()
    CUR.execute("INSERT INTO subjects (subject_name) VALUES (%s)", (subj,))
    DB.commit()
    print("Subject inserted.")

def insert_exam():
    ename = input("Enter Exam Name: ").upper()
    mw = float(input("Enter Max Written Marks: "))
    mp = float(input("Enter Max Practical Marks: "))
    CUR.execute("INSERT INTO exams (exam_name,max_written,max_practical) VALUES (%s,%s,%s)", (ename, mw, mp))
    DB.commit()
    print("Exam inserted.")

def insert_marks():

    CUR.execute("SELECT id FROM students")
    students = [row[0] for row in CUR.fetchall()]
    print("\nStudent IDs present:", ", ".join(map(str,students)) if students else "None")
    
    CUR.execute("SELECT subject_name FROM subjects")
    subjects = [row[0] for row in CUR.fetchall()]
    print("\nAvailable Subjects:", ", ".join(subjects) if subjects else "None")
    
    CUR.execute("SELECT exam_name FROM exams")
    exams = [row[0] for row in CUR.fetchall()]
    print("Available Exams:", ", ".join(exams) if exams else "None")
    print()

    try:        
        sid = int(input("Enter Student ID: "))
        CUR.execute("SELECT id FROM students WHERE id=%s", (sid,))
        if not CUR.fetchone():
            print("student ID does not exist.")
            return

        subj_name = input("Enter Subject Name: ").strip().upper()

        CUR.execute("SELECT subject_id FROM subjects WHERE subject_name=%s", (subj_name,))
        subj = CUR.fetchone()
        if not subj:
            
            print("Subject not found.")
            return
        subj_id = subj[0]

        exam_name = input("Enter Exam Name: ").strip().upper()
        CUR.execute("SELECT exam_id,max_written,max_practical FROM exams WHERE exam_name=%s", (exam_name,))
        exam = CUR.fetchone()
        if not exam:
            print("Exam not found.")
            return
    
        exam_id, mw, mp = exam
        w = int(input(f"Enter Written Marks (out of {mw}): "))

        if w < 0 or w > mw:
            print("Marks must be within limit")
            return
        
        p = int(input(f"Enter Practical Marks (out of {mp}): "))
        if p < 0 or p > mp:
            print("Marks must be within limit")
            return
    
        total = w + p

        CUR.execute("INSERT INTO marks VALUES (%s,%s,%s,%s,%s,%s)", 
                (sid, subj_id, exam_id, w, p, total))
        DB.commit()
        print("Marks inserted.")
    except Exception as e:
        print("Error while inserting marks:", e)

def show_data():
    CUR.execute("SELECT * FROM students")
    rows = CUR.fetchall()
    df = pd.DataFrame(rows, columns=["ID","Name","Class","Gender","House","Attendance"])
    print(df)

def generate_pdf_report():
    from datetime import datetime
    import os

    os.makedirs("reports", exist_ok=True)

    pdf_path = f"reports/student_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

    CUR.execute("""
        SELECT s.id, s.sname, s.sclass, sub.subject_name, e.exam_name,
               m.written, m.practical, m.total
        FROM marks m
        JOIN students s ON s.id = m.id
        JOIN subjects sub ON sub.subject_id = m.subject_id
        JOIN exams e ON e.exam_id = m.exam_id
        ORDER BY s.id
    """)

    rows = CUR.fetchall()
    if not rows:
        print("No data found.")
        return

    df = pd.DataFrame(
        rows,
        columns=["ID", "Name", "Class", "Subject", "Exam", "Written", "Practical", "Total"]
    )

    with PdfPages(pdf_path) as pdf:
        for sid, group in df.groupby("ID"):
            fig, ax = plt.subplots(figsize=(8.27, 11.69))  
            ax.axis("off")

            
            ax.text(
                0.5, 0.96,
                "STUDENT ACADEMIC REPORT",
                ha="center",
                fontsize=18,
                fontweight="bold")

            student_class = group.iloc[0]["Class"] if group.iloc[0]["Class"] else "N/A"

        
            ax.text(
                0.05, 0.90,
                f"Student Name : {group.iloc[0]['Name']}\n"
                f"Student ID   : {sid}\n"
                f"Class        : {student_class}",
                fontsize=11,
                va="top")

          
            table_data = group[
                ["Subject", "Exam", "Written", "Practical", "Total"]].values.tolist()

            table = ax.table(
                cellText=table_data,
                colLabels=["Subject", "Exam", "Written", "Practical", "Total"],
                cellLoc="center",
                bbox=[0.03, 0.44, 0.94, 0.28])

            table.auto_set_font_size(False)
            table.set_fontsize(10)
            table.scale(1.05, 0.85)

            for (row, col), cell in table.get_celld().items():
                if row == 0:
                    cell.set_text_props(weight="bold", color="white")
                    cell.set_facecolor("#2C3E50")
                else:
                    cell.set_facecolor("#F2F2F2" if row % 2 == 0 else "white")

            total_marks = group["Total"].sum()
            ax.text(0.5, 0.34,
                f"Total Marks Obtained : {total_marks}",
                ha="center",
                fontsize=13,
                fontweight="bold",
                fontfamily="Times New Roman")
                
            ax.text(0.05, 0.20, "Guardian Signature: _______________", fontsize=10)
            ax.text(0.60, 0.20, "Principal Signature: _____________", fontsize=10)

            pdf.savefig(fig)
            plt.close(fig)

    print("Final PDF generated successfully:", pdf_path)



def search_sid():
    sid = input("Enter Student ID to search: ").strip()
    CUR.execute("SELECT * FROM students WHERE id=%s", (sid,))
    stud = CUR.fetchone()
    if stud:
        data = pd.DataFrame([stud], columns=["ID","Name","Class","Gender","House","Attendance"])
        print("\nStudent Found:\n")
        print(data)
    else:
        print("Student not found.")

def search_sname():

    name = input("Enter student name: ").strip().upper()
    CUR.execute("SELECT * FROM students WHERE sname LIKE %s", (f"%{name}%",))

    stud = CUR.fetchall()
    if stud:
        data = pd.DataFrame(stud, columns=["ID","Name","Class","Gender","House","Attendance"])
        print("\nMatch Found:\n")
        print(data)
    else:
        print("No matches Found.")

def search_sclass():
    cl = input("Enter Class: ").strip().upper()
    CUR.execute("SELECT * FROM students WHERE sclass=%s", (cl,))
    stud = CUR.fetchall()
    if stud:
           
            data = pd.DataFrame(stud, columns=["ID","Name","Class","Gender","House","Attendance"])

            print("\nStudents from", cl, "are:","\n")
            print(data)
    
    else:
        print("No students found in this class.")

def search_shouse():
    house = "%" + input("Enter House: ").strip().upper() + "%"
    CUR.execute("SELECT * FROM students WHERE house LIKE %s", (house,))
    stud = CUR.fetchall()
    if stud:
        data = pd.DataFrame(stud, columns=["ID","Name","Class","Gender","House","Attendance"])
        print("\nStudents Found:\n")
        print(data)
    else:
        print("No Students is this house.")

def search_sgender():
    gender = input("Enter Gender: ").strip().upper() 
    CUR.execute("SELECT * FROM students WHERE gender LIKE %s", (gender,))
    stud = CUR.fetchall()
    if stud:
        data = pd.DataFrame(stud, columns=["ID","Name","Class","Gender","House","Attendance"])
        print("\nStudents Found:\n")
        print(data)
    else:
        print("No Students Found")

def search_menu():
    while True:
        print("\n--- STUDENT SEARCH MENU ---")
        print("1. Search by ID")
        print("2. Search by Name")
        print("3. Search by Class")
        print("4. Search by House")
        print("5. Search by Gender")
        print("6. Main Menu")

        ch = input("Enter choice: ")

        if ch == "1": 
            search_sid()
        elif ch == "2": 
            search_sname()
        elif ch == "3": 
            search_sclass()
        elif ch == "4": 
            search_shouse()
        elif ch == "5": 
            search_sgender()
        elif ch == "6": 
            return
        
        else: 
            print("Invalid choice.")

def manage_menu():
    while True:
        print("\n--- RECORD MANAGEMENT MENU ---")
        print("1. Update Records")
        print("2. Delete Records")
        print("3. Main Menu")

        ch = input("Enter choice: ")

        if ch == "1": 
            update_menu()
        elif ch == "2": 
            delete_menu()
        elif ch == "3":
            return
        
        else:
            print("Invalid choice.")

def update_menu():
    while True:
        print("\n--- RECORD UPDATION MENU ---")
        print("1. Update Student")
        print("2. Update Subject")
        print("3. Update Marks")
        print("4. Update Exam")
        print("5. Main Menu")

        ch = int(input("Enter Choice:"))

        if ch == "1": 
            update_stud()
        elif ch == "2": 
            update_sub()
        elif ch == "3":
            update_marks()
        elif ch == "4": 
            update_exam()
        elif ch == "5":
            return
        else:
            print("Invalid choice.")

def update_stud():
    sid = input("Enter Student ID to update: ").strip()
    CUR.execute("SELECT * FROM students WHERE id=%s", (sid,))
    stud = CUR.fetchone()

    if not stud:
        print("Student not found.")
        return

    print("\nLeave field blank to keep existing value.\n")

    new_name = input(f"Name ({stud[1]}): ")
    new_name = new_name.upper() if new_name else stud[1]

    new_class = input(f"Class ({stud[2]}): ")
    new_gender = input(f"Gender ({stud[3]}): ")
    new_house = input(f"House ({stud[4]}): ")

    try:
        inp_att = input(f"Attendance ({stud[5]}): ")
        new_att = float(inp_att) if inp_att else stud[5]
        if new_att < 0 or new_att > 100:
            print("Attendance must be between 0–100%")
            return
    except:
        print("Invalid attendance.")
        return

    CUR.execute("""UPDATE students SET sname=%s, sclass=%s, gender=%s, house=%s, attendance=%s WHERE id=%s""", 
                (new_name, new_class, new_gender, new_house, new_att, sid))

    DB.commit()
    print("\nStudent updated successfully.")

def update_sub():

    CUR.execute("SELECT subject_id, subject_name FROM subjects")
    subj = CUR.fetchall()

    if not subj:
        print("No subjects available.")
        return

    print("\nAvailable Subjects:")
    for sid, name in subj:
        print(f"{sid}. {name}")

    try:
        sub_id = int(input("\nEnter Subject ID to update: "))
    except:
        print("Invalid input.")
        return

    CUR.execute("SELECT subject_name FROM subjects WHERE subject_id=%s", (sub_id,))
    valid = CUR.fetchone()

    if not valid:

        print("Subject not found.")
        return

    new_name = input(f"New Subject Name ({valid[0]}): ")

    CUR.execute("UPDATE subjects SET subject_name=%s WHERE subject_id=%s",
                (new_name, sub_id))
    DB.commit()

    print("Subject updated successfully.")

def update_marks():

    sid = input("Enter Student ID: ")

    CUR.execute("SELECT sname FROM students WHERE id=%s", (sid,))
    stud = CUR.fetchone()
    if not stud:
        print("Student not found.")
        return

    print(f"\nMarks to be updated for {stud[0]} (ID: {sid})")

    CUR.execute("""SELECT m.subject_id, sub.subject_name, m.exam_id, e.exam_name, m.written, m.practical 
        FROM marks m JOIN subjects sub ON sub.subject_id = m.subject_id JOIN exams e ON e.exam_id = m.exam_id WHERE m.id=%s""", (sid,))
    
    all_marks = CUR.fetchall()

    if not all_marks:
        print("No marks found for this student.")
        return

    print("\nAvailable Marks:")
    for sub_id, sub_name, exam_id, exam_name, w, p in all_marks:
        print(f"Subject: {sub_name}  Exam: {exam_name}  Written={w}  Practical={p}")

    sub = input("\nEnter Subject Name: ")

    CUR.execute("SELECT subject_id FROM subjects WHERE subject_name=%s", (sub,))
    data1 = CUR.fetchone()

    exam = input("Enter Exam Name: ")

    CUR.execute("SELECT exam_id, max_written, max_practical FROM exams WHERE exam_name=%s", (exam,))
    data2 = CUR.fetchone()

    if not data1 or not data2:
        print("Invalid subject or exam.")
        return

    subj_id = data1[0]
    exam_id, mw, mp = data2

    CUR.execute("SELECT written, practical FROM marks WHERE id=%s AND subject_id=%s AND exam_id=%s", (sid, subj_id, exam_id))

    mark = CUR.fetchone()
    if not mark:
        print("Marks not found.")
        return

    print(f"\nOld Written={mark[0]}, Old Practical={mark[1]}")

    try:
        new_w = input(f"New Written (out of {mw}): ").strip()
        new_w = float(new_w) if new_w else mark[0]

        new_p = input(f"New Practical (out of {mp}): ").strip()
        new_p = float(new_p) if new_p else mark[1]
    except:
        print("Invalid marks.")
        return

    total = new_w + new_p

    CUR.execute("""UPDATE marks SET written=%s, practical=%s, total=%s WHERE id=%s AND subject_id=%s AND exam_id=%s
    """, (new_w, new_p, total, sid, subj_id, exam_id))

    DB.commit()
    print("Marks updated successfully.")

def update_exam():

    CUR.execute("SELECT exam_id, exam_name, max_written, max_practical FROM exams")
    exams = CUR.fetchall()

    if not exams:
        print("No exams available.")
        return

    print("\nAvailable Exams:")
    for eid, name, mw, mp in exams:
        print(f"{eid}. {name} (Written: {mw}, Practical: {mp})")

    try:
        exam_id = int(input("\nEnter Exam ID to update: "))
    except:
        print("Invalid input.")
        return

    CUR.execute("SELECT exam_name, max_written, max_practical FROM exams WHERE exam_id=%s", (exam_id,))
    data = CUR.fetchone()

    if not data:
        print("Exam not found.")
        return
    
    old_name, old_mw, old_mp = data    


    new_name = input(f"Exam Name ({old_name}): ")
    try:
        new_mw = input(f"Max Written ({old_mw}): ")
        new_mw = float(new_mw) if new_mw else old_mw

        new_mp = input(f"Max Practical ({old_mp}): ")
        new_mp = float(new_mp) if new_mp else old_mp
    except:
        print("Invalid marks.")
        return

    CUR.execute("""UPDATE exams SET exam_name=%s, max_written=%s, max_practical=%s 
        WHERE exam_id=%s""", (new_name, new_mw, new_mp, exam_id))
    DB.commit()

    print("Exam updated successfully.")


def delete_menu():

    while True:
        print("\n--- RECORD DELETION MENU ---")
        print("1. Delete Student")
        print("2. Delete Subject")
        print("3. Delete Marks")
        print("4. Delete Exam")
        print("5. Main Menu")

        ch = int(input("Enter Choice:"))

        if ch == "1": 
            delete_stud()
        elif ch == "2": 
            delete_sub()
        elif ch == "3":
            delete_marks()
        elif ch == "4": 
            delete_exam()
        elif ch == "5":
            return
        else:
             print("Invalid choice.")

             
def delete_stud():
    
    sid = input("Enter Student ID to delete: ")
    CUR.execute("SELECT * FROM students WHERE id=%s", (sid,))
    stud = CUR.fetchone()

    if not stud:
        print("Student not found.")
        return

    print(f"\nAre you sure you wish to delete student {sid}?")  

    ch = input("Type YES to confirm: ").upper()
    if ch == "YES":
        CUR.execute("DELETE FROM students WHERE id=%s", (sid,))
        DB.commit()
        print("Student deleted successfully.")
    else:
        print("Deletion Cancelled") 

def delete_sub():

    CUR.execute("SELECT subject_id, subject_name FROM subjects")
    subs = CUR.fetchall()

    if not subs:
        print("No subjects have been assigned yet.")
        return

    print("\nAvailable Subjects:")
    for sid, name in subs:
        print(f"{sid}. {name}")

    try:
        sub_id = int(input("\nEnter Subject ID to delete: "))
    except:
        print("Invalid input.")
        return

    CUR.execute("SELECT * FROM subjects WHERE subject_id=%s", (sub_id,))
    exists = CUR.fetchone()

    if not exists:
        print("Subject not found.")
        return

    print("\nAre you sure that you wish to delete this subject?.")
    ch = input("Type YES to confirm: ").upper()

    if ch == "YES":
        CUR.execute("DELETE FROM subjects WHERE subject_id=%s", (sub_id,))
        DB.commit()
        print("Subject deleted.")
    else:
        print("Cancelled.")

def delete_marks():
    sid = input("Enter Student ID: ")
    
    CUR.execute("SELECT sname FROM students WHERE id=%s", (sid,))
    if not CUR.fetchone():
        print("Student not found.")
        return

    sub = input("Enter Subject Name: ").upper()

    CUR.execute("SELECT subject_id FROM subjects WHERE subject_name=%s", (sub,))
    data1 = CUR.fetchone()

    exam = input("Enter Exam Name: ").upper()
    
    CUR.execute("SELECT exam_id FROM exams WHERE exam_name=%s", (exam,))
    data2= CUR.fetchone()

    if not data1 or not data2:
        print("Invalid subject or exam.")
        return

    subj_id, exam_id = data1[0], data2[0]

    CUR.execute("SELECT * FROM marks WHERE id=%s AND subject_id=%s AND exam_id=%s", (sid, subj_id, exam_id))
    
    if not CUR.fetchone():
        print("Marks not found.")
        return

    confirm = input("Type YES to delete these marks: ").upper()
    if confirm == "YES":
        CUR.execute("DELETE FROM marks WHERE id=%s AND subject_id=%s AND exam_id=%s", (sid, subj_id, exam_id))
        DB.commit()
        print("Marks deleted.")
    else:
        print("Cancelled.")

def delete_exam():
    CUR.execute("SELECT exam_id, exam_name FROM exams")
    exams = CUR.fetchall()

    if not exams:
        print("No exam conducted.")
        return

    print("\nAvailable Exams:")
    for eid, name in exams:
        print(f"{eid}. {name}")

    try:
        exam_id = int(input("\nEnter Exam ID to delete: "))
    except:
        print("Invalid input.")
        return

    CUR.execute("SELECT * FROM exams WHERE exam_id=%s", (exam_id,))
    exists = CUR.fetchone()

    if not exists:
        print("Exam not found.")
        return

    print("\nAre you sure that you wish to delete this Exam?")
    c = input("Type YES to confirm: ").upper()

    if c == "YES":
        CUR.execute("DELETE FROM exams WHERE exam_id=%s", (exam_id,))
        DB.commit()
        print("Exam deleted.")
    else:
        print("Cancelled.")

def main_menu():
    while True:
        print("\n==============================")
        print("STUDENT RESULT SYSTEM")
        print("==============================")
        print("1. Insert Student")
        print("2. Insert Subject")
        print("3. Insert Exam")
        print("4. Insert Marks")
        print("5. Search Records")
        print("6. Manage Records")
        print("7. Generate PDF Report")
        print("8. Exit")

        choice = input("Choose an option (1-8): ").strip()

        if choice == "1":
            insert_student()
        elif choice == "2":
            insert_subject()
        elif choice == "3":
            insert_exam()
        elif choice == "4":
            insert_marks()
        elif choice == "5":
            search_menu()
        elif choice == "6":
            manage_menu()
        elif choice == "7":
            generate_pdf_report()
                   
        elif choice == "8":
            print("Exiting.")
            break
        else:
            print("Invalid choice.")

def start_menu():
    while True:
        
        print("ACCESS MENU")
        
        print("1. Sign Up")
        print("2. Login")
        print("3. Exit")

        choice = input("Choose an option (1-3): ")

        if choice == "1":
            username = input("Enter your username: ")
            password = input("Enter your password: ").strip()
            add_teacher(username, password)
            print("Account created.")
        
        elif choice == "2":
            if login():
                return True     
            else:
                continue
                                       
        elif choice == "3":
            print("Exiting.")
            return False
        
        else:
            print("Invalid choice.")

if __name__ == "__main__":   
    if start_menu():
        main_menu()


