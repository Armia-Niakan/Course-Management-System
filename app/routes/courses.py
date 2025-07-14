from flask import current_app, Blueprint, render_template, redirect, url_for, session, flash, request
import datetime

from app.services.course_manager import CourseManager
from app.services.enrollment_manager import EnrollmentManager
from app.services.user_manager import UserManager
from app.utils.helpers import is_time_in_range

course_bp = Blueprint('course', __name__)


@course_bp.route("/courses")
def courses():
    if 'user_email' not in session:
        flash("You need to login first", "error")
        return redirect(url_for('auth.login'))

    role = session['role']
    user_email = session['user_email']
    all_courses = list(CourseManager.load_courses().values())

    day_filter = request.args.get('day')
    time_filter = request.args.get('time')
    only_my = request.args.get('only_my_courses') == 'on'
    only_enrolled = request.args.get('only_enrolled') == 'on'
    not_enrolled = request.args.get('not_enrolled') == 'on'

    filtered = all_courses

    if day_filter:
        filtered = [c for c in filtered if any(s['day'] == day_filter for s in c['schedule'])]

    if time_filter:
        filtered = [c for c in filtered if any(is_time_in_range(s['time'], time_filter) for s in c['schedule'])]

    enrolled_ids = []
    if role == 'student':
        enrolled = EnrollmentManager.get_student_enrollments(user_email)
        enrolled_ids = [e['course_id'] for e in enrolled]
        if only_enrolled:
            filtered = [c for c in filtered if c['id'] in enrolled_ids]
        elif not_enrolled:
            filtered = [c for c in filtered if c['id'] not in enrolled_ids]
    elif role == 'teacher' and only_my:
        filtered = [c for c in filtered if c['teacher'] == user_email]

    return render_template('courses.html',
                           role=role,
                           username=session['username'],
                           courses=filtered,
                           enrolled_course_ids=enrolled_ids)


@course_bp.route("/courses/create", methods=['GET', 'POST'])
def create_course():
    if 'user_email' not in session or session['role'] != 'teacher':
        flash("Unauthorized", "error")
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        courses = CourseManager.load_courses()
        course_id = str(len(courses) + 1)
        days = request.form.getlist('day[]')
        times = request.form.getlist('time[]')
        durations = request.form.getlist('duration[]')

        schedule = []
        for d, t, dur in zip(days, times, durations):
            if d and t and dur:
                schedule.append({'day': d, 'time': t, 'duration': int(dur)})

        new_course = {
            'id': course_id,
            'name': request.form['name'],
            'teacher': session['user_email'],
            'teacher_name': session['username'],
            'schedule': schedule,
            'max_students': int(request.form['max_students']),
            'current_students': 0
        }

        for existing in courses.values():
            if existing['teacher'] == session['user_email']:
                if are_conflicting(existing, new_course):
                    flash(f"Schedule conflicts with course '{existing['name']}'", "error")
                    return redirect(url_for('course.create_course'))

        courses[course_id] = new_course
        CourseManager.save_courses(courses)
        flash("Course created successfully!", "success")
        current_app.logger.info(f"New course created by {session['user_email']}: {new_course['name']}")
        return redirect(url_for('course.courses'))

    return render_template('create_course.html',
                           role=session['role'],
                           username=session['username'])


@course_bp.route("/course/<course_id>")
def course_detail(course_id):
    if 'user_email' not in session:
        flash("You need to login first", "error")
        return redirect(url_for('auth.login'))

    courses = CourseManager.load_courses()
    course = courses.get(course_id)
    if not course:
        flash("Course not found", "error")
        return redirect(url_for('course.courses'))

    role = session['role']
    email = session['user_email']
    is_enrolled = False
    is_teacher = course['teacher'] == email
    students = []

    if role == 'student':
        is_enrolled = any(e['course_id'] == course_id for e in EnrollmentManager.get_student_enrollments(email))
    elif is_teacher:
        students = [UserManager.get_user(e['student_email']) for e in EnrollmentManager.get_course_enrollments(course_id)]

    hours = sum(s['duration'] for s in course['schedule'])

    return render_template('course_detail.html',
                           course=course,
                           role=role,
                           username=session['username'],
                           is_enrolled=is_enrolled,
                           is_full=course['current_students'] >= course['max_students'],
                           students=students,
                           is_teacher_of_course=is_teacher,
                           hours_per_week=hours,
                           sorted_schedules=sorted(course['schedule'], key=lambda s: (s['day'], s['time'])))


