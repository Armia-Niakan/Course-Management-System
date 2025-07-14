from flask import current_app, Blueprint, render_template, redirect, url_for, session, flash, request
from werkzeug.security import generate_password_hash
import datetime
from app.services.user_manager import UserManager
from app.services.course_manager import CourseManager
from app.services.enrollment_manager import EnrollmentManager

main_bp = Blueprint('main', __name__)


@main_bp.route("/")
@main_bp.route("/about")
def about():
    return render_template('about.html')


@main_bp.route("/dashboard")
def dashboard():
    if 'user_email' not in session:
        flash("You have to login first", "error")
        return redirect(url_for('auth.login'))

    user_email = session['user_email']
    role = session['role']
    username = session['username']

    days = ['Saturday', 'Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    today_idx = (datetime.datetime.now().weekday() + 2) % 7
    current_day = days[today_idx]
    next_day = days[(today_idx + 1) % 7]
    now = datetime.datetime.now().time()

    all_courses = CourseManager.load_courses()

    if role == 'student':
        enrollments = EnrollmentManager.get_student_enrollments(user_email)
        courses = [all_courses.get(e['course_id']) for e in enrollments if all_courses.get(e['course_id'])]
        total_hours = sum(sch['duration'] for course in courses for sch in course['schedule'])
    else:
        courses = [c for c in all_courses.values() if c['teacher'] == user_email]
        total_students = 0
        total_hours = 0
        for course in courses:
            enrolled = EnrollmentManager.get_course_enrollments(course['id'])
            course['student_count'] = len(enrolled)
            total_students += len(enrolled)
            total_hours += sum(s['duration'] for s in course['schedule'])

    ongoing = []
    upcoming = []
    tomorrow = []

    for course in courses:
        for s in course['schedule']:
            course_copy = course.copy()
            course_copy['time'] = s['time']
            course_copy['duration'] = s['duration']

            course_time = datetime.datetime.strptime(s['time'], "%H:%M").time()
            end_time = (datetime.datetime.combine(datetime.date.today(), course_time) +
                        datetime.timedelta(hours=s['duration'])).time()

            if s['day'] == current_day:
                if course_time <= now < end_time:
                    ongoing.append(course_copy)
                elif now < course_time:
                    upcoming.append(course_copy)
            elif s['day'] == next_day:
                tomorrow.append(course_copy)

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
def profile():
    if 'user_email' not in session:
        flash("You need to login first", "error")
        return redirect(url_for('auth.login'))

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
def settings():
    if 'user_email' not in session:
        flash("You need to login first", "error")
        return redirect(url_for('auth.login'))

    email = session['user_email']
    user = UserManager.get_user(email)

    return render_template('settings.html',
                           email=email,
                           role=session['role'],
                           username=session['username'],
                           user=user)


@main_bp.route("/update_username", methods=['POST'])
def update_username():
    if 'user_email' not in session:
        return redirect(url_for('auth.login'))

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
def update_password():
    if 'user_email' not in session:
        return redirect(url_for('auth.login'))

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
def delete_account():
    if 'user_email' not in session:
        return redirect(url_for('auth.login'))

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
        teacher_ids = [cid for cid, c in courses.items() if c['teacher'] == email]
        for cid in teacher_ids:
            del courses[cid]
        CourseManager.save_courses(courses)
        EnrollmentManager.save_enrollments(
            [e for e in EnrollmentManager.load_enrollments() if e['course_id'] not in teacher_ids])

    UserManager.delete_user(email)
    session.clear()
    flash("Your account has been permanently deleted", "success")
    current_app.logger.info(f"Account deleted: {email}")
    return redirect(url_for('auth.login'))
