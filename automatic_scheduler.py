# Alden: I started on some core functionality for an automatic scheduler. This is a very basic implementation and can be expanded upon in 
# the future.
# Du: I added some methods and docstrings to exist classes.
# and I also added a simple test case to check if the time conversion is working correctly.
import sys

class Course:
    def __init__(self, name, credits, prerequisites=None, semester_term=None, 
                 section=None, time=None, dates=None):
        """
        Initializes a Course instance.

        Args:
            name (str): The name of the course .
            credits (int): The number of credits for the course.
            prerequisites (list): A list of course required before taking this course.
            semester_term (str): The term when the course is offered.
            section (str): The specific section number.
            time (str): The time slot (e.g., '10:00-10:50').
            dates (str): The days of the week (e.g., 'MWF').
        """

        if prerequisites is None:
            prerequisites = []

       # If days is a string like "MWF", it converts to ['M', 'W', 'F'].
        # This makes it easier to check if a course meets on a specific day.
        if isinstance(dates, str):
            self.dates = list(dates)
        elif dates == None:
            self.dates = []
        else:
            self.dates = dates

        self.name = name
        self.credits = credits
        self.prerequisites = prerequisites
        self.semester_term = semester_term
        self.section = section
        self.time = time

        # Convert time string to numeric minutes for conflict detection.
        self.start_minutes = self.convert_time_to_minutes(time)

    def convert_time_to_minutes(self, time):
        """
        Converts the start time from the time string into minutes.
        
        Args:
            time (str): The time range string (e.g., '10:30-12:00').
            
        Returns:
            int: Minutes since midnight.
        """
        if time == None or "-" not in time:
            return 0
        
        # We use a try-except to ensure 
        # it won't crash if the input data is incorrectly formatted.
        try:
            # .split("-") cuts the string "10:30-12:00" into a list: ["10:30", "12:00"].
            # We use [0] to grab only the first element (the start time).
            start = time.split("-")[0]
            
            # start.split(":") breaks "10:30" into ["10", "30"].
            # map(int, ...) takes each string in that list and converts it into an integer.
            # This allows us to assign 'hours' and 'minutes'.
            hours, minutes = map(int, start.split(":"))
            
            # Calculate total minutes
            return (hours * 60) + minutes
            
        except (ValueError, IndexError):
            # If time string is not formatted correctly, catch the error and return 0.
            print(f"Warning: Could not parse time for {self.name}")
            return 0
        
    def __str__(self):
        """Returns a readable string of the course."""
        return f"Course: {self.name}, Section: {self.section}, Time: {self.time}"
       
class Major:
    def __init__(self, name, required_courses=None, elective_courses=None):
        """
        Initializes a Major instance.

        Args:
            name (str): The name of the major.
            required_courses (list): Courses required for graduation.
            elective_courses (list): Available elective courses.
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

        Args:
            name (str): The student's name.
            major (str): The student's major.
            completed_courses (list): Courses student finished.
        """
        if completed_courses is None:
            completed_courses = []
        self.name = name
        self.major = major
        self.completed_courses = completed_courses

    def check_if_can_take(self, course_object):
        """
        Checks if the student meets all prerequisites for a course.
        
        Args:
            course_object (Course): The course the student wants to take.
            
        Returns:
            bool: True if all prerequisites are met, False otherwise.
        """
        for pre in course_object.prerequisites:
            if pre not in self.completed_courses:
                return False
        return True
    

if __name__ == "__main__":
    print("Academic Scheduler Data Model loaded successfully.")
    
    # Simple test case
    test_course = Course("INST326", 3, time="14:00-15:15", prerequisites=["INST126"])
    print(f"Test Course: {test_course.name}, Start Minutes: {test_course.start_minutes}")