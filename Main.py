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
                print("Invalid choice.")
                return False

    print("Too many failed attempts.")
    return False

def insert_student():
    i = int(input("Enter ID: "))
    nm = input("Enter Name: ").upper()
    cl = input("Enter Class (e.g. XII-A): ").upper()
    g = input("Enter Gender: ").upper()
    h = input("Enter House: ").upper()
    att = float(input("Enter Attendance %: "))
    CUR.execute("INSERT INTO students VALUES (%s,%s,%s,%s,%s,%s)", (i, nm, cl, g, h, att))
    DB.commit()
    print("Student inserted.")

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
    sid = int(input("Enter Student ID: "))
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
    w = float(input(f"Enter Written Marks (out of {mw}): "))
    p = float(input(f"Enter Practical Marks (out of {mp}): "))
    total = w + p

    CUR.execute("INSERT INTO marks VALUES (%s,%s,%s,%s,%s,%s)", (sid, subj_id, exam_id, w, p, total))
    DB.commit()
    print("Marks inserted.")

def show_data():
    CUR.execute("SELECT * FROM students")
    rows = CUR.fetchall()
    df = pd.DataFrame(rows, columns=["ID","Name","Class","Gender","House","Attendance"])
    print(df)

def generate_pdf_report():
    CUR.execute("""
        SELECT s.id, s.sname, s.sclass, sub.subject_name, e.exam_name,
               m.written, m.practical, m.total 
        FROM marks m 
        JOIN students s ON s.id=m.id 
        JOIN subjects sub ON sub.subject_id=m.subject_id 
        JOIN exams e ON e.exam_id=m.exam_id 
        ORDER BY s.id
    """)
    data = CUR.fetchall()

    if not data:
        print("No data found.")
        return

    df = pd.DataFrame(data, columns=["ID","Name","Class","Subject","Exam","Written","Practical","Total"])
    pdf_path = "student_report.pdf"

    with PdfPages(pdf_path) as pdf:
        for sid, group in df.groupby("ID"):
            fig, ax = plt.subplots(figsize=(8,5))
            ax.axis("tight")
            ax.axis("off")
            table_data = group[["Subject","Exam","Written","Practical","Total"]].values.tolist()
            table = ax.table(cellText=table_data,
                             colLabels=["Subject","Exam","Written","Practical","Total"],
                             loc="center")
            table.auto_set_font_size(False)
            table.set_fontsize(8)
            plt.title(f"Student ID: {sid} | Name: {group.iloc[0]['Name']} | Class: {group.iloc[0]['Class']}")
            pdf.savefig()
            plt.close()

    print("PDF report generated as", pdf_path)

def main_menu():
    while True:
        print("\n==============================")
        print("STUDENT RESULT SYSTEM")
        print("==============================")
        print("1. Insert Student")
        print("2. Insert Subject")
        print("3. Insert Exam")
        print("4. Insert Marks")
        print("5. Show Data")
        print("6. Generate PDF Report")
        print("7. Exit")

        choice = input("Choose an option (1-7): ").strip()

        if choice == "1":
            insert_student()
        elif choice == "2":
            insert_subject()
        elif choice == "3":
            insert_exam()
        elif choice == "4":
            insert_marks()
        elif choice == "5":
            show_data()
        elif choice == "6":
            generate_pdf_report()
        elif choice == "7":
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
