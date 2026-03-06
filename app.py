from flask import Flask, render_template, request, redirect, url_for, session, flash
from db_config import get_connection, UPLOAD_FOLDER, allowed_file
import os, uuid

app = Flask(__name__)
app.secret_key = 'student_db_secret_2024'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def save_photo(file):
    if file and allowed_file(file.filename):
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{ext}"
        file.save(os.path.join(UPLOAD_FOLDER, filename))
        return filename
    return None

def login_required(roles=None):
    if 'user' not in session:
        return redirect(url_for('login'))
    if roles and session.get('role') not in roles:
        flash('Access denied. You do not have permission for this action.', 'error')
        return redirect(url_for('dashboard'))
    return None

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        portal   = request.form['portal']
        conn = get_connection()
        cur  = conn.cursor()
        cur.execute("SELECT Role, Ref_ID FROM Admin_Users WHERE Username=:1 AND Password=:2", (username, password))
        result = cur.fetchone()
        cur.close(); conn.close()
        if result:
            role, ref_id = result[0], result[1]
            if role != portal:
                flash(f'This account is not a {portal} account. Please use the correct portal.', 'error')
                return render_template('login.html')
            session['user']   = username
            session['role']   = role
            session['ref_id'] = ref_id
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    guard = login_required()
    if guard: return guard
    role = session['role']
    conn = get_connection()
    cur  = conn.cursor()

    if role == 'student':
        cur.execute("""
            SELECT s.Student_ID, s.First_Name, s.Last_Name, s.Email, s.Phone,
                   f.First_Name||' '||f.Last_Name AS Faculty,
                   d.Department_Name, s.Photo,
                   TO_CHAR(s.Date_of_Birth,'DD-MON-YYYY')
            FROM Student s
            JOIN Faculty f    ON s.Faculty_ID    = f.Faculty_ID
            JOIN Department d ON f.Department_ID = d.Department_ID
            WHERE s.Student_ID = :1
        """, (session['ref_id'],))
        student = cur.fetchone()
        cur.execute("""
            SELECT c.Course_Name, c.Credits, c.Semester, e.Grade,
                   TO_CHAR(e.Enroll_Date,'DD-MON-YYYY')
            FROM Enrollment e JOIN Course c ON e.Course_Code = c.Course_Code
            WHERE e.Student_ID = :1
        """, (session['ref_id'],))
        enrollments = cur.fetchall()
        cur.execute("""
            SELECT c.Course_Name,
                   COUNT(*) AS Total,
                   SUM(CASE WHEN a.Status='Present' THEN 1 ELSE 0 END) AS Present_Days,
                   ROUND(SUM(CASE WHEN a.Status='Present' THEN 1 ELSE 0 END)*100/COUNT(*),1) AS Pct
            FROM Attendance a JOIN Course c ON a.Course_Code = c.Course_Code
            WHERE a.Student_ID = :1
            GROUP BY c.Course_Name
        """, (session['ref_id'],))
        attendance = cur.fetchall()
        cur.close(); conn.close()
        return render_template('student_dashboard.html', student=student, enrollments=enrollments, attendance=attendance)

    elif role == 'faculty':
        cur.execute("""
            SELECT f.Faculty_ID, f.First_Name, f.Last_Name, f.Email, f.Phone,
                   d.Department_Name, f.Photo, f.Qualification
            FROM Faculty f JOIN Department d ON f.Department_ID = d.Department_ID
            WHERE f.Faculty_ID = :1
        """, (session['ref_id'],))
        faculty = cur.fetchone()
        cur.execute("""
            SELECT s.Student_ID, s.First_Name||' '||s.Last_Name, s.Email, s.Phone, s.Photo
            FROM Student s WHERE s.Faculty_ID = :1
        """, (session['ref_id'],))
        students = cur.fetchall()
        cur.close(); conn.close()
        return render_template('faculty_dashboard.html', faculty=faculty, students=students)

    else:
        cur.execute("SELECT COUNT(*) FROM Student");   ts = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM Faculty");   tf = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM Course");    tc = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM Department"); td = cur.fetchone()[0]
        cur.close(); conn.close()
        return render_template('dashboard.html', total_students=ts, total_faculty=tf, total_courses=tc, total_depts=td)

