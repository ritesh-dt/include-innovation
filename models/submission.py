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

class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    file_name = db.Column(db.String(40), nullable=False)
    results = db.Column(db.String(80), nullable=False)
    language = db.Column(db.String(40), nullable=False)

    assignment_id = db.Column(db.Integer, db.ForeignKey("assignment.id"))
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"))

    def __init__(self, file_name, results, language, assignment, student) -> None:
        super().__init__()

        self.file_name = file_name
        self.results = results
        self.language = language
        self.assignment = assignment
        self.student = student
