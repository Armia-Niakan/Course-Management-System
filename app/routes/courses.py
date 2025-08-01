from flask import current_app, Blueprint, render_template, redirect, url_for, session, flash, request, send_from_directory
import datetime
import os
from app.utils.file_handler import save_uploaded_file

from app.services.course_manager import CourseManager
from app.services.enrollment_manager import EnrollmentManager
from app.services.user_manager import UserManager
from app.services.exam_manager import ExamManager
from app.services.submission_manager import SubmissionManager
from app.utils.helpers import is_time_in_range
from app.utils.decorators import teacher_required, login_required

course_bp = Blueprint('course', __name__)

@course_bp.route("/courses")
@login_required
def courses():

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

    referrer = request.referrer

    if role == 'admin':
        flash("Unauthorized access")
        return redirect(referrer or url_for('admin.admin_dashboard'))
    
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
@teacher_required
def create_course():

    if request.method == 'POST':
        courses = CourseManager.load_courses()
        course_id = str(len(courses) + 1)
        days = request.form.getlist('day[]')
        times = request.form.getlist('time[]')
        durations = request.form.getlist('duration[]')

        is_free = request.form.get('is_free') == 'on'
        price = 0.0 if is_free else float(request.form.get('price', 0.0))

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
            'price': price,
            'current_students': 0,
            'materials': []
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
@login_required
def course_detail(course_id):
    course = CourseManager.get_course(course_id)
    if not course:
        flash("Course not found", "error")
        return redirect(url_for('course.courses'))

    role = session['role']
    email = session['user_email']
    is_enrolled = False
    is_teacher = course.get('teacher') == email
    students = []
    exams = ExamManager.get_exams_for_course(course_id)
    student_submissions = {}

    if role == 'student':
        is_enrolled = any(e['course_id'] == course_id for e in EnrollmentManager.get_student_enrollments(email))
        submissions = SubmissionManager.load_submissions()
        for sub in submissions:
            if sub.student_email == email:
                student_submissions[sub.exam_id] = sub

    elif is_teacher or role == 'admin':
        students = [UserManager.get_user(e['student_email']) for e in EnrollmentManager.get_course_enrollments(course_id) if UserManager.get_user(e['student_email'])]

    hours = 0
    sorted_schedules_list = []
    schedules_list = course.get('schedule', [])
    if isinstance(schedules_list, list):
        for s in schedules_list:
            if isinstance(s, dict):
                try:
                    hours += int(s.get('duration', 0))
                except (ValueError, TypeError):
                    current_app.logger.warning(f"Could not parse duration for course {course_id}: {s.get('duration')}")
        
        try:
            sorted_schedules_list = sorted(schedules_list, key=lambda s: (s.get('day', ''), s.get('time', '')))
        except TypeError:
            current_app.logger.error(f"Failed to sort schedule for course {course_id}. Data: {schedules_list}")
            sorted_schedules_list = schedules_list

    return render_template('course_detail.html',
                           course=course,
                           role=role,
                           username=session['username'],
                           is_enrolled=is_enrolled,
                           is_full=course.get('current_students', 0) >= course.get('max_students', 0),
                           students=students,
                           is_teacher_of_course=is_teacher,
                           hours_per_week=hours,
                           sorted_schedules=sorted_schedules_list,
                           exams=exams,
                           student_submissions=student_submissions)

@course_bp.route("/enroll", methods=['POST'])
@login_required
def enroll():
    if session['role'] != 'student':
        flash("Only students can enroll in courses.", "error")
        return redirect(url_for('course.courses'))

    course_id = request.form.get('course_id')
    course = CourseManager.get_course(course_id)
    email = session['user_email']

    # Perform all pre-enrollment checks
    if not course:
        flash("Course not found.", "error")
        return redirect(url_for('course.courses'))
    if course.get('current_students', 0) >= course.get('max_students', 0):
        flash("This course is full.", "error")
        return redirect(url_for('course.course_detail', course_id=course_id))
    if any(e['course_id'] == course_id for e in EnrollmentManager.get_student_enrollments(email)):
        flash("You are already enrolled in this course.", "info")
        return redirect(url_for('course.course_detail', course_id=course_id))
    for e in EnrollmentManager.get_student_enrollments(email):
        existing = CourseManager.get_course(e['course_id'])
        if are_conflicting(existing, course):
            flash("This course has a schedule conflict with another of your courses.", "error")
            return redirect(url_for('course.courses'))

    # If the course is free, enroll directly. Otherwise, go to payment.
    if course.get('price', 0.0) <= 0:
        EnrollmentManager.add_enrollment(email, course_id)
        CourseManager.increment_students(course_id)
        flash(f"Successfully enrolled in the free course: {course['name']}!", "success")
        current_app.logger.info(f"Student {email} enrolled in free course {course_id}.")
        return redirect(url_for('course.course_detail', course_id=course_id))
    else:
        return redirect(url_for('course.payment_page', course_id=course_id))

@course_bp.route("/course/<course_id>/payment")
@login_required
def payment_page(course_id):
    if session['role'] != 'student':
        flash("Only students can enroll in courses.", "error")
        return redirect(url_for('course.courses'))

    course = CourseManager.get_course(course_id)
    if not course:
        flash("Course not found.", "error")
        return redirect(url_for('course.courses'))

    if any(e['course_id'] == course_id for e in EnrollmentManager.get_student_enrollments(session['user_email'])):
        flash("You are already enrolled in this course.", "info")
        return redirect(url_for('course.course_detail', course_id=course_id))

    return render_template('payment.html', 
                           course=course, 
                           username=session['username'], 
                           role=session['role'])