@app.route('/students')
def students():
    guard = login_required(['admin', 'faculty'])
    if guard: return guard
    conn = get_connection(); cur = conn.cursor()
    cur.execute("""
        SELECT s.Student_ID, s.First_Name, s.Last_Name, s.Email, s.Phone,
               f.First_Name||' '||f.Last_Name, s.Faculty_ID, s.Photo
        FROM Student s LEFT JOIN Faculty f ON s.Faculty_ID = f.Faculty_ID ORDER BY s.Student_ID
    """)
    students_data = cur.fetchall()
    cur.execute("SELECT Faculty_ID, First_Name||' '||Last_Name FROM Faculty ORDER BY Faculty_ID")
    faculty_list = cur.fetchall()
    cur.close(); conn.close()
    return render_template('students.html', students=students_data, faculty=faculty_list)

@app.route('/students/add', methods=['POST'])
def add_student():
    guard = login_required(['admin'])
    if guard: return guard
    conn = get_connection(); cur = conn.cursor()
    try:
        photo_name = save_photo(request.files.get('photo'))
        cur.execute("""
            INSERT INTO Student (Student_ID,First_Name,Last_Name,Email,Phone,Faculty_ID,Photo)
            VALUES (:1,:2,:3,:4,:5,:6,:7)
        """, (request.form['student_id'], request.form['first_name'], request.form['last_name'],
              request.form['email'], request.form['phone'], request.form['faculty_id'], photo_name))
        rows = cur.rowcount; conn.commit()
        flash(f'✅ Oracle DB: {rows} row inserted into STUDENT table successfully!', 'success')
    except Exception as e:
        conn.rollback(); flash(f'❌ Oracle DB: Insert failed — {str(e)}', 'error')
    finally:
        cur.close(); conn.close()
    return redirect(url_for('students'))

@app.route('/students/update', methods=['POST'])
def update_student():
    guard = login_required(['admin'])
    if guard: return guard
    conn = get_connection(); cur = conn.cursor()
    try:
        photo_file = request.files.get('photo')
        photo_name = save_photo(photo_file) if photo_file and photo_file.filename else None
        if photo_name:
            cur.execute("""UPDATE Student SET First_Name=:1,Last_Name=:2,Email=:3,Phone=:4,Faculty_ID=:5,Photo=:6 WHERE Student_ID=:7""",
                (request.form['first_name'], request.form['last_name'], request.form['email'],
                 request.form['phone'], request.form['faculty_id'], photo_name, request.form['student_id']))
        else:
            cur.execute("""UPDATE Student SET First_Name=:1,Last_Name=:2,Email=:3,Phone=:4,Faculty_ID=:5 WHERE Student_ID=:6""",
                (request.form['first_name'], request.form['last_name'], request.form['email'],
                 request.form['phone'], request.form['faculty_id'], request.form['student_id']))
        rows = cur.rowcount; conn.commit()
        flash(f'✅ Oracle DB: {rows} row updated in STUDENT table successfully!', 'success')
    except Exception as e:
        conn.rollback(); flash(f'❌ Oracle DB: Update failed — {str(e)}', 'error')
    finally:
        cur.close(); conn.close()
    return redirect(url_for('students'))

@app.route('/students/delete/<int:student_id>')
def delete_student(student_id):
    guard = login_required(['admin'])
    if guard: return guard
    conn = get_connection(); cur = conn.cursor()
    try:
        cur.execute("DELETE FROM Attendance WHERE Student_ID=:1", (student_id,)); ar = cur.rowcount
        cur.execute("DELETE FROM Enrollment WHERE Student_ID=:1",  (student_id,)); er = cur.rowcount
        cur.execute("DELETE FROM Student WHERE Student_ID=:1",     (student_id,)); sr = cur.rowcount
        conn.commit()
        flash(f'✅ Oracle DB: {sr} row deleted from STUDENT. {er} enrollment(s) and {ar} attendance record(s) also removed.', 'success')
    except Exception as e:
        conn.rollback(); flash(f'❌ Oracle DB: Delete failed — {str(e)}', 'error')
    finally:
        cur.close(); conn.close()
    return redirect(url_for('students'))

