from flask import Flask, jsonify
# flask me kam kar rhe hain. json bhi use hoga.

from flask_sqlalchemy import SQLAlchemy
#isse sqlite / postgres me work karenge.

app = Flask(__name__)
# flask application framework ka object bana

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

    # app id and name do
    #yeh javascript object return karega.
    def to_dict(self):
        return {
            "id": self.id,
            "sname": self.sname
        }
#=======================================

#=======================================
# Create Student
#is url se match ko request aaye to neeche ka function run karo
@app.route("/create_student/<int:id>/<string:sname>", methods=["POST"])
def create_student(id, sname):

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
        sname=sname
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
#code to run
# agar yeh file run hogi
if __name__ == "__main__":
    #flask app ka env and settings active karenge
    with app.app_context():
        #fir sab tables / default tables ko banayenge. Agar koi default object hai, toh use initialize karenge or db me store karenge.
        db.create_all()

    #agar app run hogi to uska logs bhi banana padega server side.
    app.run(debug=True)
#=======================================