@course_bp.route("/process_payment", methods=['POST'])
@login_required
def process_payment():
    if 'user_email' not in session or session['role'] != 'student':
        flash("Unauthorized", "error")
        return redirect(url_for('auth.login'))

    course_id = request.form['course_id']
    email = session['user_email']
    course = CourseManager.get_course(course_id)

    # Re-run checks in case the student lingered on the payment page
    if not course:
        flash("Course not found.", "error")
        return redirect(url_for('course.courses'))
    if course['current_students'] >= course['max_students']:
        flash("Course is full", "error")
        return redirect(url_for('course.courses'))
    if any(e['course_id'] == course_id for e in EnrollmentManager.get_student_enrollments(email)):
        flash("Already enrolled", "error")
        return redirect(url_for('course.courses'))

    EnrollmentManager.add_enrollment(email, course_id)
    CourseManager.increment_students(course_id)
    flash("Payment successful. You are now enrolled!", "success")
    current_app.logger.info(f"Student {session['user_email']} enrolled in course {course_id} after payment simulation.")
    return redirect(url_for('course.course_detail', course_id=course_id))


@course_bp.route("/unenroll", methods=['POST'])
@login_required
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
@teacher_required
def delete_course():

    course_id = request.form['course_id']
    courses = CourseManager.load_courses()
    course = courses.get(course_id)

    if course and course['teacher'] == session['user_email']:
        exams_to_delete = ExamManager.get_exams_for_course(course_id)
        for exam in exams_to_delete:
            ExamManager.delete_exam(exam.id)
            
        CourseManager.delete_course(course_id)
        EnrollmentManager.save_enrollments(
            [e for e in EnrollmentManager.load_enrollments() if e['course_id'] != course_id])
        flash("Course and all its exams deleted", "success")
        current_app.logger.info(f"{session['user_email']} deleted course {course_id}")
    else:
        flash("Unauthorized or not found", "error")

    return redirect(url_for('course.courses'))


@course_bp.route("/remove_student", methods=['POST'])
@teacher_required
def remove_student():

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
@login_required
def calendar():

    email = session['user_email']
    role = session['role']
    calendar_data = {day: [] for day in ['Saturday', 'Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']}

    referrer = request.referrer

    if role == 'admin':
        flash("Unauthorized access")
        return redirect(referrer or url_for('admin.admin_dashboard'))
    
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

@course_bp.route("/upload_material/<course_id>", methods=['POST'])
@teacher_required
def upload_material(course_id):
    if 'file' not in request.files:
        flash('No file part', 'error')
        return redirect(url_for('course.course_detail', course_id=course_id))
    
    file = request.files['file']
    description = request.form.get('description', '')
    
    file_info = save_uploaded_file(file, course_id)
    if not file_info:
        return redirect(url_for('course.course_detail', course_id=course_id))
    
    file_info['description'] = description
    
    courses = CourseManager.load_courses()
    if course_id in courses:
        if 'materials' not in courses[course_id]:
            courses[course_id]['materials'] = []
        courses[course_id]['materials'].append(file_info)
        CourseManager.save_courses(courses)
        flash('File uploaded successfully', 'success')
    
    return redirect(url_for('course.course_detail', course_id=course_id))

@course_bp.route("/course/<course_id>/download/<filename>")
@login_required
def download_material(course_id, filename):
    courses = CourseManager.load_courses()
    if course_id not in courses:
        flash('Course not found', 'error')
        return redirect(url_for('course.courses'))
    
    course = courses[course_id]
    if session['role'] == 'student':
        enrollments = EnrollmentManager.get_student_enrollments(session['user_email'])
        if not any(e['course_id'] == course_id for e in enrollments):
            flash('You are not enrolled in this course', 'error')
            return redirect(url_for('course.courses'))
    elif session['role'] == 'teacher' and course['teacher'] != session['user_email']:
        flash('You are not the teacher of this course', 'error')
        return redirect(url_for('course.courses'))
    
    upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], course_id)
    return send_from_directory(upload_dir, filename, as_attachment=True)

@course_bp.route("/view/<course_id>/<filename>")
@login_required
def view_material(course_id, filename):
    courses = CourseManager.load_courses()
    if course_id not in courses:
        flash('Course not found', 'error')
        return redirect(url_for('course.courses'))
    
    course = courses[course_id]
    if session['role'] == 'student':
        enrollments = EnrollmentManager.get_student_enrollments(session['user_email'])
        if not any(e['course_id'] == course_id for e in enrollments):
            flash('You are not enrolled in this course', 'error')
            return redirect(url_for('course.courses'))
    elif session['role'] == 'teacher' and course['teacher'] != session['user_email']:
        flash('You are not the teacher of this course', 'error')
        return redirect(url_for('course.courses'))
    
    upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], course_id)
    
    return send_from_directory(upload_dir, filename, as_attachment=False)

@course_bp.route("/delete_material/<course_id>/<filename>", methods=['POST'])
@login_required
def delete_material(course_id, filename):
    courses = CourseManager.load_courses()
    course = courses.get(course_id)
    
    if not (course and 
           (session['role'] == 'admin' or 
            (session['role'] == 'teacher' and course['teacher'] == session['user_email']))):
        flash('Unauthorized', 'error')
        return redirect(url_for('course.courses'))
    
    if 'materials' in courses[course_id]:
        courses[course_id]['materials'] = [m for m in courses[course_id]['materials'] if m.get('filename') != filename]
        CourseManager.save_courses(courses)
    
    upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], course_id)
    file_path = os.path.join(upload_dir, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
    
    flash('File deleted successfully', 'success')
    return redirect(url_for('course.course_detail', course_id=course_id))