@app.route('/faculty/students')
def faculty_students():
    guard = login_required(['admin', 'faculty'])
    if guard: return guard
    conn = get_connection(); cur = conn.cursor()
    if session['role'] == 'faculty':
        cur.execute("""
            SELECT s.Student_ID, s.First_Name||' '||s.Last_Name,
                   c.Course_Code, c.Course_Name, e.Grade, e.Enrollment_ID
            FROM Student s
            JOIN Enrollment e ON s.Student_ID  = e.Student_ID
            JOIN Course c     ON e.Course_Code = c.Course_Code
            WHERE s.Faculty_ID = :1 ORDER BY s.Student_ID
        """, (session['ref_id'],))
    else:
        cur.execute("""
            SELECT s.Student_ID, s.First_Name||' '||s.Last_Name,
                   c.Course_Code, c.Course_Name, e.Grade, e.Enrollment_ID
            FROM Student s
            JOIN Enrollment e ON s.Student_ID  = e.Student_ID
            JOIN Course c     ON e.Course_Code = c.Course_Code
            ORDER BY s.Student_ID
        """)
    data = cur.fetchall()
    cur.close(); conn.close()
    return render_template('faculty_students.html', data=data)

@app.route('/faculty/update_grade', methods=['POST'])
def update_grade():
    guard = login_required(['admin', 'faculty'])
    if guard: return guard
    conn = get_connection(); cur = conn.cursor()
    try:
        cur.execute("UPDATE Enrollment SET Grade=:1 WHERE Student_ID=:2 AND Course_Code=:3",
            (request.form['grade'], request.form['student_id'], request.form['course_code']))
        rows = cur.rowcount; conn.commit()
        flash(f'✅ Oracle DB: {rows} row updated in ENROLLMENT table — grade changed!', 'success')
    except Exception as e:
        conn.rollback(); flash(f'❌ Oracle DB: Grade update failed — {str(e)}', 'error')
    finally:
        cur.close(); conn.close()
    return redirect(url_for('faculty_students'))

@app.route('/attendance')
def attendance():
    guard = login_required()
    if guard: return guard
    conn = get_connection(); cur = conn.cursor()
    role = session['role']
    if role == 'student':
        cur.execute("""
            SELECT a.Attend_ID, s.First_Name||' '||s.Last_Name,
                   c.Course_Name, TO_CHAR(a.Attend_Date,'DD-MON-YYYY'), a.Status
            FROM Attendance a
            JOIN Student s ON a.Student_ID  = s.Student_ID
            JOIN Course c  ON a.Course_Code = c.Course_Code
            WHERE a.Student_ID = :1 ORDER BY a.Attend_Date DESC
        """, (session['ref_id'],))
    elif role == 'faculty':
        cur.execute("""
            SELECT a.Attend_ID, s.First_Name||' '||s.Last_Name,
                   c.Course_Name, TO_CHAR(a.Attend_Date,'DD-MON-YYYY'), a.Status
            FROM Attendance a
            JOIN Student s ON a.Student_ID  = s.Student_ID
            JOIN Course c  ON a.Course_Code = c.Course_Code
            WHERE s.Faculty_ID = :1 ORDER BY a.Attend_Date DESC
        """, (session['ref_id'],))
    else:
        cur.execute("""
            SELECT a.Attend_ID, s.First_Name||' '||s.Last_Name,
                   c.Course_Name, TO_CHAR(a.Attend_Date,'DD-MON-YYYY'), a.Status
            FROM Attendance a
            JOIN Student s ON a.Student_ID  = s.Student_ID
            JOIN Course c  ON a.Course_Code = c.Course_Code
            ORDER BY a.Attend_Date DESC
        """)
    attend_data = cur.fetchall()
    cur.execute("SELECT Student_ID, First_Name||' '||Last_Name FROM Student ORDER BY Student_ID")
    student_list = cur.fetchall()
    cur.execute("SELECT Course_Code, Course_Name FROM Course ORDER BY Course_Code")
    course_list = cur.fetchall()
    cur.close(); conn.close()
    return render_template('attendance.html', attendance=attend_data, students=student_list, courses=course_list)

