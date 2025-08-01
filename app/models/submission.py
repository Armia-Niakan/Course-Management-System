from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass
class Submission:
    exam_id: str
    student_email: str
    answers: Dict[str, Any]  # {question_id:option_index}
    score: float
    total_questions: int
    submitted_at: str

    def to_dict(self):
        return {
            'exam_id': self.exam_id,
            'student_email': self.student_email,
            'answers': self.answers,
            'score': self.score,
            'total_questions': self.total_questions,
            'submitted_at': self.submitted_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict):
        return cls(
            exam_id=data['exam_id'],
            student_email=data['student_email'],
            answers=data['answers'],
            score=data['score'],
            total_questions=data['total_questions'],
            submitted_at=data['submitted_at']
        )