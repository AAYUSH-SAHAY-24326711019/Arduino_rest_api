from flask import Flask, Response, jsonify, request,send_file,abort,render_template
import os
from datetime import datetime, timedelta
from utility import qrgen
import csv
import io

# flask me kam kar rhe hain. json bhi use hoga.

from flask_sqlalchemy import SQLAlchemy
#isse sqlite / postgres me work karenge.

# app = Flask(__name__)
app = Flask(__name__,instance_relative_config=True)
# flask application framework ka object bana
#ab ap instance folder ka components ko use kar sakte hain.

#sqlite ka code
app.config["SQLALCHEMY_DATABASE_URI"]="sqlite:///students.db"
#database location ki setting :SQLALCHEMY_DATABASE_URI
#database ka address bata rahe hain.
#/current url ka slash (1st slash)
#/current application folder (2nd slash)
#/stduents folder ka slash
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
#default sqlite objects ki changes ko track karta hai. isse yeh off hoga.
#memory ko save karna hai, render 512 mb Ram isiliye.

db = SQLAlchemy(app)
#isse ham database ko flask app se conntect karenge.

@app.route("/") #test karne ke liye
def home():
    return render_template("render_main_page.html")

#=======================================
# student ki class 
#isse sqlalchemy ko pata chalega ki iski table sqlite me banana hai.
class Student(db.Model):
    #id or name hona chahiye.

    id = db.Column(db.Integer, primary_key=True)

    sname = db.Column(db.String(100), nullable=False)

    #/* All new fields added to the database table
    sroll = db.Column(db.String(30),nullable=True)
    semail = db.Column(db.String(5),nullable=True)
    scourse = db.Column(db.String(30),nullable=True)
    ssession_start = db.Column(db.String(5),nullable=False)
    ssession_end = db.Column(db.String(5),nullable=False)
    #*/

    # app id and name do
    #yeh javascript object return karega.
    def to_dict(self):
        return {
            "id": self.id,
            "sname": self.sname,
            "sroll":self.sroll,
            "semail":self.semail,
            "scourse":self.scourse,
            "ssession_start":self.ssession_start,
            "ssession_end":self.ssession_end
        }
#=======================================

#=======================================
# Create Student
#is url se match ko request aaye to neeche ka function run karo
# @app.route("/create_student/<int:id>/<string:sname>", methods=["POST"])
@app.route("/create_student/<int:id>/<string:sname>/<string:sroll>/<string:semail>/<string:scourse>/<string:ssession_start>/<string:ssession_end>", methods=["POST"])
def create_student(id, sname,sroll,semail,scourse,ssession_start,ssession_end):

    #object lo id ke basis par, yadi db me present ho
    existing_student = Student.query.get(id)

    #yadi koi value aaiye to hame yeh json msg error wali deni hai
    if existing_student:
        return jsonify({
            "message": "Student already exists"
        }), 400

    #agar id nahi exist ki ho toh
    #student ka object banana hai
    student = Student(
        id=id,
        sname=sname,
        sroll=sroll,
        semail=semail,
        scourse=scourse,
        ssession_start=ssession_start,
        ssession_end=ssession_end

    )

    #database me store karna hai
    #yeh pending / rough list hai
    db.session.add(student)
    #is line se rough list ko fair kiya.
    db.session.commit()

    #db me save hua toh msg dena hai as json.
    return jsonify({
        "message": "Student created successfully",
        "student": student.to_dict()
    })

#=======================================

#=======================================
# Get Student by id check
@app.route("/get_student/<int:id>", methods=["GET"])
def get_student(id):

    #get the student by id if exists
    student = Student.query.get(id)

    #case : student id provided not present.
    if not student:
        return jsonify({
            "message": "Student not found"
        }), 404

    #case the student was present. toh make the object to dictionary / json by class ka method [to_dict()] then jsonify that.
    return jsonify(student.to_dict())

#=======================================

#=======================================
# Get All Students
@app.route("/all", methods=["GET"])
def get_all_students():

    students = Student.query.all()

    return jsonify(
        [student.to_dict() for student in students]
    )
#=======================================

#=======================================
#Render does not store / persist changes
# to database state then to download the
#latest db .sqlite file.

@app.get("/db")
def download_db():
    #path chahiye db ka
    db_path = os.path.join(app.instance_path,"students.db")

    #agar nahi mila to
    if not os.path.exists(db_path):
        abort(404,description="Database file not found")

    #mila toh download hoga.
    #time kya hai
    now = datetime.now()
    return send_file(db_path,
                     mimetype="application/x-sqlite3",
                     as_attachment=True,
                     download_name=f"students{now.strftime("%d/%m/%Y, %H:%M:%S")}.db")

#=======================================

#=======================================
# attendance ka table add kiye
class Attendance(db.Model):

    __tablename__ = "attendance"

    id = db.Column(db.Integer, primary_key=True)

    sroll = db.Column(db.String(30), nullable=False)

    sname = db.Column(db.String(100), nullable=False)

    course = db.Column(db.String(30), nullable=True)

    session = db.Column(db.String(20), nullable=False)

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    def to_dict(self):
        return {
            "id": self.id,
            "sroll": self.sroll,
            "sname": self.sname,
            "course": self.course,
            "session": self.session,
            "created_at": self.created_at.isoformat()
        }

#=======================================