@app.route('/attendance/add', methods=['POST'])
def add_attendance():
    guard = login_required(['admin', 'faculty'])
    if guard: return guard
    conn = get_connection(); cur = conn.cursor()
    try:
        cur.execute("SELECT attend_seq.NEXTVAL FROM DUAL")
        new_id = cur.fetchone()[0]
        cur.execute("INSERT INTO Attendance VALUES (:1,:2,:3,SYSDATE,:4)",
            (new_id, request.form['student_id'], request.form['course_code'], request.form['status']))
        rows = cur.rowcount; conn.commit()
        flash(f'✅ Oracle DB: {rows} row inserted into ATTENDANCE table successfully!', 'success')
    except Exception as e:
        conn.rollback(); flash(f'❌ Oracle DB: Insert failed — {str(e)}', 'error')
    finally:
        cur.close(); conn.close()
    return redirect(url_for('attendance'))

@app.route('/attendance/delete/<int:attend_id>')
def delete_attendance(attend_id):
    guard = login_required(['admin'])
    if guard: return guard
    conn = get_connection(); cur = conn.cursor()
    try:
        cur.execute("DELETE FROM Attendance WHERE Attend_ID=:1", (attend_id,))
        rows = cur.rowcount; conn.commit()
        flash(f'✅ Oracle DB: {rows} row deleted from ATTENDANCE table.', 'success')
    except Exception as e:
        conn.rollback(); flash(f'❌ Oracle DB: Delete failed — {str(e)}', 'error')
    finally:
        cur.close(); conn.close()
    return redirect(url_for('attendance'))

@app.route('/faculty')
def faculty():
    guard = login_required(['admin'])
    if guard: return guard
    conn = get_connection(); cur = conn.cursor()
    cur.execute("""
        SELECT f.Faculty_ID, f.First_Name, f.Last_Name, f.Email, f.Phone,
               d.Department_Name, f.Department_ID, f.Photo, f.Qualification
        FROM Faculty f LEFT JOIN Department d ON f.Department_ID = d.Department_ID ORDER BY f.Faculty_ID
    """)
    faculty_data = cur.fetchall()
    cur.execute("SELECT Department_ID, Department_Name FROM Department ORDER BY Department_ID")
    dept_list = cur.fetchall()
    cur.close(); conn.close()
    return render_template('faculty.html', faculty=faculty_data, departments=dept_list)

@app.route('/faculty/add', methods=['POST'])
def add_faculty():
    guard = login_required(['admin'])
    if guard: return guard
    conn = get_connection(); cur = conn.cursor()
    try:
        photo_name = save_photo(request.files.get('photo'))
        cur.execute("""INSERT INTO Faculty (Faculty_ID,First_Name,Last_Name,Email,Phone,Department_ID,Photo,Qualification)
            VALUES (:1,:2,:3,:4,:5,:6,:7,:8)""",
            (request.form['faculty_id'], request.form['first_name'], request.form['last_name'],
             request.form['email'], request.form['phone'], request.form['department_id'],
             photo_name, request.form.get('qualification','')))
        rows = cur.rowcount; conn.commit()
        flash(f'✅ Oracle DB: {rows} row inserted into FACULTY table successfully!', 'success')
    except Exception as e:
        conn.rollback(); flash(f'❌ Oracle DB: Insert failed — {str(e)}', 'error')
    finally:
        cur.close(); conn.close()
    return redirect(url_for('faculty'))

