# include-innovation
# Coding Classroom 💻📚

> Platform for both teachers and students where they can share and submit programming (coding) assignments.

### Features:
For teachers
1. Create classrooms.
2. Allow the students to join the classroom (using a class code).
3. Create programming assignments with any number of test cases

For students
1. Join a classroom (using a given class code).
2. View all the assignments in a grid layout.
3. Submit the assignment in any language of choice
   _(currently C, C++, Java and Python but can be extended)_
4. Write your code in a user-friendly code editor which supports syntax highlighting, bracket completion and many visual themes.

### Tools Used
- Flask and Flask-SQLAlchemy
- Bootstrap 4
- Jinja templating
- CodeMirror API (for the code editor.)
- JDoodle API (for the executing the submitted code.)

### Installation
> Make sure you have Python 3.x installed.
```
$ cd include-innovation
$ pip install -r requirements.txt
$ python main.py
```
_(If you get any python or pip not found errors, try using python3 or pip3 instead)_

Using a Python virtual environment is recommended

```
$ python -m venv coding-venv
$ source coding-venv/bin/activate
$ pip install -r requirements.txt
```