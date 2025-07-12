from flask import Flask, render_template, request, redirect, url_for, json, jsonify, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import os
import json
import datetime
import secrets
import smtplib
from email.mime.text import MIMEText
from dataclasses import dataclass, asdict
from typing import Dict, Optional, Tuple
import logging
from logging.handlers import RotatingFileHandler
from functools import wraps

app = Flask(__name__)
app.secret_key = os.urandom(24)


VALID_ROLES = {"student", "teacher", "admin"}

COURSES_FILE = 'courses.json'
ENROLLMENTS_FILE = 'enrollments.json'
USER_DATA_FILE = 'users.json'
TOKEN_DATA_FILE = 'reset_tokens.json'
LOG_FILE = 'app.log'

SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
EMAIL_ADDRESS = 'coursemanagementsystem1403@gmail.com'
EMAIL_PASSWORD = 'natm cmet bspn gvci'
APP_URL = 'http://localhost:5000'

handler = RotatingFileHandler(LOG_FILE, maxBytes=10000, backupCount=3)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)


@dataclass
class User:
    email: str
    username: str
    password_hash: str
    role: str
    created_at: str

    @classmethod
    def from_dict(cls, data: Dict):
        if not all(k in data for k in ("email", "username", "password_hash", "role", "created_at")):
            raise ValueError("Missing required fields")
            
        if data["role"] not in VALID_ROLES:
            raise ValueError(f"Invalid role. Must be one of: {VALID_ROLES}")        

        return cls(
            email=data.get('email'),
            username=data.get('username'),
            password_hash=data.get('password_hash'),
            role=data.get('role'),
            created_at=data.get('created_at'),
        )
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    def verify_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

class UserManager:
    @staticmethod
    def load_users() -> Dict[str, User]:
        try:
            with open(USER_DATA_FILE, 'r') as f:
                users_data = json.load(f)
                return {email: User.from_dict(data) for email, data in users_data.items()}
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    

class UserManager:
    @staticmethod
    def load_users() -> Dict[str, User]:
        try:
            with open(USER_DATA_FILE, 'r') as f:
                users_data = json.load(f)
                users = {email: User.from_dict(data) for email, data in users_data.items()}
                
                # Check if any admin exists
                if not any(user.role == 'admin' for user in users.values()):
                    # Create default admin if none exists
                    default_admin = User(
                        email="admin@exam.com",
                        username="admin",
                        password_hash=generate_password_hash("74578126"),
                        role="admin",
                        created_at=str(datetime.datetime.now())
                    )

                    users[default_admin.email] = default_admin
                    UserManager.save_users(users)
                    app.logger.info("Created default admin user")
                
                return users
                
        except (FileNotFoundError, json.JSONDecodeError):
            # If file doesn't exist or is invalid, create with default admin
            default_admin = User(
                email="admin@example.com",
                username="admin",
                password_hash=generate_password_hash("74578126"),
                role="admin",
                created_at=str(datetime.datetime.now())
            )
            users = {default_admin.email: default_admin}
            UserManager.save_users(users)
            app.logger.info("Created new user file with default admin")
            return users
        
    @staticmethod
    def save_users(users: Dict[str, User]):
        users_data = {email: user.to_dict() for email, user in users.items()}
        with open(USER_DATA_FILE, 'w') as f:
            json.dump(users_data, f, indent=4)
    
    @staticmethod
    def get_user(email: str) -> Optional[User]:
        users = UserManager.load_users()
        return users.get(email)
    
    @staticmethod
    def add_user(user: User):
        users = UserManager.load_users()
        users[user.email] = user
        UserManager.save_users(users)

    @staticmethod
    def update_user(email: str, **kwargs) -> bool:
        users = UserManager.load_users()
        if email not in users:
            return False
    
        user = users[email]
        allowed_fields = {'username', 'password_hash'} 
    
        updates_made = False
        for key, value in kwargs.items():
            if key in allowed_fields and hasattr(user, key):
                setattr(user, key, value)
                updates_made = True
    
        if updates_made:
            UserManager.save_users(users)
        return updates_made 
    
    @staticmethod
    def delete_user(email: str) -> bool:
        users = UserManager.load_users()
        if email not in users:
            return False
    
        del users[email]
        UserManager.save_users(users)
        return True

    @staticmethod
    def email_exists(email: str) -> bool:
        users = UserManager.load_users()
        return email in users