@app.route('/faculty/update', methods=['POST'])
def update_faculty():
    guard = login_required(['admin'])
    if guard: return guard
    conn = get_connection(); cur = conn.cursor()
    try:
        photo_file = request.files.get('photo')
        photo_name = save_photo(photo_file) if photo_file and photo_file.filename else None
        if photo_name:
            cur.execute("""UPDATE Faculty SET First_Name=:1,Last_Name=:2,Email=:3,Phone=:4,
                Department_ID=:5,Photo=:6,Qualification=:7 WHERE Faculty_ID=:8""",
                (request.form['first_name'], request.form['last_name'], request.form['email'],
                 request.form['phone'], request.form['department_id'], photo_name,
                 request.form.get('qualification',''), request.form['faculty_id']))
        else:
            cur.execute("""UPDATE Faculty SET First_Name=:1,Last_Name=:2,Email=:3,Phone=:4,
                Department_ID=:5,Qualification=:6 WHERE Faculty_ID=:7""",
                (request.form['first_name'], request.form['last_name'], request.form['email'],
                 request.form['phone'], request.form['department_id'],
                 request.form.get('qualification',''), request.form['faculty_id']))
        rows = cur.rowcount; conn.commit()
        flash(f'✅ Oracle DB: {rows} row updated in FACULTY table successfully!', 'success')
    except Exception as e:
        conn.rollback(); flash(f'❌ Oracle DB: Update failed — {str(e)}', 'error')
    finally:
        cur.close(); conn.close()
    return redirect(url_for('faculty'))

@app.route('/faculty/delete/<int:faculty_id>')
def delete_faculty(faculty_id):
    guard = login_required(['admin'])
    if guard: return guard
    conn = get_connection(); cur = conn.cursor()
    try:
        cur.execute("DELETE FROM Faculty WHERE Faculty_ID=:1", (faculty_id,))
        rows = cur.rowcount; conn.commit()
        flash(f'✅ Oracle DB: {rows} row deleted from FACULTY table successfully!', 'success')
    except Exception as e:
        conn.rollback(); flash(f'❌ Oracle DB: Delete failed — {str(e)}', 'error')
    finally:
        cur.close(); conn.close()
    return redirect(url_for('faculty'))

@app.route('/courses')
def courses():
    guard = login_required(['admin'])
    if guard: return guard
    conn = get_connection(); cur = conn.cursor()
    cur.execute("""SELECT c.Course_Code, c.Course_Name, c.Credits, c.Semester,
               d.Department_Name, c.Department_ID FROM Course c
               LEFT JOIN Department d ON c.Department_ID=d.Department_ID ORDER BY c.Course_Code""")
    courses_data = cur.fetchall()
    cur.execute("SELECT Department_ID, Department_Name FROM Department ORDER BY Department_ID")
    dept_list = cur.fetchall()
    cur.close(); conn.close()
    return render_template('courses.html', courses=courses_data, departments=dept_list)

@app.route('/courses/add', methods=['POST'])
def add_course():
    guard = login_required(['admin'])
    if guard: return guard
    conn = get_connection(); cur = conn.cursor()
    try:
        cur.execute("INSERT INTO Course (Course_Code,Course_Name,Credits,Semester,Department_ID) VALUES (:1,:2,:3,:4,:5)",
            (request.form['course_code'], request.form['course_name'],
             request.form['credits'], request.form['semester'], request.form['department_id']))
        rows = cur.rowcount; conn.commit()
        flash(f'✅ Oracle DB: {rows} row inserted into COURSE table successfully!', 'success')
    except Exception as e:
        conn.rollback(); flash(f'❌ Oracle DB: Insert failed — {str(e)}', 'error')
    finally:
        cur.close(); conn.close()
    return redirect(url_for('courses'))

@app.route('/courses/update', methods=['POST'])
def update_course():
    guard = login_required(['admin'])
    if guard: return guard
    conn = get_connection(); cur = conn.cursor()
    try:
        cur.execute("UPDATE Course SET Course_Name=:1,Credits=:2,Semester=:3,Department_ID=:4 WHERE Course_Code=:5",
            (request.form['course_name'], request.form['credits'],
             request.form['semester'], request.form['department_id'], request.form['course_code']))
        rows = cur.rowcount; conn.commit()
        flash(f'✅ Oracle DB: {rows} row updated in COURSE table successfully!', 'success')
    except Exception as e:
        conn.rollback(); flash(f'❌ Oracle DB: Update failed — {str(e)}', 'error')
    finally:
        cur.close(); conn.close()
    return redirect(url_for('courses'))

