from flask import Flask, render_template, request,session,send_file,flash,url_for,redirect
import sqlite3
import pandas as pd
import datetime

app = Flask(__name__)
app.secret_key = '123' 

#-------------------------------------home-page----------------------------------------------------------------#

@app.route("/")
def home():
    return render_template("index.html")

#---------------------------------------------------------------------------------------------------------------#



#---------------------------------admin-login-process----------------------------------------------------------------#

@app.route("/admin_login_form")
def admin_login_form():
    username="Admin"
    userid = 0
    return render_template("admin/login.html",username=username,userid=userid)


@app.route('/login_user_admin', methods=["POST", "GET"])
def login_user_admin():
    user_name = request.form['user_name']
    password = request.form['password']
    userid = request.form['user_id']
    
    if user_name == "Admin" and password == "123" and userid == "0":
        return render_template("admin/index.html")
    else:
        return "Username or password invalid.", "error"


#-----------------------------------------------------------------------------------------------------------------#





#-------------------------------------staffs login process---------------------------------------------------------------------#

@app.route("/staff_login_form")
def staff_login_form():
    return render_template("staff/login.html")


@app.route('/login_user_staff', methods=["POST", "GET"])
def login_user_staff():
    staff_name = request.form['user_name']
    password = request.form['password']
    staffid = request.form['user_id']
    con = sqlite3.connect("data_base.db")
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute("Select * from staffs where staffname=? and password=? and staffid =?", (staff_name, password,int(staffid)))
    data = cur.fetchall()
    if data:
        session['staffid'] = staffid
        session['staffname'] = staff_name
        return render_template("staff/index.html")
    else:
        return "invalid user or password"

#-------------------------------------------------------------------------------------------------------------------------------#





#----------------------------------others-login-process---------------------------------------------------------------------------#

@app.route('/login_user_other', methods=["POST", "GET"])
def login_user_other():
    return render_template("other/index.html")

#-----------------------------------------------------------------------------------------------------------------------#




#------------------------------------manage class admin--------------------------------------------------------------#

@app.route("/manage_classes_admin", methods=["POST", "GET"])
def manage_classes_admin():
    con = sqlite3.connect("data_base.db")
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute("Select * from all_classes")
    data = cur.fetchall()
    con.close()
    return render_template("admin/manage_classes.html", data=data)

#--------------------------------------------------------------------------------------------------------------------#





#--------------------------------manage-classes-staff---------------------------------------------------------------------------#

@app.route("/manage_classes_staff", methods=["POST", "GET"])
def manage_classes_staff():
    con = sqlite3.connect("data_base.db")
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    staffid = session.get('staffid')
    staffname = session.get('staffname')
    query = f"select * from all_classes where staffid ={staffid}"
    cur.execute(query )
    data = cur.fetchall()
    con.close()
    return render_template("staff/manage_classes.html", data=data,staffid =staffid ,staffname = staffname )

#--------------------------------------------------------------------------------------------------------------------------#





#--------------CLASS CREATION,DELETION,UPDATION PROCESS BOTH ADMIN and STAFFs---------------------------------------------#

# create class
@app.route("/create_class", methods=["POST", "GET"])
def create_class():
    try:
        in_classname = request.form['classname']
        in_classid = request.form['classid']
        in_staffname = request.form['staffname']
        in_staffid = request.form['staffid']
        dept =request.form['dept']
        year = request.form['year']
        file = request.files.get('file')
        if not file:
            return "No file uploaded, please upload the student details Excel file."

        con = sqlite3.connect('data_base.db')
        cur = con.cursor()

        cur.execute("SELECT * FROM all_classes WHERE classname = ?", (in_classname,))
        data = cur.fetchone()
        if data:
            return "Class Name already exists, give a valid class name."

        cur.execute("SELECT * FROM all_classes WHERE classid = ?", (in_classid,))
        data = cur.fetchone()
        if data:
            return "Class ID already exists, give a valid class ID."

        cur.execute("INSERT INTO all_classes(classname, classid, staffname,staffid,dept,year) VALUES(?,?,?,?,?,?)",
                    (in_classname, in_classid, in_staffname,in_staffid,dept,year))

        create_table_query = f"""
        CREATE TABLE IF NOT EXISTS {in_classname} (
            slno INTEGER,
            rollno INTEGER,
            name VARCHAR(50),
            present INTEGER, absent INTEGER,
            date VARCHAR(50)
        )
        """
        cur.execute(create_table_query)
        
        df = pd.read_excel(file)
        df = df[['slno','rollno', 'name']] 
        df['present'] = "NULL"
        df['absent'] = "NULL"
        df['date'] = "NULL"
        
        df.to_sql(in_classname, con, if_exists='append', index=False)
        con.commit()
        
        df = pd.read_excel(file)
        df = df[['slno','name', 'rollno','email']] 
        df['classid'] = in_classid
        df['staffid'] = in_staffid
        df['dept'] = dept
        df['year'] = year
        df.to_sql("all_students", con, if_exists='append', index=False)
        con.commit()
        return "Class created successfully"

    except sqlite3.Error as e:
        return f"Error occurred: {e}"

    finally:
        con.close()



