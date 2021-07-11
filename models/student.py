from models.database import db

students = db.Table("students",
    db.Column("student_id", db.Integer, db.ForeignKey("student.id")),
    db.Column("classroom_id", db.Integer, db.ForeignKey("classroom.id"))
)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_type = db.Column(db.String(10), nullable=False)

    name = db.Column(db.String(40), nullable=False)

    email = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(64), nullable=False)

    classrooms = db.relationship("Classroom", secondary=students, backref=db.backref("students", lazy=True))
    submissions = db.relationship("Submission", backref="student", lazy=True)

    def __init__(self, name, email, password) -> None:
        super().__init__()
        self.user_type = "student"

        self.name = name
        self.email = email
        self.password = password