@app.route('/courses/delete/<course_code>')
def delete_course(course_code):
    guard = login_required(['admin'])
    if guard: return guard
    conn = get_connection(); cur = conn.cursor()
    try:
        cur.execute("DELETE FROM Attendance WHERE Course_Code=:1", (course_code,)); ar = cur.rowcount
        cur.execute("DELETE FROM Enrollment WHERE Course_Code=:1", (course_code,)); er = cur.rowcount
        cur.execute("DELETE FROM Course WHERE Course_Code=:1",     (course_code,)); cr = cur.rowcount
        conn.commit()
        flash(f'✅ Oracle DB: {cr} row deleted from COURSE. {er} enrollment(s) and {ar} attendance record(s) also removed.', 'success')
    except Exception as e:
        conn.rollback(); flash(f'❌ Oracle DB: Delete failed — {str(e)}', 'error')
    finally:
        cur.close(); conn.close()
    return redirect(url_for('courses'))

@app.route('/departments')
def departments():
    guard = login_required(['admin'])
    if guard: return guard
    conn = get_connection(); cur = conn.cursor()
    cur.execute("SELECT * FROM Department ORDER BY Department_ID")
    dept_data = cur.fetchall()
    cur.close(); conn.close()
    return render_template('departments.html', departments=dept_data)

@app.route('/departments/add', methods=['POST'])
def add_department():
    guard = login_required(['admin'])
    if guard: return guard
    conn = get_connection(); cur = conn.cursor()
    try:
        cur.execute("INSERT INTO Department VALUES (:1,:2,:3,:4)",
            (request.form['dept_id'], request.form['dept_name'],
             request.form['email'], request.form['location']))
        rows = cur.rowcount; conn.commit()
        flash(f'✅ Oracle DB: {rows} row inserted into DEPARTMENT table successfully!', 'success')
    except Exception as e:
        conn.rollback(); flash(f'❌ Oracle DB: Insert failed — {str(e)}', 'error')
    finally:
        cur.close(); conn.close()
    return redirect(url_for('departments'))

@app.route('/departments/update', methods=['POST'])
def update_department():
    guard = login_required(['admin'])
    if guard: return guard
    conn = get_connection(); cur = conn.cursor()
    try:
        cur.execute("UPDATE Department SET Department_Name=:1,Email=:2,Location=:3 WHERE Department_ID=:4",
            (request.form['dept_name'], request.form['email'],
             request.form['location'], request.form['dept_id']))
        rows = cur.rowcount; conn.commit()
        flash(f'✅ Oracle DB: {rows} row updated in DEPARTMENT table successfully!', 'success')
    except Exception as e:
        conn.rollback(); flash(f'❌ Oracle DB: Update failed — {str(e)}', 'error')
    finally:
        cur.close(); conn.close()
    return redirect(url_for('departments'))

@app.route('/departments/delete/<int:dept_id>')
def delete_department(dept_id):
    guard = login_required(['admin'])
    if guard: return guard
    conn = get_connection(); cur = conn.cursor()
    try:
        cur.execute("DELETE FROM Department WHERE Department_ID=:1", (dept_id,))
        rows = cur.rowcount; conn.commit()
        flash(f'✅ Oracle DB: {rows} row deleted from DEPARTMENT table successfully!', 'success')
    except Exception as e:
        conn.rollback(); flash(f'❌ Oracle DB: Delete failed — {str(e)}', 'error')
    finally:
        cur.close(); conn.close()
    return redirect(url_for('departments'))