@course_bp.route("/enroll", methods=['POST'])
def enroll():
    if 'user_email' not in session or session['role'] != 'student':
        flash("Unauthorized", "error")
        return redirect(url_for('auth.login'))

    course_id = request.form['course_id']
    email = session['user_email']
    course = CourseManager.get_course(course_id)

    if course['current_students'] >= course['max_students']:
        flash("Course is full", "error")
        return redirect(url_for('course.courses'))

    if any(e['course_id'] == course_id for e in EnrollmentManager.get_student_enrollments(email)):
        flash("Already enrolled", "error")
        return redirect(url_for('course.courses'))

    for e in EnrollmentManager.get_student_enrollments(email):
        existing = CourseManager.get_course(e['course_id'])
        if are_conflicting(existing, course):
            flash("Schedule conflict with another course", "error")
            return redirect(url_for('course.courses'))

    EnrollmentManager.save_enrollments(EnrollmentManager.load_enrollments() + [{
        'student_email': email,
        'course_id': course_id
    }])
    CourseManager.increment_students(course_id)
    flash("Enrolled successfully!", "success")
    current_app.logger.info(f"Student {session['user_email']} enrolled in course {course_id}")
    return redirect(url_for('course.courses'))


@course_bp.route("/unenroll", methods=['POST'])
def unenroll():
    if 'user_email' not in session or session['role'] != 'student':
        return redirect(url_for('auth.login'))

    course_id = request.form['course_id']
    email = session['user_email']
    EnrollmentManager.delete_enrollment(email, course_id)
    CourseManager.decrement_students(course_id)
    flash("Unenrolled successfully", "success")
    current_app.logger.info(f"Student {session['user_email']} unenrolled from course {course_id}")
    return redirect(url_for('course.courses'))


@course_bp.route("/delete_course", methods=['POST'])
def delete_course():
    if 'user_email' not in session or session['role'] != 'teacher':
        flash("Unauthorized", "error")
        return redirect(url_for('auth.login'))

    course_id = request.form['course_id']
    courses = CourseManager.load_courses()
    course = courses.get(course_id)

    if course and course['teacher'] == session['user_email']:
        del courses[course_id]
        CourseManager.save_courses(courses)
        EnrollmentManager.save_enrollments(
            [e for e in EnrollmentManager.load_enrollments() if e['course_id'] != course_id])
        flash("Course deleted", "success")
        current_app.logger.info(f"{session['user_email']} deleted course {course_id}")
    else:
        flash("Unauthorized or not found", "error")

    return redirect(url_for('course.courses'))


@course_bp.route("/remove_student", methods=['POST'])
def remove_student():
    if 'user_email' not in session or session['role'] != 'teacher':
        flash("Unauthorized", "error")
        return redirect(url_for('auth.login'))

    course_id = request.form['course_id']
    student_email = request.form['student_email']
    course_name = request.form.get('course_name')

    course = CourseManager.get_course(course_id)
    if course and course['teacher'] == session['user_email']:
        EnrollmentManager.delete_enrollment(student_email, course_id)
        CourseManager.decrement_students(course_id)
        flash("Student removed", "success")
        current_app.logger.info(f"{session['user_email']} removed student {student_email} from course {course_id}")
    else:
        flash("Unauthorized", "error")

    return redirect(url_for('course.course_detail', course_id=course_id))


@course_bp.route("/calendar")
def calendar():
    if 'user_email' not in session:
        return redirect(url_for('auth.login'))

    email = session['user_email']
    role = session['role']
    calendar_data = {day: [] for day in ['Saturday', 'Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']}

    if role == 'student':
        enrolled = EnrollmentManager.get_student_enrollments(email)
        courses = [CourseManager.get_course(e['course_id']) for e in enrolled if CourseManager.get_course(e['course_id'])]
    else:
        courses = [c for c in CourseManager.load_courses().values() if c['teacher'] == email]

    for course in courses:
        for s in course['schedule']:
            entry = course.copy()
            entry['time'] = s['time']
            entry['duration'] = s['duration']
            calendar_data[s['day']].append(entry)

    for day in calendar_data:
        calendar_data[day].sort(key=lambda x: x['time'])

    return render_template('calendar.html',
                           calendar_data=calendar_data,
                           role=role,
                           username=session['username'])


def are_conflicting(course1, course2):
    def to_minutes(time_str):
        h, m = map(int, time_str.split(":"))
        return h * 60 + m

    for s1 in course1['schedule']:
        for s2 in course2['schedule']:
            if s1['day'] != s2['day']:
                continue
            start1, end1 = to_minutes(s1['time']), to_minutes(s1['time']) + s1['duration'] * 60
            start2, end2 = to_minutes(s2['time']), to_minutes(s2['time']) + s2['duration'] * 60
            if not (end1 <= start2 or end2 <= start1):
                return True
    return False
