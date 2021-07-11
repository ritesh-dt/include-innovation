from flask import Flask
from flask import render_template,request,redirect,url_for,flash,session

from datetime import datetime
import os, json

from flask.helpers import send_file

# Database and Models
from models.database import db
from models.student import Student
from models.teacher import Teacher
from models.classroom import Classroom
from models.assignment import Assignment
from models.submission import Submission

app = Flask(__name__)
app.secret_key = "WCEHACKATHON"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///data.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
UPLOAD_FOLDER = "submissions"

# Initialize database
with app.app_context():
    db.init_app(app)
    # db.drop_all()
    # db.create_all()

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method=="GET":
        return redirect(url_for("home"))
    email=request.form.get("email")
    password=request.form.get("password")

    user = GetUser(email)
    if isinstance(user, Student) or isinstance(user, Teacher) :
        if user.password == password:
            session["name"] = user.name
            session["email"] = user.email
            session["user_type"] = user.user_type

            flash(f"Login Successful !", "success")
            return redirect(url_for("dashboard"))
        else:
            flash(f"Invalid Password !", "danger")
            return redirect(url_for("home"))

    else:
        return user

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method=="GET":
        return redirect(url_for("home"))

    email=request.form.get("email")
    user_type=request.form.get("user_type")
    name=request.form.get("name")
    password=request.form.get("password")
    verify_password=request.form.get("verify_password")

    user = GetUser(email)
    if isinstance(user, Student) or isinstance(user, Teacher) :
        flash(f"User with email {email} already exists!", "danger")
        return redirect(url_for("home"))
    else:
        if verify_password == password:
            if user_type =="student":
                user = Student(name,email,password)
            if user_type =="teacher":
                user = Teacher(name,email,password)
            db.session.add(user)
            db.session.commit()

            session["name"] = user.name
            session["email"] = user.email
            session["user_type"] = user.user_type

            flash("Registered successfully!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash(f"Invalid Password !", "danger")
            return redirect(url_for("home"))


@app.route("/logout", methods=["GET", "POST"])
def logout():
    if request.method=="GET":
        return redirect(url_for("home"))

    del session["name"]
    del session["email"]
    del session["user_type"]

    flash(f"Logout Successful !", "success")
    return redirect(url_for("home"))

def AuthorizeUser(user_type=None):
    is_authorized = False

    if session.get("name") is not None and session.get("email") is not None:
        if user_type is None or session.get("user_type") == user_type:
            is_authorized = True

    return is_authorized

def GetUser(email):
    user = None
    user = Student.query.filter_by(email=email).first()

    if user:
        return user

    user = Teacher.query.filter_by(email=email).first()
    if user:
        return user

    flash(f"No such user with email {email}!", "danger")
    return redirect(url_for("home"))


# Classroom Management
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    is_authorized = AuthorizeUser("teacher")
    if is_authorized:
        user = GetUser(session["email"])
        classes = []
        for classroom in user.classrooms:
            print(classroom.name)
            classes.append({
                "name": classroom.name,
                "desc": classroom.description,
                "code": classroom.code,
                "assignment": None
            })

        return render_template("teacher_dashboard.html", classes=classes)

    is_authorized = AuthorizeUser("student")

    if is_authorized:
        user = GetUser(session["email"])
        if request.method == "POST":
            class_code = request.form.get("class_code")

            classroom = Classroom.query.filter_by(code=class_code).first()
            if classroom:
                if classroom not in user.classrooms:
                    user.classrooms.append(classroom)
                    db.session.add(user)
                    db.session.commit()

                    flash(f"Joined classroom successfully!", "success")

            else:
                flash(f"No classroom found with code {class_code}!", "danger")

        classes = []
        for classroom in user.classrooms:
            classes.append({
                "name": classroom.name,
                "desc": classroom.description,
                "code": classroom.code,
                "assignment": None
            })

        return render_template("student_dashboard.html", classes=classes)

    return flash(f"Please login first!", "danger")

@app.route("/classroom/create", methods=["GET", "POST"])
def ClassroomCreate():
    if request.method == "GET":
        return render_template("classroom_create.html")

    is_teacher = AuthorizeUser("teacher")
    if not is_teacher:
        flash(f"Permission denied!", "danger")
        return redirect(url_for("home"))

    name = request.form.get("class_name")
    description = request.form.get("class_desc")

    user = GetUser(session["email"])

    new_classroom = Classroom(name, description, teacher=user)
    db.session.add(new_classroom)
    db.session.commit()

    flash(f"Classroom {name} created successfully!", "success")

    return redirect(url_for("dashboard"))


@app.route("/classroom/<class_code>", methods=["GET"])
def ClassroomMain(class_code):
    is_authorized = AuthorizeUser()
    if not is_authorized:
        flash("Permission denied!", "danger")
        return redirect(url_for("home"))

    classroom = Classroom.query.filter_by(code=class_code).first()
    if not classroom:
        flash("Classroom does not exist!", "danger")
        return redirect(url_for("dashboard"))

    user = GetUser(session["email"])
    if classroom not in user.classrooms:
        flash("Permission denied to class!", "danger")
        return redirect(url_for("dashboard"))

    assignments = Assignment.query.filter_by().first()

    return render_template("classroom_main.html", classroom=classroom, assignments=classroom.assignments, current_time=datetime.now, strftime=lambda x: x.strftime("%a, %d %b %Y at %I:%M %p"))

@app.route("/assignment/<assignment_code>/edit", methods=["GET", "POST"])
def AssignmentEdit(assignment_code):
    is_teacher = AuthorizeUser("teacher")
    if not is_teacher:
        flash(f"Permission denied!", "danger")
        return redirect(url_for("home"))

    assignment = Assignment.query.filter_by(code=assignment_code).first()
    if not assignment:
        flash(f"Assignment not found!", "warning")
        return redirect(url_for("dashboard"))


    if request.method == "GET":
        return render_template("assignment_edit.html", assignment=assignment)
    else:

        classroom = Classroom.query.filter_by(code=assignment.classroom.code).first()

        user = GetUser(session["email"])
        if classroom not in user.classrooms:
            flash("Permission denied!", "danger")
            return redirect(url_for("dashboard"))

        name = request.form.get("assignment_name")
        description = request.form.get("assignment_desc")
        input_format = request.form.get("assignment_input_format")
        output_format = request.form.get("assignment_output_format")

        input_cases = []
        for k in request.form.keys():
            if "assignment_input_case" in k:
                input_cases.append(request.form.get(k))
        input_cases = "----".join(str(x) for x in input_cases if x)

        output_cases = []
        for k in request.form.keys():
            if "assignment_output_case" in k:
                output_cases.append(request.form.get(k))
        output_cases = "----".join(str(x) for x in output_cases if x)

        constraints = request.form.get("assignment_constraints")
        deadline = request.form.get("assignment_deadline")

        assignment.name = name
        assignment.description = description
        assignment.deadline = deadline
        assignment.classroom = classroom
        assignment.input_format = input_format
        assignment.output_format = output_format
        assignment.input_cases = input_cases
        assignment.output_cases = output_cases
        assignment.constraints = constraints
        db.session.commit()


        # Update submissions
        submissions = Submission.query.filter_by(assignment=assignment, student=student)

        submitted = False
        for submission in submissions:
            submission_file = open(submission.file_name, "r")
            code = submission_file.read()
            submission_file.close()
            results = json.loads(SubmissionCheck(code, submission.language, assignment_code=assignment.code))
            submission.results = "".join(["1" if test_case["solved"] else "0" for test_case in results["test_cases"]])
            db.session.commit()

        assignment_folder = f"{UPLOAD_FOLDER}/{assignment.code}/"
        if not os.path.exists(assignment_folder):
            os.mkdir(assignment_folder)

        flash("Assignment edited successfully!", "success")
        return redirect(f"/classroom/{classroom.code}")


@app.route("/classroom/<class_code>/assignment/create", methods=["GET", "POST"])
def AssignmentCreate(class_code):
    is_authorized = AuthorizeUser("teacher")
    if not is_authorized:
        flash("Permission denied!", "danger")
        return redirect(url_for("home"))

    if request.method == "GET":
        session["class_code"] = class_code
        return render_template("assignment_create.html")
    else:
        print(class_code)
        classroom = Classroom.query.filter_by(code=class_code).first()
        print(classroom)
        if not classroom:
            flash("Classroom does not exist!", "danger")
            return redirect(url_for("dashboard"))

        user = GetUser(session["email"])
        if classroom not in user.classrooms:
            flash("Permission denied!", "danger")
            return redirect(url_for("dashboard"))

        name = request.form.get("assignment_name")
        description = request.form.get("assignment_desc")
        input_format = request.form.get("assignment_input_format")
        output_format = request.form.get("assignment_output_format")

        input_cases = []
        for k in request.form.keys():
            if "assignment_input_case" in k:
                input_cases.append(request.form.get(k))
        input_cases = "----".join(str(x) for x in input_cases if x)

        output_cases = []
        for k in request.form.keys():
            if "assignment_output_case" in k:
                output_cases.append(request.form.get(k))
        output_cases = "----".join(str(x) for x in output_cases if x)

        constraints = request.form.get("assignment_constraints")
        deadline = request.form.get("assignment_deadline")

        new_assignment = Assignment(name, description, deadline, classroom)
        new_assignment.input_format = input_format
        new_assignment.output_format = output_format
        new_assignment.input_cases = input_cases
        new_assignment.output_cases = output_cases
        new_assignment.constraints = constraints

        assignment_folder = f"{UPLOAD_FOLDER}/{new_assignment.code}/"
        if not os.path.exists(assignment_folder):
            os.mkdir(assignment_folder)

        db.session.add(new_assignment)
        db.session.commit()

        flash("Assignment created successfully!", "success")
        return redirect(f"/classroom/{class_code}")

@app.route("/assignment/<assignment_code>", methods=["GET", "POST"])
def AssignmentMain(assignment_code):
    is_authorized = AuthorizeUser()
    if not is_authorized:
        flash("Permission denied!", "danger")
        return redirect(url_for("home"))

    assignment = Assignment.query.filter_by(code=assignment_code).first()
    print(assignment)
    if not assignment:
        flash("Assignment not found!", "danger")
        return redirect(url_for("dashboard"))

    user = GetUser(session["email"])
    file_names = [f"{UPLOAD_FOLDER}/{assignment_code}/{user.id}-{idx+1}.txt" for idx in range(3)]

    submissions = []
    for file_name in file_names:
        submission = Submission.query.filter_by(file_name=file_name).first()
        if submission:
            submissions.append(submission)
        else:
            submissions.append(None)
    print(submissions)

    submission_id = request.args.get("view")
    if submission_id:
        submission = Submission.query.filter_by(id=submission_id).first()
        if not submission in user.submissions:
            flash("Permission denied", "danger")
            submission_id = None


    submission_program = ""
    if submission_id:
        code_file = open(submission.file_name, "r")
        submission_program = code_file.read()
    else:
        for submission in submissions:
            if submission:
                code_file = open(submission.file_name, "r")
                submission_program = code_file.read()
                break

    if request.method == "GET":
        return render_template("assignment_main.html", assignment=assignment, current_time=datetime.now, strftime=lambda x: x.strftime("%a, %d %b %Y at %I:%M %p"), submission_program=submission_program, submissions=submissions)
    else:
        code = request.form.get("code")
        language = request.form.get("language")
        assignment_code = request.form.get("assignment_code")

        if not os.path.exists(f"{UPLOAD_FOLDER}/{assignment_code}/"):
            os.mkdir(f"{UPLOAD_FOLDER}/{assignment_code}/")

        results = json.loads(SubmissionCheck(code, language, assignment_code))
        results = "".join(["1" if test_case["solved"] else "0" for test_case in results["test_cases"]])

        new_file_name = f"{UPLOAD_FOLDER}/{assignment_code}/{user.id}-1.txt"
        new_submission = Submission(new_file_name, results, language, assignment, user)

        if submissions[-1]:
            submission = submissions.pop(-1)
            os.remove(submission.file_name)
            db.session.delete(submission)
            db.session.commit()

        for submission in reversed(submissions):
            if submission:
                current_name = submission.file_name
                idx = int(current_name.split(".txt")[0][-1])
                new_name = f"{UPLOAD_FOLDER}/{assignment_code}/{user.id}-{idx+1}.txt"

                os.rename(current_name, new_name)
                submission.file_name = new_name
                db.session.commit()

        submissions.append(new_submission)
        new_file = open(new_file_name, "w+")
        for line in code.split("\n"):
            new_file.write(line)

        db.session.add(new_submission)
        db.session.commit()

        flash("Assignment submitted!", "success")
        return redirect(url_for("AssignmentMain", assignment_code=assignment_code))



# Code checking Module
@app.route("/check", methods=["POST"])
def check():
    code = request.json.get("code")
    language = request.json.get("language")
    assignment_code = request.json.get("assignment_code")

    return SubmissionCheck(code, language, assignment_code)

def SubmissionCheck(code, language, assignment_code):
    supported_languages = {
        "C (GCC 5.3.0)": "c",
        "C (GCC 9.1.0)": "c",
        "C++": "cpp",
        "C++14": "cpp14",
        "C++17": "cpp17",
        "Java (JDK 11.0.4)": "java",
        "Python 2 (2.7.16)": "python2",
        "Python 3 (3.7.4)": "python3"
    }
    versionIds = {
        "C (GCC 5.3.0)": "0",
        "C (GCC 9.1.0)": "4",
        "C++": "4",
        "C++14": "3",
        "C++17": "0",
        "Java (JDK 11.0.4)": "3",
        "Python 2 (2.7.16)": "2",
        "Python 3 (3.7.4)": "3"
    }

    assignment = Assignment.query.filter_by(code=assignment_code).first()
    if not assignment:
        return json.dumps("No assignment found in database!")

    input_cases = assignment.input_cases.split("----")
    output_cases = assignment.output_cases.split("----")

    results = {
        "result": 0,
        "test_cases": []
    }

    import requests

    url = "https://api.jdoodle.com/v1/execute"
    body = {
        "clientId": "2ce11d64a18b40825e71eb25cba1e7be",
        "clientSecret": "***REMOVED***",
        "script": code,
        "language": supported_languages[language],
        "stdin": "",
        "versionIndex": versionIds[language]
    }

    headers = {
        "Content-Type": "application/json"
    }


    for idx in range(len(input_cases)):
        stdin = input_cases[idx]
        stdout = output_cases[idx]

        body["stdin"] = stdin

        response = requests.post(url, json=body, headers=headers)
        response = response.json()

        if response["statusCode"] == 200:
            print(response["output"], stdout)
            if check_output(response["output"], stdout):
                results["test_cases"].append({
                    "solved": True,
                    "output": response["output"]
                })
                results["result"] += 1
            else:
                results["test_cases"].append({
                    "solved": False,
                    "output": response["output"]
                })
        elif response["statusCode"] == 400:
            print(response["error"])
            results["test_cases"].append({
                "solved": False,
                "output": response["error"]
            })
        else:
            print(response)

    return json.dumps(results)

def check_output(output, output_test_case):
    output_values = []
    for line in output.strip().split("\n"):
        if not line:
            continue
        for value in line.split(" "):
            try:
                float(value)
                output_values.append(float(value))
            except ValueError:
                output_values.append(value)

    expected_values = []
    for line in output_test_case.strip().split("\n"):
        if not line:
            continue
        for value in line.split(" "):
            try:
                float(value)
                expected_values.append(float(value))
            except ValueError:
                expected_values.append(value)

    for val1, val2 in zip(output_values, expected_values):
        if not val1 == val2 and not str(val1) == str(val2):
            return False

    return True

@app.route("/assignment/<assignment_code>/results", methods=["GET"])
def AssignmentResults(assignment_code):
    is_teacher = AuthorizeUser("teacher")
    if not is_teacher:
        flash(f"Permission denied!", "danger")
        return redirect(url_for("home"))

    assignment = Assignment.query.filter_by(code=assignment_code).first()
    if not assignment:
        flash(f"Assignment not found!", "warning")
        return redirect(url_for("dashboard"))



    csv_data = "Sr No., Name, Classroom, Assignment, Results\n"
    submissions = Submission.query.filter_by(assignment=assignment)
    idx = 1

    for student in assignment.classroom.students:
        submissions = Submission.query.filter_by(assignment=assignment, student=student)

        submitted = False
        for submission in submissions:
            if submission.student == student and submission.file_name.split(".txt")[0][-1] == "1":
                csv_data += f"{idx}, {submission.student.name}, {submission.assignment.classroom.name}, {submission.assignment.name}, {submission.results}\n"
                idx += 1
                submitted = True
                break
        if not submitted:
            csv_data += f"{idx}, {submission.student.name}, {submission.assignment.classroom.name}, {submission.assignment.name}, Not submitted\n"

    results_file = open(f"{UPLOAD_FOLDER}/{assignment_code}/results.csv", "w+")
    results_file.write(csv_data)
    results_file.close()

    return send_file(f"{UPLOAD_FOLDER}/{assignment_code}/results.csv", as_attachment=True, download_name=f"{submission.assignment.classroom.name} - {submission.assignment.name}.csv")

if __name__ == "__main__":
    app.run(debug=True)

