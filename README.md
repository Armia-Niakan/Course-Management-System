Course Management System
https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54
https://img.shields.io/badge/flask-%2523000.svg?style=for-the-badge&logo=flask&logoColor=white
https://img.shields.io/badge/html5-%2523E34F26.svg?style=for-the-badge&logo=html5&logoColor=white
https://img.shields.io/badge/css3-%25231572B6.svg?style=for-the-badge&logo=css3&logoColor=white

A comprehensive Course Management System built with Python Flask that allows students, teachers, and administrators to manage courses, enrollments, and schedules.

Features
User Management
Three user roles: Student, Teacher, Admin

Secure password hashing with Werkzeug

Password reset functionality via email

Profile management (username/password updates)

Course Management
Create/edit/delete courses

Schedule management with day/time/duration

Conflict detection for overlapping schedules

Enrollment capacity limits

Dashboard Features
Today's schedule view

Upcoming classes

Weekly calendar view

Course statistics

Admin Features
User management (view/delete users)

Course management

Enrollment management

System logs viewer

Technical Details
Backend
Python 3

Flask web framework

JSON-based data storage

SMTP email integration

Comprehensive logging system

Frontend
HTML5

W3.CSS framework

Responsive design

Font Awesome icons

Installation
Clone the repository:

bash
git clone https://github.com/yourusername/course-management-system.git
cd course-management-system
Install dependencies:

bash
pip install -r requirements.txt
Configure environment:

Set up email credentials in app.py (SMTP_SERVER, EMAIL_ADDRESS, etc.)

Configure any other settings as needed

Run the application:

bash
python app.py
Access the system at http://localhost:5000

Default Admin Credentials
Email: admin@example.com

Password: 123456789

Project Structure
text
course-management-system/
├── app.py                # Main application file
├── static/               # Static files (CSS, JS)
├── templates/            # HTML templates
│   ├── about.html        # About page
│   ├── admin/            # Admin templates
│   ├── auth/             # Authentication templates
│   └── ...               # Other templates
├── *.json                # Data storage files
└── README.md             # This file
Screenshots
https://screenshots/dashboard.png
Dashboard view for teachers

https://screenshots/courses.png
Course management interface

https://screenshots/calendar.png
Weekly calendar view

License
This project is licensed under the MIT License - see the LICENSE file for details.

Contact
Armia Niakan
armia.niakan@gmail.com
