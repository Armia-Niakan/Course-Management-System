from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class Question:
    id: int
    text: str
    options: List[str]
    correct_option: int 

    def to_dict(self):
        return {
            'id': self.id,
            'text': self.text,
            'options': self.options,
            'correct_option': self.correct_option
        }

@dataclass
class Exam:
    id: str
    course_id: str
    title: str
    questions: List[Question] = field(default_factory=list)
    duration_minutes: int = 30 # minutes

    def to_dict(self):
        return {
            'id': self.id,
            'course_id': self.course_id,
            'title': self.title,
            'questions': [q.to_dict() for q in self.questions],
            'duration_minutes': self.duration_minutes
        }

    @classmethod
    def from_dict(cls, data: Dict):
        questions = [Question(
            id=q['id'],
            text=q['text'],
            options=q['options'],
            correct_option=q['correct_option']
        ) for q in data.get('questions', [])]
        
        return cls(
            id=data['id'],
            course_id=data['course_id'],
            title=data['title'],
            questions=questions,
            duration_minutes=data.get('duration_minutes', 60)
        )
