import enum

class UserGender(enum.Enum):
    male = 'male'
    female = 'female'
    other = 'other'

class UserRole(enum.Enum):
    student = 'student'
    teacher = 'teacher'
    parent = 'parent'