class TokenManager:
    @staticmethod
    def load_tokens() -> Dict[str, dict]:
        try:
            with open(TOKEN_DATA_FILE, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    @staticmethod
    def save_tokens(tokens: Dict[str, dict]):
        with open(TOKEN_DATA_FILE, 'w') as f:
            json.dump(tokens, f, indent=4)
    
    @staticmethod
    def generate_token(email: str) -> str:
        token = secrets.token_urlsafe(32)
        tokens = TokenManager.load_tokens()
        tokens[token] = {
            'email': email,
            'created_at': datetime.datetime.now().isoformat(),
            'expires_at': (datetime.datetime.now() + datetime.timedelta(hours=1)).isoformat()
        }
        TokenManager.save_tokens(tokens)
        return token
    
    @staticmethod
    def validate_token(token: str) -> Tuple[bool, Optional[str]]:
        tokens = TokenManager.load_tokens()
        if token not in tokens:
            return False, None
        
        token_data = tokens[token]
        expires_at = datetime.datetime.fromisoformat(token_data['expires_at'])
        
        if datetime.datetime.now() > expires_at:
            del tokens[token]
            TokenManager.save_tokens(tokens)
            return False, None
        
        return True, token_data['email']
    
    @staticmethod
    def delete_token(token: str):
        tokens = TokenManager.load_tokens()
        if token in tokens:
            del tokens[token]
            TokenManager.save_tokens(tokens)

def send_reset_email(email: str, token: str) -> bool:
    reset_url = f"{APP_URL}/reset_password/{token}"
    message = MIMEText(
        f"""Hello,

You requested a password reset for your account. Please click the following link to reset your password:
{reset_url}

This link will expire in 1 hour. If you didn't request this, please ignore this email."""
    )

    message['Subject'] = 'Password Reset Request'
    message['From'] = EMAIL_ADDRESS
    message['To'] = email

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, email, message.as_string())
        print("Email sent successfully!")
        app.logger.info(f"Password reset email sent to {email}")
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        app.logger.error(f"Error sending password reset email to {email}: {e}")
        return False

if not os.path.exists(USER_DATA_FILE):
    UserManager.save_users({})

if not os.path.exists(TOKEN_DATA_FILE):
    TokenManager.save_tokens({})

@dataclass
class Course:
    id: str
    name: str
    teacher: str
    teacher_name: str
    schedule: list[dict]    #{day: str, time: str, duration: int}
    max_students: int
    current_students: int = 0

@dataclass
class Enrollment:
    student_email: str
    course_id: str

class CourseManager:
    @staticmethod
    def load_courses():
        try:
            with open(COURSES_FILE, 'r') as f:
                courses_data = json.load(f)
                for course_id, course in courses_data.items():
                    if 'current_students' not in course:
                        course['current_students'] = 0
                return courses_data
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
        
    @staticmethod
    def increment_students(course_id):
        courses = CourseManager.load_courses()
        if course_id in courses:
            courses[course_id]['current_students'] += 1
            CourseManager.save_courses(courses)
            return True
        return False

    @staticmethod
    def decrement_students(course_id):
        courses = CourseManager.load_courses()
        if course_id in courses and courses[course_id]['current_students'] > 0:
            courses[course_id]['current_students'] -= 1
            CourseManager.save_courses(courses)
            return True
        return False
        
    @staticmethod
    def save_courses(courses):
        with open(COURSES_FILE, 'w') as f:
            json.dump(courses, f, indent=4)

    @staticmethod
    def get_course(course_id):
        courses = CourseManager.load_courses()
        return courses.get(course_id)

class EnrollmentManager:
    @staticmethod
    def load_enrollments():
        try:
            with open(ENROLLMENTS_FILE, 'r') as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
                return []
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    @staticmethod
    def save_enrollments(enrollments):
        with open(ENROLLMENTS_FILE, 'w') as f:
            json.dump(enrollments, f, indent=4)

    @staticmethod
    def delete_enrollment(student_email: str, course_id: str) -> bool:
        enrollments = EnrollmentManager.load_enrollments()
        initial_count = len(enrollments)
        
        # Filter out the enrollment to delete
        enrollments = [e for e in enrollments 
                      if not (e['student_email'] == student_email and e['course_id'] == course_id)]
        
        if len(enrollments) < initial_count:
            EnrollmentManager.save_enrollments(enrollments)
            return True
        return False

    @staticmethod
    def get_student_enrollments(student_email):
        enrollments = EnrollmentManager.load_enrollments()
        return [e for e in enrollments if e['student_email'] == student_email]
    
    @staticmethod
    def get_course_enrollments(course_id):
        enrollments = EnrollmentManager.load_enrollments()
        return [e for e in enrollments if e['course_id'] == course_id]

if not os.path.exists(COURSES_FILE):
    CourseManager.save_courses({})
if not os.path.exists(ENROLLMENTS_FILE):
    EnrollmentManager.save_enrollments([])

@app.template_filter('datetimeformat')
def datetimeformat(value, format='%B %d, %Y'):
    try:
        dt = datetime.datetime.fromisoformat(value)
        return dt.strftime(format)
    except Exception:
        return value
    
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'role' not in session or session['role'] != 'admin':
            flash("Unauthorized - Admin access required", "error")
            app.logger.warning(f"Unauthorized admin access attempt by {session.get('email', 'unknown')}")
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

    
@app.route("/")
@app.route("/about")
def about():
    return render_template('about.html')

@app.route("/signUp", methods=['GET', 'POST'])
def signup_page():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm-password')
        role = request.form.get('role')  

        if password != confirm_password:
            flash("Passwords do not match", "error")
            app.logger.warning(f"Password mismatch during signup for {email}")
            return redirect(url_for('signup_page'))

        if UserManager.email_exists(email):
            flash("Email already registered", "error")
            app.logger.warning(f"Failed sign up attempt for email: {email} ({email} already exist) ")
            return redirect(url_for('signup_page'))

        hashed_password = generate_password_hash(password)
        new_user = User(
            email=email,
            username=username,
            password_hash=hashed_password,
            role=role,
            created_at=datetime.datetime.now().isoformat()
        )
        
        UserManager.add_user(new_user)
        flash("Account created successfully! Please log in.", "success")
        app.logger.info(f"New {role} account created: {email}")
        return redirect(url_for('login'))

    return render_template('signUp.html')