#=======================================
#to mark attendance
@app.route("/attendance", methods=["POST"])
def mark_attendance():

    data = request.get_json()

    rolls = data.get("students", [])

    saved_records = []

    for roll in rolls:

        student = Student.query.filter_by(
            sroll=str(roll)
        ).first()

        if not student:
            continue

        attendance = Attendance(
            sroll=student.sroll,
            sname=student.sname,
            course=student.scourse,
            session=f"{student.ssession_start}-{student.ssession_end}"
        )

        db.session.add(attendance)

        saved_records.append(attendance)

    db.session.commit()

    return jsonify({
        "message": "Attendance saved",
        "count": len(saved_records)
    })
#=======================================

#=======================================
#get attendance api
@app.route("/getattendance", methods=["GET"])
def get_attendance():

    attendance_records = Attendance.query.all()

    return jsonify(
        [record.to_dict() for record in attendance_records]
    )

#=======================================

#=======================================
# csv banane ka common helper
# taaki teeno api me code repeat na ho.
def _attendance_to_csv_response(records, filename):

    output = io.StringIO()
    writer = csv.writer(output)

    #header row
    writer.writerow(
        ["id", "sroll", "sname", "course", "session", "created_at"]
    )

    #data rows
    for r in records:
        writer.writerow([
            r.id,
            r.sroll,
            r.sname,
            r.course,
            r.session,
            r.created_at.isoformat()
        ])

    csv_data = output.getvalue()

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )

# DDMMYY string ko datetime me convert karega
# invalid format pe ValueError khud raise ho jayega.
def _parse_ddmmyy(date_str):
    return datetime.strptime(date_str, "%d%m%y")

#=======================================

#=======================================
# saari attendance ab tak ki, csv me download
@app.route("/downloadattendance", methods=["GET"])
def download_attendance_csv():

    records = Attendance.query.order_by(Attendance.created_at.asc()).all()

    now = datetime.now()

    return _attendance_to_csv_response(
        records,
        f"attendance_all_{now.strftime('%d%m%y')}.csv"
    )

#=======================================

#=======================================
# date range wali attendance, csv me
# eg /getBD/120726/130726  -> 12 July 2026 se 13 July 2026 tak
@app.route("/getBD/<string:startdate>/<string:enddate>", methods=["GET"])
def get_attendance_by_date(startdate, enddate):

    try:
        start_dt = _parse_ddmmyy(startdate)
        # enddate wale din ka pura din cover karne ke liye
        # agla din 00:00:00 se pehle tak ki range lenge.
        end_dt = _parse_ddmmyy(enddate) + timedelta(days=1)
    except ValueError:
        return jsonify({
            "message": "Invalid date format. Use DDMMYY, e.g. 120726"
        }), 400

    if start_dt > end_dt:
        return jsonify({
            "message": "startdate cannot be after enddate"
        }), 400

    records = Attendance.query.filter(
        Attendance.created_at >= start_dt,
        Attendance.created_at < end_dt
    ).order_by(Attendance.created_at.asc()).all()

    return _attendance_to_csv_response(
        records,
        f"attendance_{startdate}_to_{enddate}.csv"
    )

#=======================================

#=======================================
# same as above, course ke basis par bhi filter
# eg /getBD/120726/130726/BCA
@app.route("/getBD/<string:startdate>/<string:enddate>/<string:course>", methods=["GET"])
def get_attendance_by_date_and_course(startdate, enddate, course):

    try:
        start_dt = _parse_ddmmyy(startdate)
        end_dt = _parse_ddmmyy(enddate) + timedelta(days=1)
    except ValueError:
        return jsonify({
            "message": "Invalid date format. Use DDMMYY, e.g. 120726"
        }), 400

    if start_dt > end_dt:
        return jsonify({
            "message": "startdate cannot be after enddate"
        }), 400

    records = Attendance.query.filter(
        Attendance.created_at >= start_dt,
        Attendance.created_at < end_dt,
        Attendance.course == course
    ).order_by(Attendance.created_at.asc()).all()

    return _attendance_to_csv_response(
        records,
        f"attendance_{course}_{startdate}_to_{enddate}.csv"
    )

#=======================================
#Qr code generate karne ka route
@app.route("/qrpage")
def qr_page():

    students = Student.query.all()

    grouped = {}

    for student in students:

        session = (
            f"{student.ssession_start}"
            f"-"
            f"{student.ssession_end}"
        )

        key = f"{student.scourse}|{session}"

        student.qr = qrgen.generate_qr(student)

        grouped.setdefault(
            key,
            []
        ).append(student)

    return render_template(
        "qr_page.html",
        grouped=grouped
    )
#=======================================


#=======================================
# qr code scan karne ke bad attendance ka end point
@app.route(
    "/attendance/scan",
    methods=["POST"]
)
def attendance_scan():

    data = request.get_json()

    roll = data.get("roll")

    student = Student.query.filter_by(
        sroll=roll
    ).first()

    if not student:
        return jsonify({
            "message":"Student not found"
        }),404

    attendance = Attendance(
        sroll=student.sroll,
        sname=student.sname,
        course=student.scourse,
        session=f"{student.ssession_start}-{student.ssession_end}"
    )

    db.session.add(attendance)
    db.session.commit()

    return jsonify({
        "message":"Attendance Marked"
    })

#=======================================

#=======================================
#code to run
with app.app_context():
        #fir sab tables / default tables ko banayenge. Agar koi default object hai, toh use initialize karenge or db me store karenge.
        db.create_all()
# agar yeh file run hogi
if __name__ == "__main__":
    #flask app ka env and settings active karenge
    #agar app run hogi to uska logs bhi banana padega server side.
    app.run(debug=True)
#=======================================