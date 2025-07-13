# Course Management System

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![Flask](https://img.shields.io/badge/flask-%23000.svg?style=for-the-badge&logo=flask&logoColor=white)
![HTML5](https://img.shields.io/badge/html5-%23E34F26.svg?style=for-the-badge&logo=html5&logoColor=white)
![CSS3](https://img.shields.io/badge/css3-%231572B6.svg?style=for-the-badge&logo=css3&logoColor=white)

A comprehensive Course Management System built with Python Flask that allows students, teachers, and administrators to manage courses, enrollments, and schedules.

## Features

### User Management
- **Three user roles**: Student, Teacher, Admin
- Secure password hashing with Werkzeug
- Password reset functionality via email
- Profile management (username/password updates)

### Course Management
- Create/edit/delete courses
- Schedule management with day/time/duration
- Conflict detection for overlapping schedules
- Enrollment capacity limits

### Dashboard Features
- Today's schedule view
- Upcoming classes
- Weekly calendar view
- Course statistics

### Admin Features
- User management (view/delete users)
- Course management
- Enrollment management
- System logs viewer

## Technical Details

### Backend
- Python 3
- Flask web framework
- JSON-based data storage
- SMTP email integration
- Comprehensive logging system

### Frontend
- HTML5
- W3.CSS framework
- Responsive design
- Font Awesome icons

## Requirements
- Python 3.6+
- Flask 3.1.0: Install via pip install flask
- Werkzeug 3.1.3
  ```bash
  pip install -r requirements.txt

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/armia05/course-management-system.git
   cd course-management-system
2. Install requirements

3. Run the application:
   ```bash
   python app.py
4. Access the system at http://localhost:5000

## Default Admin Credentials
Email: admin@example.com

Password: 123456789

## Project Structure

## License
None

## Contact
Armia Niakan
armia.niakan@gmail.com
