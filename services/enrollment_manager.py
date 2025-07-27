import json
from flask import current_app


class EnrollmentManager:
    @staticmethod
    def load_enrollments():
        path = current_app.config['ENROLLMENTS_FILE']
        try:
            with open(path, 'r') as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    @staticmethod
    def save_enrollments(enrollments):
        path = current_app.config['ENROLLMENTS_FILE']
        with open(path, 'w') as f:
            json.dump(enrollments, f, indent=4)

    @staticmethod
    def delete_enrollment(student_email: str, course_id: str) -> bool:
        enrollments = EnrollmentManager.load_enrollments()
        original_count = len(enrollments)
        enrollments = [e for e in enrollments if not (e['student_email'] == student_email and e['course_id'] == course_id)]
        if len(enrollments) < original_count:
            EnrollmentManager.save_enrollments(enrollments)
            return True
        return False

    @staticmethod
    def get_student_enrollments(student_email):
        return [e for e in EnrollmentManager.load_enrollments() if e['student_email'] == student_email]

    @staticmethod
    def get_course_enrollments(course_id):
        return [e for e in EnrollmentManager.load_enrollments() if e['course_id'] == course_id]
