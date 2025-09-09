from flask import current_app, Blueprint, render_template, redirect, url_for, session, flash, request
from werkzeug.security import generate_password_hash
import datetime

from app.services.user_manager import UserManager
from app.services.course_manager import CourseManager
from app.services.enrollment_manager import EnrollmentManager
from app.services.exam_manager import ExamManager
from app.services.submission_manager import SubmissionManager
from app.utils.decorators import login_required, admin_required, teacher_required
main_bp = Blueprint('main', __name__)

@main_bp.route("/")
@main_bp.route("/about")
def about():
    return render_template('about.html')

@main_bp.route("/dashboard")
@login_required
def dashboard():

    user_email = session['user_email']
    role = session['role']
    username = session['username']

    days = ['Saturday', 'Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    today_idx = (datetime.datetime.now().weekday() + 2) % 7
    current_day = days[today_idx]
    next_day = days[(today_idx + 1) % 7]
    now = datetime.datetime.now().time()

    all_courses = CourseManager.load_courses()

    if role == 'admin':
        return redirect(url_for('admin.admin_dashboard'))
    
    courses = []
    enrollments = []
    total_students = 0
    total_hours = 0

    if role == 'student':
        enrollments = EnrollmentManager.get_student_enrollments(user_email)
        courses = [all_courses.get(e['course_id']) for e in enrollments if all_courses.get(e['course_id'])]
        total_hours = sum(sch.get('duration', 0) for course in courses if course for sch in course.get('schedule', []))
    else: # Teacher
        courses = [c for c in all_courses.values() if c.get('teacher') == user_email]
        for course in courses:
            enrolled_count = len(EnrollmentManager.get_course_enrollments(course['id']))
            course['student_count'] = enrolled_count
            total_students += enrolled_count
            total_hours += sum(s.get('duration', 0) for s in course.get('schedule', []))

    ongoing = []
    upcoming = []
    tomorrow = []
    
    ongoing_ids = set()
    upcoming_ids = set()
    tomorrow_ids = set()

    for course in courses:
        if not isinstance(course, dict) or 'id' not in course:
            continue

        course_id = course['id']
        for s in course.get('schedule', []):
            if not all(k in s for k in ['day', 'time', 'duration']):
                continue

            course_time = datetime.datetime.strptime(s['time'], "%H:%M").time()
            end_time = (datetime.datetime.combine(datetime.date.today(), course_time) +
                        datetime.timedelta(hours=s['duration'])).time()

            if s['day'] == current_day:
                if course_time <= now < end_time:
                    if course_id not in ongoing_ids:
                        course_copy = course.copy()
                        course_copy.update(s)
                        ongoing.append(course_copy)
                        ongoing_ids.add(course_id)
                elif now < course_time:
                    if course_id not in upcoming_ids:
                        course_copy = course.copy()
                        course_copy.update(s)
                        upcoming.append(course_copy)
                        upcoming_ids.add(course_id)
            elif s['day'] == next_day:
                if course_id not in tomorrow_ids:
                    course_copy = course.copy()
                    course_copy.update(s)
                    tomorrow.append(course_copy)
                    tomorrow_ids.add(course_id)

    return render_template('dashboard.html',
                           role=role,
                           username=username,
                           today=datetime.datetime.now().strftime("%B %d %H:%M"),
                           ongoing_classes=sorted(ongoing, key=lambda c: c['time']),
                           today_upcoming_classes=sorted(upcoming, key=lambda c: c['time']),
                           tomorrow_classes=sorted(tomorrow, key=lambda c: c['time']),
                           current_day=current_day,
                           next_day=next_day,
                           total_hours=total_hours,
                           total_students=total_students if role == 'teacher' else None,
                           enrollments=enrollments if role == 'student' else None,
                           courses_teaching=courses if role == 'teacher' else None)


@main_bp.route("/profile")
@login_required
def profile():

    email = session['user_email']
    role = session['role']
    username = session['username']
    user = UserManager.get_user(email)

    enrollments = EnrollmentManager.get_student_enrollments(email) if role == 'student' else None
    courses = CourseManager.load_courses()
    teaching = [c for c in courses.values() if c['teacher'] == email] if role == 'teacher' else None

    return render_template('profile.html',
                           email=email,
                           role=role,
                           username=username,
                           user=user,
                           enrollments=enrollments,
                           courses_teaching=teaching)


@main_bp.route("/settings")
@login_required
def settings():

    email = session['user_email']
    user = UserManager.get_user(email)

    return render_template('settings.html',
                           email=email,
                           role=session['role'],
                           username=session['username'],
                           user=user)


@main_bp.route("/update_username", methods=['POST'])
@login_required
def update_username():

    new_username = request.form.get('new_username')
    password = request.form.get('password')
    email = session['user_email']

    user = UserManager.get_user(email)
    if not user or not user.verify_password(password):
        flash("Incorrect password", "error")
        return redirect(url_for('main.settings'))

    if UserManager.update_user(email, username=new_username):
        session['username'] = new_username
        flash("Username updated successfully!", "success")
        current_app.logger.info(f"User {email} updated username to {new_username}")
    else:
        flash("Failed to update username", "error")
        current_app.logger.error(f"Failed to update username for {email}")

    return redirect(url_for('main.settings'))


@main_bp.route("/update_password", methods=['POST'])
@login_required
def update_password():

    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm = request.form.get('confirm_password')
    email = session['user_email']

    if new_password != confirm:
        flash("New passwords do not match", "error")
        return redirect(url_for('main.settings'))

    user = UserManager.get_user(email)
    if not user or not user.verify_password(current_password):
        flash("Current password incorrect", "error")
        return redirect(url_for('main.settings'))

    if UserManager.update_user(email, password_hash=generate_password_hash(new_password)):
        flash("Password updated successfully!", "success")
        current_app.logger.info(f"User {email} changed their password")
    else:
        flash("Failed to update password", "error")
        current_app.logger.error(f"Failed to update password for {email}")

    return redirect(url_for('main.settings'))


@main_bp.route("/delete_account", methods=['POST'])
@login_required
def delete_account():
    password = request.form.get('password')
    email = session['user_email']
    user = UserManager.get_user(email)

    if not user or not user.verify_password(password):
        flash("Incorrect password", "error")
        return redirect(url_for('main.settings'))

    role = session['role']

    if role == 'student':
        enrollments = EnrollmentManager.get_student_enrollments(email)
        for e in enrollments:
            CourseManager.decrement_students(e['course_id'])
        EnrollmentManager.save_enrollments(
            [e for e in EnrollmentManager.load_enrollments() if e['student_email'] != email])

    elif role == 'teacher':
        courses = CourseManager.load_courses()
        teacher_course_ids = [cid for cid, c in courses.items() if c['teacher'] == email]
        
        for course_id in teacher_course_ids:
            exams_to_delete = ExamManager.get_exams_for_course(course_id)
            for exam in exams_to_delete:
                ExamManager.delete_exam(exam.id)
        
        for course_id in teacher_course_ids:
            CourseManager.delete_course(course_id)
        
        all_enrollments = EnrollmentManager.load_enrollments()
        remaining_enrollments = [e for e in all_enrollments if e['course_id'] not in teacher_course_ids]
        EnrollmentManager.save_enrollments(remaining_enrollments)

    UserManager.delete_user(email)
    session.clear()
    flash("Your account has been permanently deleted", "success")
    current_app.logger.info(f"Account deleted: {email}")
    return redirect(url_for('auth.login'))