@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        role = request.form.get('role')
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = UserManager.get_user(email)
        
        if not user:
            flash("Invalid email or password", "error")
            app.logger.warning(f"Failed login attempt for email: {email}")
            return redirect(url_for('login'))

        if user.role != role:
            flash("Invalid role for this account", "error")
            app.logger.warning(f"Role mismatch for {email} (expected {role}, actual {user.role})")
            return redirect(url_for('login'))

        if user.verify_password(password):
            session['user_email'] = email
            session['username'] = user.username
            session['role'] = user.role
            flash(f"Welcome back, {user.username}!", "success")
            app.logger.info(f"User {email} logged in successfully")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid email or password", "error")
            app.logger.warning(f"Failed login attempt for email: {email}")
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route("/forgot_password", methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        
        if not UserManager.email_exists(email):
            flash("There is no account with this email")
            app.logger.warning(f"Password reset requested for non-existent email: {email}")
            return redirect(url_for('login'))
        
        token = TokenManager.generate_token(email)
        if send_reset_email(email, token):
            flash("Password reset link has been sent to your email", "success")
            app.logger.info(f"Password reset link has been sent to {email}")
        else:
            flash("Failed to send reset email. Please try again later.", "error")
            app.logger.warning(f"Failed to send password reset link for email: {email}")

        return redirect(url_for('login'))
    
    return render_template('forgot_password.html')

@app.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_password(token):
    valid, email = TokenManager.validate_token(token)
    
    if not valid:
        flash("Invalid or expired token", "error")
        app.logger.warning(f"Invalid/expired token used: {token}")
        return redirect(url_for('forgot_password'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash("Passwords do not match", "error")
            return redirect(url_for('reset_password', token=token))
        
        hashed_password = generate_password_hash(password)
        UserManager.update_user(email, password_hash=hashed_password)
        TokenManager.delete_token(token)
        
        flash("Password updated successfully! Please login with your new password.", "success")
        app.logger.info(f"Password for user {email} has changed successfully")
        return redirect(url_for('login'))
    
    return render_template('reset_password.html', token=token)

@app.route("/dashboard")
def dashboard():
    if 'user_email' not in session:
        flash("You have to login first", "error")
        return redirect(url_for('login'))
    
    user_email = session['user_email']
    role = session['role']
    username = session.get('username')

    days = ['Saturday', 'Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    today = (datetime.datetime.now().weekday() + 2) % 7
    current_day = days[today]
    next_day = days[(today + 1) % 7]

    now = datetime.datetime.now()
    current_time = now.time()

    # Load all courses once at the beginning
    all_courses = CourseManager.load_courses()

    if role == 'student':
        enrollments = EnrollmentManager.get_student_enrollments(user_email)
        courses = [all_courses.get(e['course_id']) for e in enrollments]
        courses = [c for c in courses if c]  # Filter out None values
        
        # Calculate total hours for student
        total_hours = sum(
            schedule['duration'] 
            for course in courses 
            for schedule in course['schedule']
        )
    else:
        # Teacher section
        courses = [c for c in all_courses.values() if c['teacher'] == user_email]
        
        # Calculate total students and hours for teacher
        total_students = 0
        total_hours = 0
        for course in courses:
            enrollments = EnrollmentManager.get_course_enrollments(course['id'])
            student_count = len(enrollments)
            course['student_count'] = student_count
            total_students += student_count
            total_hours += sum(schedule['duration'] for schedule in course['schedule'])

    ongoing_classes = []
    today_upcoming_classes = []
    tomorrow_classes = []
    
    for course in courses:
        if course:
            for schedule in course['schedule']:
                if schedule['day'] == current_day:
                    try:
                        course_time = datetime.datetime.strptime(schedule['time'], "%H:%M").time()
                        end_time = (datetime.datetime.combine(now.date(), course_time) + 
                                  datetime.timedelta(hours=schedule['duration']))
                        end_time = end_time.time()
                        
                        # Create a course entry with specific schedule
                        course_entry = course.copy()
                        course_entry['time'] = schedule['time']
                        course_entry['duration'] = schedule['duration']
                        
                        if course_time <= current_time < end_time:
                            ongoing_classes.append(course_entry)
                        elif current_time < course_time:
                            today_upcoming_classes.append(course_entry)
                    except ValueError:
                        continue
                elif schedule['day'] == next_day:
                    course_entry = course.copy()
                    course_entry['time'] = schedule['time']
                    course_entry['duration'] = schedule['duration']
                    tomorrow_classes.append(course_entry)
    
    # Sort all sections by time
    ongoing_classes.sort(key=lambda x: x['time'])
    today_upcoming_classes.sort(key=lambda x: x['time'])
    tomorrow_classes.sort(key=lambda x: x['time'])

    return render_template('dashboard.html',
                         role=role,
                         username=username,
                         ongoing_classes=ongoing_classes,
                         today_upcoming_classes=today_upcoming_classes,
                         tomorrow_classes=tomorrow_classes,
                         current_day=current_day,
                         next_day=next_day,
                         total_hours=total_hours,
                         enrollments=enrollments if role == 'student' else None,
                         courses_teaching=courses if role == 'teacher' else None,
                         total_students=total_students if role == 'teacher' else None)
    

@app.route("/courses")
def courses():
    if 'user_email' not in session:
        flash("You need to login first", "error")
        return redirect(url_for('login'))
    
    role = session['role']
    user_email = session['user_email']
    all_courses = list(CourseManager.load_courses().values())

    # Filters
    day_filter = request.args.get('day')
    time_filter = request.args.get('time')
    only_my_courses = request.args.get('only_my_courses') == 'on'
    only_enrolled = request.args.get('only_enrolled') == 'on'
    not_enrolled = request.args.get('not_enrolled') == 'on'

    # Initial filtered list
    filtered_courses = all_courses

    # Apply Day filter
    if day_filter:
        filtered_courses = [
            c for c in filtered_courses 
            if any(schedule['day'] == day_filter for schedule in c['schedule'])
        ]

    # Apply Time filter
    if time_filter:
        filtered_courses = [
            c for c in filtered_courses 
            if any(is_time_in_range(schedule['time'], time_filter) 
                  for schedule in c['schedule'])
        ]

    # Enrollment info
    enrolled_course_ids = []
    if role == 'student':
        enrollments = EnrollmentManager.get_student_enrollments(user_email)
        enrolled_course_ids = [e['course_id'] for e in enrollments]

        if only_enrolled:
            filtered_courses = [c for c in filtered_courses if c['id'] in enrolled_course_ids]
        elif not_enrolled:
            filtered_courses = [c for c in filtered_courses if c['id'] not in enrolled_course_ids]

    elif role == 'teacher' and only_my_courses:
        filtered_courses = [c for c in filtered_courses if c['teacher'] == user_email]

    return render_template('courses.html',
                         role=role,
                         username=session.get('username'),
                         courses=filtered_courses,
                         enrolled_course_ids=enrolled_course_ids)


@app.route("/courses/create", methods=['GET', 'POST'])
def create_course():
    if 'user_email' not in session or session['role'] != 'teacher':
        flash("Unauthorized", "error")
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Load existing courses first
        courses = CourseManager.load_courses()
        course_id = str(len(courses) + 1)
        
        # Get days, times and durations as lists
        days = request.form.getlist('day[]')
        times = request.form.getlist('time[]')
        durations = request.form.getlist('duration[]')
        
        # Create schedule list
        schedule = []
        for i in range(len(days)):
            if days[i] and times[i] and durations[i]:  # Ensure all fields are present
                schedule.append({
                    'day': days[i],
                    'time': times[i],
                    'duration': int(durations[i])
                })

        new_course = {
            'id': course_id,
            'name': request.form.get('name'),
            'teacher': session['user_email'],
            'teacher_name': session['username'],
            'schedule': schedule,
            'max_students': int(request.form.get('max_students')),
            'current_students': 0
        }

        # Check for conflicts with teacher's existing courses
        teacher_courses = [c for c in courses.values() if c['teacher'] == session['user_email']]
        
        for existing_course in teacher_courses:
            if are_courses_conflicting(existing_course, new_course):
                flash(f"This schedule conflicts with your course '{existing_course['name']}'", "error")
                return redirect(url_for('create_course'))
        
        # If no conflicts, save the new course
        courses[course_id] = new_course
        CourseManager.save_courses(courses)
        
        flash("Course created successfully!", "success")
        app.logger.info(f"New course created by {session['user_email']}: {new_course['name']}")
        return redirect(url_for('courses'))
    
    # For GET request, show existing schedules
    existing_courses = CourseManager.load_courses()
    teacher_courses = [c for c in existing_courses.values() if c['teacher'] == session['user_email']]
    
    return render_template('create_course.html',
                         role=session['role'],
                         username=session.get('username'),
                         teacher_courses=teacher_courses)

@app.route("/course/<course_name>")
def course_detail(course_name):
    if 'user_email' not in session:
        flash("You need to login first", "error")
        return redirect(url_for('login'))
    
    courses = CourseManager.load_courses()
    course = None
    for c in courses.values():
        if c['name'].lower().replace(' ', '-') == course_name.lower():
            course = c
            break
    
    if not course:
        flash("Course not found", "error")
        return redirect(url_for('courses'))
    
    role = session['role']
    user_email = session['user_email']
    is_enrolled = False
    students = []
    is_teacher_of_course = False
    
    # Calculate total hours per week
    total_hours = sum(schedule['duration'] for schedule in course['schedule'])
    
    # Sort schedules by day and time
    days_order = {
        'Saturday': 0, 'Sunday': 1, 'Monday': 2, 
        'Tuesday': 3, 'Wednesday': 4, 'Thursday': 5, 'Friday': 6
    }
    sorted_schedules = sorted(
        course['schedule'], 
        key=lambda x: (days_order[x['day']], x['time'])
    )
    
    # Get current schedule if any
    now = datetime.datetime.now()
    current_day = ['Saturday', 'Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'][
        (now.weekday() + 2) % 7
    ]
    current_time = now.time()
    current_schedule = None
    next_schedule = None
    
    for schedule in sorted_schedules:
        if schedule['day'] == current_day:
            schedule_time = datetime.datetime.strptime(schedule['time'], "%H:%M").time()
            end_time = (datetime.datetime.combine(now.date(), schedule_time) + 
                       datetime.timedelta(hours=schedule['duration'])).time()
            
            if schedule_time <= current_time <= end_time:
                current_schedule = schedule
                break
            elif current_time < schedule_time:
                if not next_schedule:
                    next_schedule = schedule
    
    if not current_schedule and not next_schedule:
        # Look for next schedule in coming days
        found_today = False
        for schedule in sorted_schedules:
            if not found_today and schedule['day'] == current_day:
                found_today = True
                continue
            if found_today or days_order[schedule['day']] > days_order[current_day]:
                next_schedule = schedule
                break
        if not next_schedule and sorted_schedules:  # If we reached end of week, take first schedule
            next_schedule = sorted_schedules[0]
    
    if role == "teacher":
        is_teacher_of_course = (course['teacher'] == user_email)
    
    if role == 'student':
        enrollments = EnrollmentManager.get_student_enrollments(user_email)
        is_enrolled = any(e['course_id'] == course['id'] for e in enrollments)
    elif is_teacher_of_course:
        enrollments = EnrollmentManager.get_course_enrollments(course['id'])
        students = []
        for e in enrollments:
            user = UserManager.get_user(e['student_email'])
            if user:
                students.append(user)
    
    is_full = course['current_students'] >= course['max_students']
    
    return render_template('course_detail.html',
                         course=course,
                         role=role,
                         username=session.get('username'),
                         is_enrolled=is_enrolled,
                         is_full=is_full,
                         students=students,
                         is_teacher_of_course=is_teacher_of_course,
                         total_hours=total_hours,
                         sorted_schedules=sorted_schedules,
                         current_schedule=current_schedule,
                         next_schedule=next_schedule,
                         current_day=current_day)

@app.route('/remove_student', methods=['POST'])
def remove_student():
    if 'user_email' not in session or session.get('role') != 'teacher':
        flash("Unauthorized", "error")
        return redirect(url_for('login'))
    
    course_id = request.form.get('course_id')
    student_email = request.form.get('student_email')
    course_name = request.form.get('course_name')
    
    # Verify the teacher owns this course
    course = CourseManager.get_course(course_id)
    if not course or course['teacher'] != session['user_email']:
        flash("Unauthorized - You don't teach this course", "error")
        return redirect(url_for('courses'))
    
    # Your removal logic here
    enrollments = EnrollmentManager.load_enrollments()
    enrollments = [e for e in enrollments if not (e['course_id'] == course_id and e['student_email'] == student_email)]
    EnrollmentManager.save_enrollments(enrollments)
    
    CourseManager.decrement_students(course_id)
    
    flash("Student removed successfully", "success")
    app.logger.info(f"{session['user_email']} removed student {student_email} from course {course_id}")
    return redirect(url_for('course_detail',
                         course_name=course_name))

@app.route('/delete_course', methods=['POST'])
def delete_course():
    if 'user_email' not in session or session['role'] != 'teacher':
        flash("Unauthorized", "error")
        return redirect(url_for('login'))
    
    course_id = request.form.get('course_id')
    
    # Verify the teacher owns this course
    course = CourseManager.get_course(course_id)
    if not course or course['teacher'] != session['user_email']:
        flash("Unauthorized - You don't teach this course", "error")
        return redirect(url_for('courses'))
    
    # Remove course from courses
    courses = CourseManager.load_courses()
    if course_id in courses:
        del courses[course_id]
        CourseManager.save_courses(courses)
    
    # Remove all enrollments for this course
    enrollments = EnrollmentManager.load_enrollments()
    enrollments = [e for e in enrollments if e['course_id'] != course_id]
    EnrollmentManager.save_enrollments(enrollments)
    
    flash("Course deleted successfully", "success")
    app.logger.info(f"{session['user_email']} deleted course {course_id}")
    return redirect(url_for('courses'))

@app.route("/enroll", methods=['POST'])
def enroll_course():
    if 'user_email' not in session or session['role'] != 'student':
        flash("Unauthorized", "error")
        return redirect(url_for('login'))
    
    course_id = request.form.get('course_id')
    course = CourseManager.get_course(course_id)
    enrollments = EnrollmentManager.load_enrollments()
    
    if course['current_students'] >= course['max_students']:
        flash("This course is already full", "error")
        return redirect(url_for('courses'))
    
    enrollments = EnrollmentManager.load_enrollments()

    if any(e['student_email'] == session['user_email'] and e['course_id'] == course_id for e in enrollments):
        flash("You are already enrolled in this course", "error")
        return redirect(url_for('courses'))
    
    course = CourseManager.get_course(course_id)
    student_courses = EnrollmentManager.get_student_enrollments(session['user_email'])
    
    for enrolled in student_courses:
        enrolled_course = CourseManager.get_course(enrolled['course_id'])
        if are_courses_conflicting(enrolled_course, course):
            flash("This course conflicts with another course you're enrolled in", "error")
            return redirect(url_for('courses'))
    
    enrollments.append({'student_email': session['user_email'], 'course_id': course_id})
    EnrollmentManager.save_enrollments(enrollments)
    CourseManager.increment_students(course_id)
    
    flash("Successfully enrolled in the course!", "success")
    app.logger.info(f"Student {session['user_email']} enrolled in course {course_id}")
    return redirect(url_for('courses'))

@app.route("/unenroll", methods=['POST'])
def unenroll_course():
    if 'user_email' not in session or session['role'] != 'student':
        flash("Unauthorized", "error")
        return redirect(url_for('login'))
    
    course_id = request.form.get('course_id')
    enrollments = EnrollmentManager.load_enrollments()
    enrollments = [e for e in enrollments if not (e['student_email'] == session['user_email'] and e['course_id'] == course_id)]
    EnrollmentManager.save_enrollments(enrollments)
    CourseManager.decrement_students(course_id)
    
    flash("Successfully unenrolled from the course", "success")
    app.logger.info(f"Student {session['user_email']} unenrolled from course {course_id}")
    return redirect(url_for('courses'))

def is_time_in_range(time_str, time_range):
    hour = int(time_str.split(':')[0])
    if time_range == 'morning':
        return 8 <= hour < 12
    elif time_range == 'afternoon':
        return 12 <= hour < 17
    elif time_range == 'evening':
        return 17 <= hour < 21
    return False

@app.route("/calendar")
def calendar():
    if 'user_email' not in session:
        flash("You need to login first", "error")
        return redirect(url_for('login'))
    
    user_email = session['user_email']
    role = session['role']
    
    if role == 'student':
        enrollments = EnrollmentManager.get_student_enrollments(user_email)
        courses = [CourseManager.get_course(e['course_id']) for e in enrollments if CourseManager.get_course(e['course_id'])]
    else:
        all_courses = CourseManager.load_courses()
        courses = [c for c in all_courses.values() if c['teacher'] == session['user_email']]
        
        enrollments = EnrollmentManager.load_enrollments()
        enrollment_counts = {}
        for e in enrollments:
            enrollment_counts[e['course_id']] = enrollment_counts.get(e['course_id'], 0) + 1
        
        for course in courses:
            course['student_count'] = enrollment_counts.get(course['id'], 0)

    days = ['Saturday', 'Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    calendar_data = {day: [] for day in days}
    
    for course in courses:
        if course:
            for schedule in course['schedule']:
                day = schedule['day']
                if day in calendar_data:
                    # Create a copy of course data with specific schedule
                    course_entry = course.copy()
                    course_entry['time'] = schedule['time']
                    course_entry['duration'] = schedule['duration']
                    calendar_data[day].append(course_entry)
    
    for day in calendar_data:
        calendar_data[day].sort(key=lambda x: x['time'])
    
    return render_template('calendar.html', 
                         calendar_data=calendar_data, 
                         role=role,
                         username=session.get('username'))

@app.route("/profile")
def profile():
    if 'user_email' not in session:
        flash("You need to login first", "error")
        return redirect(url_for('login'))

    email = session['user_email']
    role = session['role']
    username = session['username']
    user = UserManager.get_user(email)

    enrollments = None
    courses_teaching = None

    if role == "student":
        enrollments = EnrollmentManager.get_student_enrollments(email)
    elif role == "teacher":
        all_courses = CourseManager.load_courses()
        courses_teaching = [course for course in all_courses.values() if course['teacher'] == email]

    return render_template('profile.html',
                           email=email,
                           role=role,
                           username=username,
                           user=user,
                           enrollments=enrollments,
                           courses_teaching=courses_teaching)

@app.route("/settings")
def settings():
    if 'user_email' not in session:
        flash("You need to login first", "error")
        return redirect(url_for('login'))
    email = session['user_email']
    role = session['role']
    username = session['username']
    user = UserManager.get_user(email)
    
    return render_template('settings.html', 
                         email=email,
                         role=role,
                         username=username,
                         user=user)

@app.route("/update_username", methods=['POST'])
def update_username():
    if 'user_email' not in session:
        flash("You need to login first", "error")
        return redirect(url_for('login'))
    
    new_username = request.form.get('new_username')
    password = request.form.get('password')
    user_email = session['user_email']
    
    user = UserManager.get_user(user_email)
    if not user or not user.verify_password(password):
        flash("Incorrect password", "error")
        return redirect(url_for('settings'))
    
    if UserManager.update_user(user_email, username=new_username):
        session['username'] = new_username
        flash("Username updated successfully!", "success")
        app.logger.info(f"User {user_email} updated username to {new_username}")
    else:
        flash("Failed to update username", "error")
        app.logger.error(f"Failed to update username for {user_email}")
    
    return redirect(url_for('settings'))

@app.route("/update_password", methods=['POST'])
def update_password():
    if 'user_email' not in session:
        flash("You need to login first", "error")
        return redirect(url_for('login'))
    
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    user_email = session['user_email']
    
    if new_password != confirm_password:
        flash("New passwords do not match", "error")
        return redirect(url_for('settings'))
    
    user = UserManager.get_user(user_email)
    if not user or not user.verify_password(current_password):
        flash("Current password is incorrect", "error")
        return redirect(url_for('settings'))
    
    hashed_password = generate_password_hash(new_password)
    if UserManager.update_user(user_email, password_hash=hashed_password):
        flash("Password updated successfully!", "success")
        app.logger.info(f"User {user_email} changed their password")
    else:
        flash("Failed to update password", "error")
        app.logger.error(f"Failed to update password for {user_email}")
    
    return redirect(url_for('settings'))

@app.route("/delete_account", methods=['POST'])
def delete_account():
    if 'user_email' not in session:
        flash("You need to login first", "error")
        return redirect(url_for('login'))
    
    password = request.form.get('password')
    user_email = session['user_email']
    
    user = UserManager.get_user(user_email)
    if not user or not user.verify_password(password):
        flash("Incorrect password", "error")
        return redirect(url_for('settings'))
    
    # Delete user's enrollments if they're a student
    if session['role'] == 'student':
        enrollments = EnrollmentManager.load_enrollments()
        enrollments = [e for e in enrollments if e['student_email'] != user_email]
        EnrollmentManager.save_enrollments(enrollments)
        
        # Decrement student counts in courses
        for enrollment in enrollments:
            CourseManager.decrement_students(enrollment['course_id'])
    
    # Delete courses if they're a teacher
    if session['role'] == 'teacher':
        courses = CourseManager.load_courses()
        # Find all course IDs taught by this teacher
        teacher_course_ids = [course_id for course_id, course in courses.items() if course['teacher'] == user_email]
        
        # Delete these courses
        for course_id in teacher_course_ids:
            del courses[course_id]
        
        CourseManager.save_courses(courses)
        
        # Delete enrollments for these courses
        enrollments = EnrollmentManager.load_enrollments()
        enrollments = [e for e in enrollments if e['course_id'] not in teacher_course_ids]
        EnrollmentManager.save_enrollments(enrollments)
    
    # Delete the user
    users = UserManager.load_users()
    if user_email in users:
        del users[user_email]
        UserManager.save_users(users)
    
    # Clear session and logout
    session.clear()
    flash("Your account has been permanently deleted", "success")
    app.logger.info(f"Account deleted: {user_email}")
    return redirect(url_for('login'))

@app.route("/logout")
def logout():
    user_email = session.get('user_email', 'unknown')
    session.pop('user_email', None)
    session.pop('username', None)
    session.pop('role', None)
    flash("You have been logged out", "success")
    app.logger.info(f"User {user_email} logged out")
    return redirect(url_for('login'))

@app.route('/api/courses', methods=['GET'])
def get_courses_api():
    courses = CourseManager.load_courses()
    return json.dumps(list(courses.values()))

def are_courses_conflicting(course1, course2):
    def time_to_minutes(time_str):
        h, m = map(int, time_str.split(':'))
        return h * 60 + m

    # Check each schedule combination for conflicts
    for schedule1 in course1['schedule']:
        for schedule2 in course2['schedule']:
            if schedule1['day'] != schedule2['day']:
                continue

            start1 = time_to_minutes(schedule1['time'])
            end1 = start1 + int(schedule1['duration'] * 60)

            start2 = time_to_minutes(schedule2['time'])
            end2 = start2 + int(schedule2['duration'] * 60)

            if not (end1 <= start2 or end2 <= start1):
                return True
    
    return False

@app.route("/admin/login", methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = UserManager.get_user(email)

        if not user or user.role != 'admin':
            flash("Invalid admin credentials", "error")
            app.logger.warning(f"Admin login failed for {email}")
            return redirect(url_for('admin_login'))

        if user.verify_password(password):
            session['user_email'] = email
            session['username'] = user.username
            session['role'] = user.role
            flash(f"Welcome back, Admin {user.username}!", "success")
            app.logger.info(f"Admin {email} logged in successfully")
            return redirect(url_for('admin_dashboard'))
        else:
            flash("Invalid admin credentials", "error")
            app.logger.warning(f"Admin login failed for {email}")
            return redirect(url_for('admin_login'))

    return render_template('admin_login.html')



@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    users = UserManager.load_users()
    courses = CourseManager.load_courses()
    enrollments = EnrollmentManager.load_enrollments()
    
    # Statistics
    total_users = len(users)
    total_courses = len(courses)
    total_enrollments = len(enrollments)
    
    # Recent activity (last 5 users)
    recent_users = sorted(users.values(), 
                         key=lambda u: u.created_at, 
                         reverse=True)[:5]
    
    return render_template('admin_dashboard.html',
                         total_users=total_users,
                         total_courses=total_courses,
                         total_enrollments=total_enrollments,
                         recent_users=recent_users,
                         username=session.get('username'))
@app.route("/admin/users")
@admin_required
def admin_users():
    users = UserManager.load_users()
    return render_template('admin_users.html',
                         users=users.values(),
                         username=session.get('username'))

@app.route("/admin/courses")
@admin_required
def admin_courses():
    courses = CourseManager.load_courses()
    users = UserManager.load_users()
    
    course_list = []
    for course_id, course in courses.items():
        teacher = users.get(course['teacher'])
        
        # Calculate total hours per week
        total_hours = sum(schedule['duration'] for schedule in course['schedule'])
        
        course_data = {
            'id': course_id,
            'name': course['name'],
            'teacher': course['teacher'],
            'teacher_name': teacher.username if teacher else 'Unknown',
            'schedule': course['schedule'],
            'total_hours': total_hours,
            'max_students': course['max_students'],
            'current_students': course.get('current_students', 0)
        }
        course_list.append(course_data)
    
    return render_template('admin_courses.html',
                         courses=course_list,
                         username=session.get('username'))

@app.route("/admin/enrollments")
@admin_required
def admin_enrollments():
    enrollments = EnrollmentManager.load_enrollments()
    courses = CourseManager.load_courses()
    users = UserManager.load_users()
    
    enhanced_enrollments = []
    for e in enrollments:
        course = courses.get(e['course_id'])
        user = users.get(e['student_email'])
        if course and user:
            teacher = users.get(course['teacher'])
            enhanced_enrollments.append({
                'course_name': course['name'],
                'student_name': user.username,
                'teacher_name': teacher.username if teacher else 'Unknown',
                'schedule': course['schedule'],
                'student_email': e['student_email'],
                'course_id': e['course_id']
            })
    
    return render_template('admin_enrollments.html',
                         enrollments=enhanced_enrollments,
                         username=session.get('username'))

@app.route("/admin/logs")
@admin_required
def admin_logs():
    try:
        with open(LOG_FILE, 'r') as f:
            logs = f.readlines()
        logs = [log.strip() for log in logs][-200:]  # Get last 200 lines
    except FileNotFoundError:
        logs = ["No log file found"]
    
    return render_template('admin_logs.html',
                         logs=reversed(logs), 
                         username=session.get('username'))

@app.route("/admin/delete_user", methods=['POST'])
@admin_required
def admin_delete_user():
    email = request.form.get('email')
    if not email:
        flash("No email provided", "error")
        return redirect(url_for('admin_users'))
    
    if email == session.get('user_email'):
        flash("You cannot delete your own account from here", "error")
        return redirect(url_for('admin_users'))
    
    if UserManager.delete_user(email):
        # Also delete enrollments for this user
        enrollments = EnrollmentManager.load_enrollments()
        enrollments = [e for e in enrollments if e['student_email'] != email]
        EnrollmentManager.save_enrollments(enrollments)
        
        flash(f"User {email} deleted successfully", "success")
        app.logger.info(f"User {email} deleted by admin {session.get('user_email')}")
    else:
        flash("User not found", "error")
    
    return redirect(url_for('admin_users'))

@app.route("/admin/delete_course", methods=['POST'])
@admin_required
def admin_delete_course():
    course_id = request.form.get('course_id')
    if not course_id:
        flash("No course ID provided", "error")
        return redirect(url_for('admin_courses'))
    
    courses = CourseManager.load_courses()
    if course_id not in courses:
        flash("Course not found", "error")
        return redirect(url_for('admin_courses'))
    
    # Delete the course
    del courses[course_id]
    CourseManager.save_courses(courses)
    
    # Delete enrollments for this course
    enrollments = EnrollmentManager.load_enrollments()
    enrollments = [e for e in enrollments if e['course_id'] != course_id]
    EnrollmentManager.save_enrollments(enrollments)
    
    flash("Course deleted successfully", "success")
    app.logger.info(f"Course {course_id} deleted by admin {session.get('user_email')}")
    return redirect(url_for('admin_courses'))

@app.route("/admin/delete_enrollment", methods=['POST'])
@admin_required
def admin_delete_enrollment():
    student_email = request.form.get('student_email')
    course_id = request.form.get('course_id')
    
    if not student_email or not course_id:
        flash("Missing student email or course ID", "error")
        return redirect(url_for('admin_enrollments'))
    
    if EnrollmentManager.delete_enrollment(student_email, course_id):
        # Decrement student count in course
        CourseManager.decrement_students(course_id)
        flash("Enrollment deleted successfully", "success")
        app.logger.info(f"Enrollment deleted: student {student_email} from course {course_id} by admin {session.get('user_email')}")
    else:
        flash("Enrollment not found", "error")
    
    return redirect(url_for('admin_enrollments'))

@app.route("/admin/clear_logs", methods=['POST'])
@admin_required
def admin_clear_logs():
    try:
        # Clear the log file
        with open(LOG_FILE, 'w') as f:
            f.write('')
        
        # Also clear the log handler
        for handler in app.logger.handlers:
            if isinstance(handler, logging.FileHandler):
                handler.close()
                app.logger.removeHandler(handler)
        
        # Re-add the handler to continue logging
        handler = RotatingFileHandler(LOG_FILE, maxBytes=10000, backupCount=3)
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        app.logger.addHandler(handler)
        
        flash("Logs cleared successfully", "success")
        app.logger.info("Logs cleared by admin")
        return jsonify({"success": True})
    except Exception as e:
        app.logger.error(f"Failed to clear logs: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)