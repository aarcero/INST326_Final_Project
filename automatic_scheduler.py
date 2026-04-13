#Alden: I started on some core functionality for an automatic scheduler. This is a very basic implementation and can be expanded upon in 
# the future.



class Course:
    def __init__(self, name, credits, prerequisites=None, semester_term=None, section=None, time=None, dates=None):
        """
        Initializes a Course instance. (P.S I kind of suck at writing docstrings, so if you are pretty good at it
        feel free to rewrite. We might also need to initilize more classes. So far this is what I have in mind.)
        """
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

class Major:
    def __init__(self, name, required_courses=None, elective_courses=None):
        """
        Initializes a Major instance.
        """
        if required_courses is None:
            required_courses = []
        if elective_courses is None:
            elective_courses = []
        self.name = name
        self.required_courses = required_courses
        self.elective_courses = elective_courses

class Student:
    def __init__(self, name, major, completed_courses=None):
        """
        Initializes a Student instance.
        """
        if completed_courses is None:
            completed_courses = []
        self.name = name
        self.major = major
        self.completed_courses = completed_courses