from flask import Flask, jsonify, request,send_file,abort
import os
from datetime import datetime
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