# delete class
@app.route('/del_attendance/<string:classname>/<int:classid>', methods=["POST", "GET"])
def del_attendance(classname,classid):
    con = sqlite3.connect("data_base.db")
    cur = con.cursor()
    query = f"DROP TABLE {classname}"
    cur.execute("DELETE FROM all_classes WHERE classname = ?", (classname,))
    
    cur.execute(query)
    query = f"DELETE FROM all_students WHERE classid = {classid}"
    cur.execute(query)
    con.commit()
    con.close()
    return "Deleted successfully"


# edit class
@app.route('/edit_class/<string:classid>', methods=["POST", "GET"])
def edit_class(classid):
    con = sqlite3.connect("data_base.db")
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute("SELECT * FROM all_classes WhERE classid=?", (classid,))
    data = cur.fetchone()
    con.close()
    return render_template('admin/update_class.html', data=data)


@app.route('/update_class', methods=["POST", "GET"])
def update_class():
    in_classname = request.form['classname']
    in_classid = request.form['classid']
    in_oldclassname = request.form['oldclassname']

    con = sqlite3.connect('data_base.db')
    cur = con.cursor()

    if in_oldclassname == in_classname:
        return "NO changes"
        
    else:
        cur.execute("SELECT * FROM all_classes WHERE classname = ?", (in_classname,))
        data = cur.fetchall()
        if data:
            return "The class name already exists"

        cur.execute("UPDATE all_classes SET classname = ? WHERE classid = ?", (in_classname, in_classid))

        try:
            query = f"ALTER TABLE '{in_oldclassname}' RENAME TO '{in_classname}'"
            cur.execute(query)
            con.commit()
        except sqlite3.OperationalError as e:
            return f"Error in renaming class: {e}"

        con.close()
        return "Class Name Updated Successfully !!"

    

#------------------------------------------------------------------------------------------------------------------------------#



#-------------------manage the staff creation-deletion-updation-----------------------------------------------------------#
@app.route("/manage_staff")
def manage_staff():
    con = sqlite3.connect("data_base.db")
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute("Select * from staffs")
    data = cur.fetchall()
    con.close()
    return render_template("admin/manage_staff.html",data=data)



#staff create
@app.route("/create_staff",methods=["POST","GET"])
def create_staff():
    in_staffname = request.form['staffname']
    in_password = request.form['staffpassword']
    in_staffid = request.form['staffid']
    in_confirmpass = request.form['confirmpassword']
    in_dept = request.form['select']


    if in_password == in_confirmpass:
        con = sqlite3.connect("data_base.db")
        cur = con.cursor()
        con.row_factory = sqlite3.Row
        cur.execute("SELECT * FROM staffs WHERE staffname=?", (in_staffname,))

        data = cur.fetchall()
        if data:
            return "user already exist"
        else:
            cur.execute("INSERT INTO staffs(staffname,password,staffid,dept) VALUES(?,?,?,?)", (in_staffname,in_password, in_staffid,in_dept))
            con.commit()
            con.close()
            return "Staff Added successfully"

    else:
        return "password not match"


#updation staff
@app.route('/edit_staff_form/<string:staffid>')
def edit_staff_form(staffid):
    con = sqlite3.connect("data_base.db")
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute("Select * from staffs where staffid = ?",(staffid))
    data = cur.fetchone()
    con.close()
    
    return render_template("admin/update_staff_form.html",data = data)


@app.route("/update_staff",methods=["POST","GET"])
def update_staff():
    try:
        in_staffname = request.form['staffname']
        in_password = request.form['password']
        in_staffid = request.form['staffid']
        in_dept = request.form['dept']
        
        con = sqlite3.connect('data_base.db')
        cur = con.cursor()
        cur.execute("UPDATE staffs SET staffname= ?,dept=?,password= ? WHERE staffid = ?",
                        (in_staffname, in_dept,in_password, int(in_staffid)))
        con.commit()
        con.close()
        return "Updated sucessfully !!"
    except:
        return "Errors In Updation"
    finally:
        con.close()

    

