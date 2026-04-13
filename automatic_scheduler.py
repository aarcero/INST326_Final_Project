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