from dataclasses import dataclass


@dataclass
class Course:
    id: str
    name: str
    teacher: str
    teacher_name: str
    schedule: list[dict]    # {day: str, time: str, duration: int}
    max_students: int
    current_students: int = 0