#delete staff
@app.route('/delete_staff/<string:staffid>', methods=["POST", "GET"])
def delete_staff(staffid):
    con = sqlite3.connect("data_base.db")
    cur = con.cursor()
    cur.execute("DELETE FROM staffs WHERE staffid = ?", (staffid,))
    con.commit()
    con.close()
    return "Deleted successfully"

#------------------------------------------------------------------------------------------------------------------------#


#--------------------------------------attendance-module------------------------------------------------------------------#

@app.route("/attendance/<string:classname>/<int:classid>", methods=["GET", "POST"])
def attendance(classname, classid):
    
    formatted_date = datetime.date.today().strftime('%Y-%m-%d')
    con = sqlite3.connect("data_base.db")
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    query = f"SELECT * FROM {classname} WHERE date = ?"
    cur.execute(query, (formatted_date,))
    data = cur.fetchall()
    if data:
        con.close()
        return render_template("staff/today_attendance.html", data=data,classname = classname,classid = classid)
    else:
        query = f"SELECT * FROM all_students WHERE classid = {classid}"
        cur.execute(query)
        data = cur.fetchall()
        con.close()
        return render_template("staff/attendance_sheet.html",data = data,classname = classname,classid = classid)
        

@app.route("/edit_today_attendance", methods=["GET", "POST"]) 
def edit_today_attendance():
    classname = request.form['classname']
    classid = request.form['classid']
    con = sqlite3.connect("data_base.db")
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    query = f"SELECT * FROM all_students WHERE classid = {int(classid)}"
    cur.execute(query)
    data = cur.fetchall()
    return render_template("staff/today_attendance_update_sheet.html",data = data,classname = classname,classid = classid)
    
    

def update_attendance(register_number, present, absent, current_date, classname):
    try:
        conn = sqlite3.connect('data_base.db')
        cursor = conn.cursor()

        # Update query to update attendance for the given register number and date
        query = f"""
        UPDATE {classname}
        SET present = ?, absent = ?
        WHERE rollno = ? AND date = ?
        """

        cursor.execute(query, (present, absent, register_number, current_date))
        conn.commit()
        conn.close()

    except Exception as e:
        print(f"Error updating attendance: {e}")



@app.route('/update_today_attendance', methods=['POST'])
def update_today_attendance():
    current_date = datetime.date.today().strftime('%Y-%m-%d')
    in_classname = request.form['classname']
    processed_students = set()

    for key in request.form:
        if key.startswith('p'):
            try:
                student_slno = key.split('_')[1]  # Extract serial number (slno)
                student_slno = int(student_slno)

                # Get register number (rollno) from form data
                register_no = request.form.get(f'reg_{student_slno}')

                if not register_no:
                    print(f"Error: Register number not found for slno {student_slno}")
                    continue

                if register_no in processed_students:
                    continue

                present = 0
                absent = 0

                for period in range(1, 9):
                    if f'p{period}_{student_slno}' in request.form:
                        present += 1
                    else:
                        absent += 1

                # Call the update function instead of insert
                update_attendance(register_no, present, absent, current_date, in_classname)

                processed_students.add(register_no)

            except IndexError:
                print(f"Error processing attendance for form field: {key}")
                continue

    return "Attendance updated successfully!"





#save attendance
def insert_attendance(register_number, present, absent, current_date, classname):
    try:
        conn = sqlite3.connect('data_base.db')
        cursor = conn.cursor()

        query = f"""
        INSERT INTO {classname} (rollno, date, present, absent)
        VALUES (?, ?, ?, ?)
        """

        cursor.execute(query, (register_number, current_date, present, absent))
        conn.commit()
        conn.close()

    except Exception as e:
        print(f"Error inserting attendance: {e}")


@app.route('/save_attendance', methods=['POST'])
def save_attendance():
    current_date = datetime.date.today().strftime('%Y-%m-%d')
    in_classname = request.form['classname']
    processed_students = set()

    # Debugging: Log the entire form data
    print("Form data:", request.form)

    for key in request.form:
        if key.startswith('p'):  # Identifying attendance-related fields
            try:
                student_slno = key.split('_')[1]  # Extract serial number (slno)
                student_slno = int(student_slno)

                # Get the register number (rollno) from form data
                register_no = request.form.get(f'reg_{student_slno}')
                student_name = request.form.get(f'name_{student_slno}')
                
                # Debugging: Log values of rollno and name
                print(f"Processing student slno: {student_slno}, Register No: {register_no}, Name: {student_name}")

                # Check if rollno or name is missing
                if not register_no or not student_name:
                    print(f"Error: Missing register number or name for slno {student_slno}")
                    continue

                # Skip if this register number has already been processed
                if register_no in processed_students:
                    continue

                present = 0
                absent = 0

                # Count periods marked as present or absent
                for period in range(1, 9):
                    if f'p{period}_{student_slno}' in request.form:
                        present += 1
                    else:
                        absent += 1

                # Insert attendance into the database
                insert_attendance(register_no, present, absent, current_date, in_classname)

                # Mark this register number as processed
                processed_students.add(register_no)

            except IndexError:
                print(f"Error processing attendance for form field: {key}")
                continue

    return "Attendance updated successfully!"



