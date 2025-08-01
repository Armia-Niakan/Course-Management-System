import json
import uuid
from flask import current_app

from app.models.exam import Exam
from app.services.submission_manager import SubmissionManager

class ExamManager:
    @staticmethod
    def get_exams_file_path():
        return current_app.config['EXAMS_FILE']

    @staticmethod
    def load_exams():
        path = ExamManager.get_exams_file_path()
        try:
            with open(path, 'r') as f:
                data = json.load(f)
                return {exam_id: Exam.from_dict(exam_data) for exam_id, exam_data in data.items()}
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    @staticmethod
    def save_exams(exams):
        path = ExamManager.get_exams_file_path()
        with open(path, 'w') as f:
            json.dump({exam_id: exam.to_dict() for exam_id, exam in exams.items()}, f, indent=4)

    @staticmethod
    def add_exam(exam: Exam):
        exams = ExamManager.load_exams()
        exam.id = str(uuid.uuid4())
        exams[exam.id] = exam
        ExamManager.save_exams(exams)
        return exam

    @staticmethod
    def get_exam(exam_id: str):
        return ExamManager.load_exams().get(exam_id)

    @staticmethod
    def get_exams_for_course(course_id: str):
        all_exams = ExamManager.load_exams().values()
        return [exam for exam in all_exams if exam.course_id == course_id]

    @staticmethod
    def delete_exam(exam_id: str):
        exams = ExamManager.load_exams()
        if exam_id in exams:
            del exams[exam_id]
            ExamManager.save_exams(exams)
            SubmissionManager.delete_submissions_for_exam(exam_id)
            return True
        return False

