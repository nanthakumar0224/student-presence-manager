from flask import Flask, render_template, request,session,send_file
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
    if user_name == "Admin" and password == "123" and userid =="0":
        return render_template("admin/index.html")
    else:
        return "username or password invalid "

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
    in_classteacher = request.form['classteacher']

    in_oldclassname = request.form['oldclassname']
    in_oldclassteacher = request.form['oldclassteacher']
    con = sqlite3.connect('data_base.db')
    cur = con.cursor()
    if in_oldclassname == in_classname and in_oldclassteacher == in_classteacher:
        return "No changes"
    elif in_oldclassname == in_classname and in_oldclassteacher != in_classteacher:
        cur.execute("UPDATE all_classes SET classname= ?, classteacher=? WHERE classid=?",
                    (in_classname, in_classteacher, in_classid))
        con.commit()
        con.close()
        return "Class Teacher Updated Successfully !!"

    elif in_oldclassname != in_classname and in_oldclassteacher == in_classteacher:
        cur.execute("UPDATE all_classes SET classname= ?, classteacher=? WHERE classid=?",
                    (in_classname, in_classteacher, in_classid))

        query = F"ALTER TABLE {in_oldclassname} RENAME TO {in_classname}"
        
        cur.execute(query)
        
        con.commit()
        con.close()
        return "Class Name Updated Successfully !!"
    else:
        cur.execute("UPDATE all_classes SET classname= ?, classteacher=? WHERE classid=?",
                    (in_classname, in_classteacher, in_classid))

        query = F"ALTER TABLE {in_oldclassname} RENAME TO {in_classname}"

        cur.execute(query)
        con.commit()
        con.close()
        return "Class Name and Teacher Name Updated Successfully !!"

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
    query = f"SELECT * FROM {classname} WHERE date = {formatted_date}"
    cur.execute(query)
    data = cur.fetchall()
    if data:
        con.close()
        return "Your attendance closed"
    else:
        query = f"SELECT * FROM all_students WHERE classid = {classid}"
        cur.execute(query)
        data = cur.fetchall()
        
        return render_template("staff/attendance_sheet.html",data = data,classname = classname,classid = classid)


#save attendance
def insert_attendance(student_slno, present, absent, current_date, classname):
    try:
        conn = sqlite3.connect('data_base.db')
        cursor = conn.cursor()

        query = f"""
        INSERT INTO {classname} (rollno, date, present, absent)
        VALUES (?, ?, ?, ?)
        """

        cursor.execute(query, (student_slno, current_date, present, absent))
        conn.commit()
        conn.close()

    except Exception as e:
        print(f"Error inserting attendance: {e}")

@app.route('/save_attendance', methods=['POST'])
def save_attendance():
    current_date = datetime.date.today().strftime('%Y-%m-%d')
    in_classname = request.form['classname']  
    processed_students = set()  

    for slno in request.form:
        if slno.startswith('p'):  
            try:
                student_slno = slno.split('_')[1] 
                student_slno = int(student_slno)  

               
                if student_slno in processed_students:
                    continue

                present = 0
                absent = 0

              
                for period in range(1, 9):
                  
                    if f'p{period}_{student_slno}' in request.form:
                        present += 1 
                    else:
                        absent += 1 

                insert_attendance(student_slno, present, absent, current_date, in_classname)
              
                processed_students.add(student_slno)

            except IndexError:
                print(f"Error processing attendance for form field: {slno}")
                continue

    return "Attendance updated successfully!"

#----------------------------------------------------------------------------------------------------#



#---------------------------report generation------------------------------------------------------------------#

@app.route('/report_generate_form')
def report_generate_form():
    return render_template("report_generate_form.html")


# add the after search report form procss

#------------------------------------------------------------------------------------------------------------------#

if (__name__ == '__main__'):
    app.run()
