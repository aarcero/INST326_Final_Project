#Alden: I started on some core functionality for an automatic scheduler. This is a very basic implementation and can be expanded upon in 
# the future.

class Course:
    def __init__(self, name, credits, prerequisites=None, semester_term=None, section=None, time=None, dates=None):
        if prerequisites is None:
            prerequisites = []
        if dates is None:
            dates = []
        self.name = name
        self.credits = credits
        self.prerequisites = prerequisites
        self.semester_term = semester_term
        self.section = section
        self.time = time
        self.dates = dates

Class Major:
    def __init__(self, name, required_courses=None, elective_courses=None):
        if required_courses is None:
            required_courses = []
        if elective_courses is None:
            elective_courses = []
        self.name = name
        self.required_courses = required_courses
        self.elective_courses = elective_courses