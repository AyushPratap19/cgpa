from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector

app = Flask(__name__)
app.secret_key = 'ayush'

# Database connection
def get_db_connection():
    conn = mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="Rajawat@5776",
        database="cgpa"
    )
    return conn

# Fetch subjects and calculate CGPA for a semester
def calculate_cgpa_and_get_subjects(semester):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, subject_name FROM subjects WHERE semester_id = %s', (semester,))
    subjects = cursor.fetchall()
    conn.close()
    return subjects

# Calculate SGPA for a semester
def calculate_sgpa(marks):
    conn = get_db_connection()
    cursor = conn.cursor()
    total_marks = 0
    total_grade_points = 0
    
    for subject_id, mark in marks.items():
        cursor.execute("SELECT grade_point FROM subjects WHERE id = %s", (subject_id,))
        row = cursor.fetchone()
        if row:
            grade_point = row[0]
            total_marks += mark * grade_point
            total_grade_points += grade_point
        else:
            print(f"No grade point found for subject with ID {subject_id}")

    conn.close()

    if total_grade_points > 0:
        sgpa = total_marks / total_grade_points
        return sgpa, total_marks, total_grade_points
    else:
        return None, None, None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/check_student', methods=['POST'])
def check_student():
    usn = request.form['usn']
    semester = int(request.form['semester'])
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM students WHERE usn = %s AND sem = %s", (usn, semester))
    existing_student = cursor.fetchone()
    
    if existing_student:
        conn.close()
        return render_template('student_exists.html', student=existing_student)
    else:
        subjects = calculate_cgpa_and_get_subjects(semester)
        conn.close()
        if subjects:
            return render_template('new_student.html', usn=usn, semester=semester, subjects=subjects)
        else:
            flash(f"No subjects found for semester {semester}.")
            return redirect(url_for('index'))

@app.route('/calculate', methods=['POST'])
def calculate():
    usn = request.form['usn']
    semester = int(request.form['semester'])
    name = request.form['name']
    
    subjects = calculate_cgpa_and_get_subjects(semester)
    if subjects:
        marks = {}
        for subject in subjects:
            subject_id, subject_name = subject
            mark = int(request.form[f'mark_{subject_id}'])
            if mark == 100:
                mark = mark / 10
            else:
                mark = mark // 10 + 1
            marks[subject_id] = mark
        
        cgpa, total_marks, total_grade_points = calculate_sgpa(marks)
        if cgpa is not None:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO students (usn, name, cgpa, sem, total_marks, total_grade_points) VALUES (%s, %s, %s, %s, %s, %s)", (usn, name, cgpa, semester, total_marks, total_grade_points))
            conn.commit()
            conn.close()
            return render_template('sgpa_result.html', semester=semester, sgpa=cgpa)
        else:
            flash("Error calculating SGPA.")
    else:
        flash(f"No subjects found for semester {semester}.")
    
    return redirect(url_for('index'))

@app.route('/calculate_cgpa', methods=['POST'])
def calculate_cgpa():
    usn = request.form['usn']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Fetch the student's name from the database
    cursor.execute("SELECT name FROM students WHERE usn = %s", (usn,))
    student_name = cursor.fetchone()[0]  # Assuming name is the third column
    
    # Consume all result sets
    while cursor.nextset():
        pass
    
    # Fetch all semester data for the specified student
    cursor.execute("SELECT total_marks, total_grade_points FROM students WHERE usn = %s", (usn,))
    results = cursor.fetchall()
    
    # Calculate cumulative total marks and total grade points
    cumulative_total_marks = 0
    cumulative_total_grade_points = 0
    for total_marks, total_grade_points in results:
        cumulative_total_marks += total_marks
        cumulative_total_grade_points += total_grade_points
    
    conn.close()
    
    if cumulative_total_grade_points > 0:
        # Calculate CGPA
        cgpa = cumulative_total_marks / cumulative_total_grade_points
        return render_template('overall_cgpa.html', student_name=student_name, cgpa=cgpa)
    else:
        flash("Error calculating CGPA: Total grade points is 0.")
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
