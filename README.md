# College Management System

A Flask-based College ERP, built in phases as a college project.

**Status: Phase 2 complete** (project setup, full database schema,
authentication, student & teacher management).

## Tech stack

Python 3.11+, Flask, SQLAlchemy, SQLite, Flask-Login, Jinja2, vanilla
CSS/JS. Chart.js will be added when the dashboard gets real charts
(Phase 7).

## Installation

```bash
cd college_management
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Set up the database and demo data

```bash
python seed.py
```

This drops any existing tables, recreates them from the models, and
inserts one demo user per role.

## Run the app

```bash
python run.py
```

Visit http://127.0.0.1:5000 — you'll be redirected to the login page.

## Demo credentials

| Role    | Email                | Password    |
|---------|----------------------|-------------|
| Admin   | admin@college.edu    | admin123    |
| Teacher | teacher@college.edu  | teacher123  |
| Student | student@college.edu  | student123  |

`seed.py` also creates a second teacher (`teacher2@college.edu`) and a
second student (`student2@college.edu`, same password pattern) in a
different department/course, so search and filter have more than one
option to actually filter between.

## Running tests

```bash
pip install pytest
pytest
```

## Folder structure

```
college_management/
├── app/
│   ├── __init__.py        # application factory
│   ├── models/            # one file per database table
│   ├── routes/             # auth.py, main.py, students.py, teachers.py
│   ├── templates/          # Jinja2 HTML
│   ├── static/css/js       # styling and front-end scripts
│   └── utils/decorators.py # role_required() access-control decorator
├── tests/                  # pytest tests
├── instance/                # college.db (SQLite file) lives here
├── config.py
├── run.py
├── seed.py
└── requirements.txt
```

## Database schema (Phase 1)

All 15 tables from the spec are defined as SQLAlchemy models:
`User`, `Student`, `Teacher`, `Department`, `Course`, `Semester`,
`Section`, `Subject`, `Enrollment`, `Attendance`, `Examination`,
`Marks`, `Fee`, `Payment`, `Notice`.

Design notes:

- **User vs. Student/Teacher**: login credentials (email, password
  hash, role) live on `User`. Personal/academic data lives on `Student`
  or `Teacher`, linked back with a one-to-one `user_id` foreign key.
  This keeps "how do I log in" completely separate from "who am I".
- **Course → Semester → Section**: a `Course` (e.g. B.Tech CSE) has
  many `Semester`s (1 through 8), and each `Semester` has `Section`s
  (A, B...). A `Student` belongs to one `Section` at a time.
- **Subject → Examination → Marks**: a `Subject` belongs to a
  `Semester` and has one assigned `Teacher`. Each `Subject` can have
  several `Examination`s (Internal, Mid-Term, Final...). `Marks` links
  one `Student` to one `Examination`.
- **Fee → Payment**: a `Fee` is a billing record (e.g. "Semester 3
  Fees", ₹60,000 total). Every `Payment` against it is stored as its
  own row, so `Fee.paid_amount()` / `pending_amount()` are computed by
  summing payments rather than storing a number that could drift out
  of sync.
- **Enrollment** is a join table connecting `Student` and `Subject`
  (many-to-many): one student takes many subjects, one subject has
  many students.

## Authentication & authorization

- Passwords are hashed with Werkzeug's `generate_password_hash` /
  `check_password_hash` (salted, never stored in plain text).
- Flask-Login manages the session (`login_user`, `logout_user`,
  `@login_required`).
- Role checks happen on the **server**, via the `@role_required(...)`
  decorator in `app/utils/decorators.py` — not just by hiding buttons
  in templates. Visiting a URL directly without the right role returns
  a 403, it doesn't just look wrong in the UI.
- There is no public registration page. Accounts are created by the
  admin (Phase 2) or, for now, by `seed.py`.

## Student & teacher management (Phase 2)

- Admin-only CRUD for both `Student` and `Teacher`, at
  `/admin/students` and `/admin/teachers`. Every route is protected by
  both `@login_required` and `@role_required("admin")` — a teacher or
  student who guesses the URL gets a 403, not just a hidden nav link.
- Adding a student/teacher creates their `User` (login) row and their
  profile row (`Student`/`Teacher`) together, in one transaction, so
  you never end up with a login that has no profile or vice versa.
- Search (by name/roll number/employee code) and filters (course,
  semester, section, department, active/inactive) are combined as
  SQLAlchemy query filters — see `list_students()` /
  `list_teachers()` in the route files.
- The student form's Course → Semester → Section dropdowns are
  cascading: picking a course repopulates the semester list with only
  that course's semesters, and picking a semester does the same for
  sections. The data comes from the database (`_course_choices()` in
  `students.py`), rendered to JSON and read by
  `initCascadingDropdowns()` in `static/js/main.js` — the same helper
  will be reused for the attendance page in Phase 4 (Course → Semester
  → Section → Subject → Date).
- Deactivating a student/teacher sets both the profile's own "active"
  flag AND `User.is_active_account` to false, which immediately blocks
  that person from logging in (Flask-Login checks `User.is_active`).
- A teacher's profile page has an "Assigned subjects" section that's
  empty for now — subject assignment needs `Subject` records to exist,
  which is a Phase 3 concern (Courses + Subjects + Enrollment).

## What to manually verify

1. Run `python seed.py`, then `python run.py`.
2. Log in as each of the three demo accounts and confirm you land on
   a different dashboard page for each role.
3. Try a wrong password — you should see "Invalid email or password."
4. Log out, then try visiting `http://127.0.0.1:5000/` directly — you
   should be redirected to `/auth/login`.
5. Visit a made-up URL like `/does-not-exist` — you should see the
   custom 404 page, not a stack trace.
6. As admin, open **Students**: search by name/roll number, filter by
   course/semester/section/status, add a new student, edit one, and
   deactivate one (then confirm that student can no longer log in).
7. Do the same for **Teachers** (add/edit/deactivate, search, filter
   by department).
8. Log in as the teacher or student demo account and try visiting
   `/admin/students/` directly in the browser — you should get a 403
   page, not the student list.
9. Run `pytest` — all 15 tests should pass.

## Future improvements (tracked, not yet built)

Phase 3 onward: courses/subjects/enrollment (including teacher subject
assignment), attendance, exams/marks, fees/payments, dashboard
analytics with Chart.js, reports with CSV export, notices, and a fuller
test suite.