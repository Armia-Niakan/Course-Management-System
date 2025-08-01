import json
from flask import current_app
from app.models.submission import Submission

class SubmissionManager:
    @staticmethod
    def get_submissions_file_path():
        return current_app.config['SUBMISSIONS_FILE']

    @staticmethod
    def load_submissions():
        path = SubmissionManager.get_submissions_file_path()
        try:
            with open(path, 'r') as f:
                data = json.load(f)
                return [Submission.from_dict(sub_data) for sub_data in data]
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    @staticmethod
    def save_submissions(submissions):
        path = SubmissionManager.get_submissions_file_path()
        with open(path, 'w') as f:
            json.dump([sub.to_dict() for sub in submissions], f, indent=4)

    @staticmethod
    def add_submission(submission: Submission):
        submissions = SubmissionManager.load_submissions()
        # Remove any previous submission by the same student for the same exam
        submissions = [s for s in submissions if not (s.student_email == submission.student_email and s.exam_id == submission.exam_id)]
        submissions.append(submission)
        SubmissionManager.save_submissions(submissions)

    @staticmethod
    def get_submissions_for_exam(exam_id: str):
        return [s for s in SubmissionManager.load_submissions() if s.exam_id == exam_id]

    @staticmethod
    def get_submission(exam_id: str, student_email: str):
        for s in SubmissionManager.load_submissions():
            if s.exam_id == exam_id and s.student_email == student_email:
                return s
        return None

    @staticmethod
    def has_student_submitted(exam_id: str, student_email: str):
        return SubmissionManager.get_submission(exam_id, student_email) is not None

    @staticmethod
    def delete_submissions_for_exam(exam_id: str):
        submissions = SubmissionManager.load_submissions()
        filtered_submissions = [s for s in submissions if s.exam_id != exam_id]
        SubmissionManager.save_submissions(filtered_submissions)