# Course Management System - Project Structure

```markdown
/Course-Management-System

├── app/
│ ├── models/
│ │ ├── init.py
│ │ ├── course.py
│ │ ├── enrollment.py
│ │ └── user.py
│ ├── routes/
│ │ ├── init.py
│ │ ├── admin.py
│ │ ├── auth.py
│ │ ├── courses.py
│ │ └── main.py
│ ├── services/
│ │ ├── init.py
│ │ ├── course_manager.py
│ │ ├── enrollment_manager.py
│ │ ├── token_manager.py
│ │ └── user_manager.py
│ ├── static/
│ │ └── w3.css
│ ├── templates/
│ │ ├── about.html
│ │ ├── add_admin.html
│ │ ├── admin_courses.html
│ │ ├── admin_dashboard.html
│ │ ├── admin_enrollments.html
│ │ ├── admin_login.html
│ │ ├── admin_logs.html
│ │ ├── admin_users.html
│ │ ├── calendar.html
│ │ ├── course_detail.html
│ │ ├── courses.html
│ │ ├── create_course.html
│ │ ├── dashboard.html
│ │ ├── forgot_password.html
│ │ ├── login.html
│ │ ├── profile.html
│ │ ├── reset_password.html
│ │ ├── settings.html
│ │ └── signUp.html
│ ├── utils/
│ │ ├── init.py
│ │ ├── decorators.py
│ │ └── helpers.py
│ ├── init.py
│ └── config.py
├── data/
│ ├── (JSON data files will be created here)
├── app.log
├── run.py
└── requirements.txt
```
