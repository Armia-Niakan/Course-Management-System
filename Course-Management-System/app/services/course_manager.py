import json
from flask import current_app


class CourseManager:
    @staticmethod
    def load_courses():
        path = current_app.config['COURSES_FILE']
        try:
            with open(path, 'r') as f:
                courses = json.load(f)
                for course in courses.values():
                    course.setdefault('current_students', 0)
                return courses
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    @staticmethod
    def save_courses(courses):
        path = current_app.config['COURSES_FILE']
        with open(path, 'w') as f:
            json.dump(courses, f, indent=4)

    @staticmethod
    def get_course(course_id):
        return CourseManager.load_courses().get(course_id)

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
