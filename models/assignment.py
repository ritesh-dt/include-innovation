from models.database import db
from datetime import datetime

def create_assignment_code():
    from string import ascii_letters
    from random import choice
    code = ""
    while True:
        code = ""
        for letter in range(5):
            code = code + choice(ascii_letters)
        if Assignment.query.filter_by(code=code).first() is None:
            break

    return code

class Assignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(40), nullable=False)
    description = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(5), nullable=False)

    input_format = db.Column(db.String(100), nullable=False)
    output_format = db.Column(db.String(100), nullable=False)

    input_cases = db.Column(db.String(100), nullable=False)
    output_cases = db.Column(db.String(100), nullable=False)

    constraints = db.Column(db.String(100), nullable=False)
    deadline = db.Column(db.DateTime, nullable=False)

    classroom_id = db.Column(db.Integer, db.ForeignKey("classroom.id"))
    submissions = db.relationship("Submission", backref="assignment", lazy=True)

    def __init__(self, name, description, deadline, classroom) -> None:
        super().__init__()

        self.name = name
        self.description = description
        self.code = create_assignment_code()
        self.classroom = classroom
        self.deadline = datetime.strptime(deadline, "%Y-%m-%dT%H:%M")

