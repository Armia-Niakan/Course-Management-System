# Course Management System

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![Flask](https://img.shields.io/badge/flask-%23000.svg?style=for-the-badge&logo=flask&logoColor=white)
![dotenv](https://img.shields.io/badge/dotenv-%23ECD53F.svg?style=for-the-badge&logo=dotenv&logoColor=black)
![HTML5](https://img.shields.io/badge/html5-%23E34F26.svg?style=for-the-badge&logo=html5&logoColor=white)
![W3.CSS](https://img.shields.io/badge/w3.css-%23FFFFFF.svg?style=for-the-badge&logo=w3schools&logoColor=%2304AA6D)

This a Course Management System developed as a project for Guilan university advanced programming class.

A comprehensive Course Management System built with Python and Flask. It provides a clean and efficient platform for students, teachers, and administrators to manage courses, enrollments, and schedules.

## Table of Contents
- [Key Features](#key-features)
  - [User & Role Management](#user--role-management)
  - [Course & Enrollment](#course--enrollment)
  - [Dashboards & Views](#dashboards--views)
  - [Admin Panel](#admin-panel)
- [Technical Details](#technical-details)
- [Requirements](#requirements)
- [Installation & Setup](#installation--setup)
- [Configuration](#configuration)
- [Security Note](#security-note)
- [Project Structure](#project-structure)
- [License](#license)
- [Contact](#contact)


## Key Features

#### User & Role Management
- **Three User Roles**: Student, Teacher, and Admin with distinct permissions.
- **Secure Authentication**: Secure password hashing using Werkzeug and session management.
- **Account Management**: Users can update their profile information and password.
- **Password Reset**: Secure "Forgot Password" functionality with email-based tokens.

#### Course & Enrollment
- Teachers can create, read, and delete their courses.
- **Smart Scheduling**: The system automatically detects and prevents schedule conflicts for both teachers and students.
- **Enrollment Control**: Courses have capacity limits, and students can enroll/unenroll with a single click.

#### Dashboards & Views
- **Personalized Dashboards**: Role-specific dashboards showing relevant stats, ongoing classes, and upcoming schedules.
- **Weekly Calendar**: A visual calendar view of a user's weekly class schedule.
- **Advanced Filtering**: Easily filter courses by day, time, enrollment status, or courses taught.

#### Admin Panel
- **System Oversight**: A dedicated admin dashboard with statistics on users, courses, and enrollments.
- **Centralized Management**: Admins can manage all users, courses, and enrollments in the system.
- **Activity Logging**: View system logs to monitor application activity and troubleshoot issues.

## Technical Details

- **Backend**: Python 3, Flask
- **Frontend**: HTML5, W3.CSS, Font Awesome Icons
- **Data Storage**: Data is managed using flat-file JSON, making the application portable and easy to set up.
- **Email Integration**: Uses `smtplib` for sending password reset emails.

## Requirements
- Python 3.7+
- All required packages are listed in `requirements.txt`.

## Installation & Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/Armia-Niakan/Course-Management-System.git
    cd Course-Management-System
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv env
    source env/bin/activate  # On Windows, use `env\Scripts\activate`
    ```

3.  **Install the requirements:**
    ```bash
    pip install -r requirements.txt
    ```
4. **Configurate .env file**
   
   You can use .env.example
    ```bash
    cp .env.example .env
    # Then edit .env with your values.
    ```
5.  **Run the application:**
    ```bash
    python run.py
    ```
6.  Access the system in your browser at `http://127.0.0.1:5000`.

## Configuration
Create a file named .env in the root directory (same level as run.py) and add the following environment variables:

```env
SECRET_KEY=your-secret-key

EMAIL_ADDRESS=your-email@gmail.com
EMAIL_PASSWORD=your-gmail-app-password

DEFAULT_ADMIN_EMAIL=admin@example.com
DEFAULT_ADMIN_USERNAME=admin
DEFAULT_ADMIN_PASSWORD=123456789
```
Make sure your .env file is NOT committed to Git. It should be listed in your .gitignore.

## Security Note
- Use an App Password for Gmail (you must enable 2-Step Verification on your Google account)
- Do not share your .env file or credentials publicly.
- Example .env is intentionally excluded from the repository for security reasons.

## Project Structure

<details>
<summary>View project structure</summary>
  
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
│ ├── courses.json
│ ├── enrollments.json
│ ├── reset_tokens.json
│ └── users.json
├── app.log
├── run.py
└── requirements.txt
```
</details>
  
## License
None

## Contact
Armia Niakan

armia.niakan@gmail.com

GitHub: Armia-Niakan