#----------------------------------------------------------------------------------------------------#



#---------------------------report generation------------------------------------------------------------------#

@app.route('/report_generate_form')
def report_generate_form():
    conn = sqlite3.connect("data_base.db")
    cursor = conn.cursor()

    cursor.execute("SELECT DISTINCT classname FROM all_classes")  # Change table name if needed
    classes = [row[0] for row in cursor.fetchall()]

    conn.close()
    return render_template("report_generate_form.html",classes=classes)


# add the after search report form procss
#------------------------------------------------------------------------------------------------------------------#
def get_students_attendance(classname, start_date, end_date):
    conn = sqlite3.connect("data_base.db")
    cursor = conn.cursor()

    query = f"""
        SELECT s.name, s.rollno, s.dept, s.year, 
               SUM(c.present) AS total_present_hours, 
               COUNT(DISTINCT c.date) AS total_days
        FROM all_students s
        JOIN {classname} c ON s.rollno = c.rollno
        WHERE c.date BETWEEN ? AND ?
        GROUP BY s.rollno
    """

    cursor.execute(query, (start_date, end_date))
    students = cursor.fetchall()
    conn.close()

    report = []
    for student in students:
        name, rollno, dept, year, present_hours, total_days = student
        attendance_percentage = (present_hours / (total_days * 8)) * 100 if total_days > 0 else 0

        report.append({
            "name": name,
            "rollno": rollno,
            "dept": dept,
            "year": year,
            "total_present_hours": present_hours,
            "total_days": total_days,
            "attendance_percentage": round(attendance_percentage, 2)
        })

    return report


@app.route('/get_attendance_report_inputs', methods=['GET','POST'])
def get_attendance_report_inputs():
    classname=request.form.get('classname')
    dept = request.form.get('dept')
    year = request.form.get('year')
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')

    report_data = get_students_attendance(classname, start_date, end_date)

    return render_template("attendance_report.html",
                           report_data=report_data,
                           department=dept,
                           start_date=start_date,
                           end_date=end_date,year=year,classname=classname)

@app.route('/download_excel', methods=['GET'])
def download_excel():
    classname = request.args.get('classname')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    report_data = get_students_attendance(classname, start_date, end_date)

    df = pd.DataFrame(report_data)
    df["Student Sign"] = ""  # Empty column for signatures

    excel_file = "attendance_report.xlsx"
    df.to_excel(excel_file, index=False)

    return send_file(excel_file, as_attachment=True)


def get_attendance_percentage(rollno, dept, year, classname):
    conn = sqlite3.connect("data_base.db")
    cursor = conn.cursor()

    # Fetch student name from all_students table
    cursor.execute("SELECT name FROM all_students WHERE rollno = ? AND dept = ? AND year = ?", (rollno, dept, year))
    student = cursor.fetchone()

    if not student:
        conn.close()
        return {"error": "Student not found."}

    student_name = student[0]

    # Get attendance data
    query = f"""
        SELECT SUM(present) AS total_present_hours, COUNT(DISTINCT date) AS total_days
        FROM {classname}  
        WHERE rollno = ?
    """
    cursor.execute(query, (rollno,))
    result = cursor.fetchone()
    conn.close()

    if not result or result[1] == 0:  # No attendance data found
        return {"name": student_name, "attendance_percentage": 0.0}

    total_present_hours, total_days = result
    total_days-=1
    attendance_percentage = (total_present_hours / (total_days * 8)) * 100 if total_days else 0

    return {
        "name": student_name,
        "attendance_percentage": round(attendance_percentage, 2)
    }


@app.route('/others_report',methods=['GET','POST'])
def others_report():
    attendance_percentage = None
    if request.method == "POST":
        rollno = request.form["rollno"]
        dept = request.form["dept"]
        year = request.form["year"]
        classname = request.form["classname"]

        student_data = get_attendance_percentage(rollno, dept, year, classname)

    conn = sqlite3.connect("data_base.db")
    cursor = conn.cursor()

    cursor.execute("SELECT DISTINCT classname FROM all_classes")  # Change table name if needed
    classes = [row[0] for row in cursor.fetchall()]

    conn.close()
    return render_template('other/report.html',classes=classes,student_data=student_data)


if __name__ == '__main__':
    app.run(debug=True)
