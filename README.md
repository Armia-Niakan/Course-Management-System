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

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/course-management-system.git
   cd course-management-system