@app.route('/enrollments')
def enrollments():
    guard = login_required(['admin'])
    if guard: return guard
    conn = get_connection(); cur = conn.cursor()
    cur.execute("""SELECT e.Enrollment_ID, s.First_Name||' '||s.Last_Name,
               c.Course_Name, e.Grade, TO_CHAR(e.Enroll_Date,'DD-MON-YYYY'), e.Student_ID, e.Course_Code
               FROM Enrollment e JOIN Student s ON e.Student_ID=s.Student_ID
               JOIN Course c ON e.Course_Code=c.Course_Code ORDER BY e.Enrollment_ID""")
    enroll_data = cur.fetchall()
    cur.execute("SELECT Student_ID, First_Name||' '||Last_Name FROM Student ORDER BY Student_ID")
    student_list = cur.fetchall()
    cur.execute("SELECT Course_Code, Course_Name FROM Course ORDER BY Course_Code")
    course_list = cur.fetchall()
    cur.close(); conn.close()
    return render_template('enrollments.html', enrollments=enroll_data, students=student_list, courses=course_list)

@app.route('/enrollments/add', methods=['POST'])
def add_enrollment():
    guard = login_required(['admin'])
    if guard: return guard
    conn = get_connection(); cur = conn.cursor()
    try:
        cur.execute("SELECT enrollment_seq.NEXTVAL FROM DUAL")
        new_id = cur.fetchone()[0]
        cur.execute("INSERT INTO Enrollment VALUES (:1,:2,:3,SYSDATE,:4)",
            (new_id, request.form['student_id'], request.form['course_code'], request.form['grade']))
        rows = cur.rowcount; conn.commit()
        flash(f'✅ Oracle DB: {rows} row inserted into ENROLLMENT table. Audit trigger also fired!', 'success')
    except Exception as e:
        conn.rollback(); flash(f'❌ Oracle DB: Enrollment failed — {str(e)}', 'error')
    finally:
        cur.close(); conn.close()
    return redirect(url_for('enrollments'))

@app.route('/enrollments/delete/<int:enrollment_id>')
def delete_enrollment(enrollment_id):
    guard = login_required(['admin'])
    if guard: return guard
    conn = get_connection(); cur = conn.cursor()
    try:
        cur.execute("DELETE FROM Enrollment WHERE Enrollment_ID=:1", (enrollment_id,))
        rows = cur.rowcount; conn.commit()
        flash(f'✅ Oracle DB: {rows} row deleted from ENROLLMENT table successfully!', 'success')
    except Exception as e:
        conn.rollback(); flash(f'❌ Oracle DB: Delete failed — {str(e)}', 'error')
    finally:
        cur.close(); conn.close()
    return redirect(url_for('enrollments'))

@app.route('/reports')
def reports():
    guard = login_required(['admin'])
    if guard: return guard
    conn = get_connection(); cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM Student");   ts = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM Faculty");   tf = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM Course");    tc = cur.fetchone()[0]
    cur.execute("SELECT AVG(Credits) FROM Course"); avg_c = round(cur.fetchone()[0] or 0, 2)
    cur.execute("SELECT MAX(Credits) FROM Course"); max_c = cur.fetchone()[0]
    cur.execute("SELECT MIN(Credits) FROM Course"); min_c = cur.fetchone()[0]
    cur.execute("SELECT SUM(Credits) FROM Course"); sum_c = cur.fetchone()[0]
    cur.execute("SELECT * FROM vw_Department_Report ORDER BY Student_Count DESC")
    dept_report = cur.fetchall()
    cur.execute("SELECT * FROM vw_Course_Enrollment ORDER BY Enrolled_Count DESC")
    course_report = cur.fetchall()
    cur.execute("SELECT * FROM vw_Student_Details ORDER BY Student_ID")
    student_view = cur.fetchall()
    cur.execute("""SELECT Log_ID, Action_Type, Table_Name,
               TO_CHAR(Action_Date,'DD-MON-YYYY HH24:MI:SS'), Done_By
               FROM Audit_Log ORDER BY Log_ID DESC""")
    audit_data = cur.fetchall()
    cur.close(); conn.close()
    return render_template('reports.html',
        total_students=ts, total_faculty=tf, total_courses=tc,
        avg_credits=avg_c, max_credits=max_c, min_credits=min_c, sum_credits=sum_c,
        dept_report=dept_report, course_report=course_report,
        student_view=student_view, audit_data=audit_data)

if __name__ == '__main__':
    app.run(debug=True)