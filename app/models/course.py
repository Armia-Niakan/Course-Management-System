from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class Course:
    id: str
    name: str
    teacher: str
    teacher_name: str
    schedule: list[dict]    # {day: str, time: str, duration: int}
    max_students: int
    current_students: int = 0
    materials: List[Dict] = field(default_factory=list)
    # {filename: str, path: str, upload_date: str, description: str, size: int}