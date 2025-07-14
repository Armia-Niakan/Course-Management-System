from flask import current_app, Blueprint, render_template, redirect, url_for, request, flash, session, jsonify
from werkzeug.security import generate_password_hash
import datetime
import os

from app.utils.decorators import admin_required
from app.services.user_manager import UserManager
from app.services.course_manager import CourseManager
from app.services.enrollment_manager import EnrollmentManager
from app.models.user import User

admin_bp = Blueprint('admin', __name__, url_prefix="/admin")


@admin_bp.route("/login", methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = UserManager.get_user(email)
        if not user or user.role != 'admin' or not user.verify_password(password):
            flash("Invalid admin credentials", "error")
            current_app.logger.warning(f"Admin login failed for {email}")
            return redirect(url_for('admin.admin_login'))

        session['user_email'] = user.email
        session['username'] = user.username
        session['role'] = user.role
        flash(f"Welcome Admin {user.username}!", "success")
        current_app.logger.info(f"Admin {email} logged in successfully")
        return redirect(url_for('admin.admin_dashboard'))

    return render_template('admin_login.html')

@admin_bp.route("/add_admin", methods=['GET', 'POST'])
@admin_required
def add_admin():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        if not all([username, email, password]):
            flash("All fields are required.", "error")
            return redirect(url_for('admin.add_admin'))

        if UserManager.email_exists(email):
            flash("An account with this email already exists.", "error")
            current_app.logger.warning(
                f"Admin {session.get('user_email')} failed to add new admin {email}: email already exists."
            )
            return redirect(url_for('admin.add_admin'))

        new_admin = User(
            email=email,
            username=username,
            password_hash=generate_password_hash(password),
            role='admin',
            created_at=datetime.datetime.now().isoformat()
        )
        
        UserManager.add_user(new_admin)
        flash(f"Admin user '{username}' created successfully.", "success")
        current_app.logger.info(f"Admin {session.get('user_email')} created new admin user: {email}.")
        return redirect(url_for('admin.admin_users'))

    return render_template('add_admin.html', username=session.get('username'))

@admin_bp.route("/dashboard")
@admin_required
def admin_dashboard():
    users = UserManager.load_users()
    courses = CourseManager.load_courses()
    enrollments = EnrollmentManager.load_enrollments()

    total_users = len(users)
    total_courses = len(courses)
    total_enrollments = len(enrollments)
    recent_users = sorted(users.values(), key=lambda u: u.created_at, reverse=True)[:5]

    return render_template('admin_dashboard.html',
                           total_users=total_users,
                           total_courses=total_courses,
                           total_enrollments=total_enrollments,
                           recent_users=recent_users,
                           username=session['username'])


@admin_bp.route("/users")
@admin_required
def admin_users():
    users = UserManager.load_users()
    return render_template('admin_users.html', users=users.values(), username=session['username'])


@admin_bp.route("/courses")
@admin_required
def admin_courses():
    courses = CourseManager.load_courses()
    users = UserManager.load_users()

    course_list = []
    for course_id, course in courses.items():
        teacher = users.get(course['teacher'])
        total_hours = sum(s['duration'] for s in course['schedule'])

        course_list.append({
            'id': course_id,
            'name': course['name'],
            'teacher': course['teacher'],
            'teacher_name': teacher.username if teacher else 'Unknown',
            'schedule': course['schedule'],
            'total_hours': total_hours,
            'max_students': course['max_students'],
            'current_students': course.get('current_students', 0)
        })

    return render_template('admin_courses.html', courses=course_list, username=session['username'])


@admin_bp.route("/enrollments")
@admin_required
def admin_enrollments():
    enrollments = EnrollmentManager.load_enrollments()
    courses = CourseManager.load_courses()
    users = UserManager.load_users()

    enhanced = []
    for e in enrollments:
        course = courses.get(e['course_id'])
        student = users.get(e['student_email'])
        teacher = users.get(course['teacher']) if course else None

        if course and student:
            enhanced.append({
                'course_name': course['name'],
                'student_name': student.username,
                'teacher_name': teacher.username if teacher else 'Unknown',
                'schedule': course['schedule'],
                'student_email': e['student_email'],
                'course_id': e['course_id']
            })

    return render_template('admin_enrollments.html', enrollments=enhanced, username=session['username'])


@admin_bp.route("/logs")
@admin_required
def admin_logs():
    log_path = current_app.config['LOG_FILE']
    try:
        with open(log_path, 'r') as f:
            logs = f.readlines()
        logs = [line.strip() for line in logs][-200:]
    except FileNotFoundError:
        logs = ["Log file not found"]

    return render_template('admin_logs.html', logs=reversed(logs), username=session['username'])


@admin_bp.route("/delete_user", methods=['POST'])
@admin_required
def admin_delete_user():
    email = request.form.get('email')
    if email == session.get('user_email'):
        flash("You cannot delete your own account from here", "error")
        return redirect(url_for('admin.admin_users'))

    if UserManager.delete_user(email):
        enrollments = EnrollmentManager.load_enrollments()
        enrollments = [e for e in enrollments if e['student_email'] != email]
        EnrollmentManager.save_enrollments(enrollments)
        flash(f"User {email} deleted", "success")
        current_app.logger.info(f"User {email} deleted by admin {session.get('user_email')}")
    else:
        flash("User not found", "error")

    return redirect(url_for('admin.admin_users'))


@admin_bp.route("/delete_course", methods=['POST'])
@admin_required
def admin_delete_course():
    course_id = request.form.get('course_id')
    courses = CourseManager.load_courses()

    if course_id not in courses:
        flash("Course not found", "error")
        return redirect(url_for('admin.admin_courses'))

    del courses[course_id]
    CourseManager.save_courses(courses)
    EnrollmentManager.save_enrollments(
        [e for e in EnrollmentManager.load_enrollments() if e['course_id'] != course_id])
    flash("Course deleted", "success")
    current_app.logger.info(f"Course {course_id} deleted by admin {session.get('user_email')}")
    return redirect(url_for('admin.admin_courses'))


@admin_bp.route("/delete_enrollment", methods=['POST'])
@admin_required
def admin_delete_enrollment():
    student_email = request.form.get('student_email')
    course_id = request.form.get('course_id')

    if EnrollmentManager.delete_enrollment(student_email, course_id):
        CourseManager.decrement_students(course_id)
        flash("Enrollment deleted", "success")
        current_app.logger.info(f"Enrollment deleted: student {student_email} from course {course_id} by admin {session.get('user_email')}")
    else:
        flash("Enrollment not found", "error")

    return redirect(url_for('admin.admin_enrollments'))


@admin_bp.route("/clear_logs", methods=['POST'])
@admin_required
def admin_clear_logs():
    log_path = current_app.config['LOG_FILE']
    try:
        with open(log_path, 'w') as f:
            f.write('')

        for handler in current_app.logger.handlers:
            if isinstance(handler, current_app.logger.FileHandler):
                handler.close()
                current_app.logger.removeHandler(handler)

        flash("Logs cleared", "success")
        current_app.logger.info("Logs cleared by admin")
        return jsonify({"success": True})
    except Exception as e:
        current_app.logger.error(f"Log clear failed: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
