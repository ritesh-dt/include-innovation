from flask import Flask
from flask import render_template,request,redirect,url_for,flash,session

# Database and Models
from models.database import db
from models.student import Student
from models.teacher import Teacher
from models.classroom import Classroom

app = Flask(__name__)
app.secret_key = "WCEHACKATHON"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///data.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

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
            return redirect(url_for("home"))
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
            return redirect(url_for("home"))
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
        if user_type is not None and session.get("user_type") == user_type:
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


if __name__ == "__main__":
    app.run(debug=True)

