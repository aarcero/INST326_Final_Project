# Du:
# - Implemented Person inheritance for Student/Advisor.
# - Add new class AdvisorRecommendation to wrap Course objects.
# - Added conflicts_with for future scheduling logic.
# - A new class method from_csv_row is added to AdvisorRecommendation to create instances from CSV data.
import sys
import csv


class Person:
    """Parent class for all individuals in the system."""
    def __init__(self, name, directory_id=None):
        self.name = name
        self.directory_id = directory_id

class Student(Person):
    """A Student is a Person who has a major and a list of completed courses."""
    def __init__(self, name, major, directory_id=None, completed_courses=None):
        super().__init__(name, directory_id)
        self.major = major
        if completed_courses:
            self.completed_courses = completed_courses
        else:
            self.completed_courses = []

    def check_if_can_take(self, course_object):
        """
        Checks if the student meets all prerequisites for a course.
        
        Returns:
            bool: True if all prerequisites are met, False otherwise.
        """
        for pre in course_object.prerequisites:
            if pre not in self.completed_courses:
                return False
        return True

class Advisor(Person):
    """An Advisor is a Person who provides course recommendations."""
    def __init__(self, name, directory_id=None, department="iSchool"):
        super().__init__(name, directory_id)
        self.department = department


class Course:
    def __init__(self, name, credits, prerequisites=None, semester_term=None, 
                 section=None, time=None, dates=None, category=None):
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

        self.name = name
        self.credits = credits

        if prerequisites:
            self.prerequisites = prerequisites
        else:
            self.prerequisites = []

        self.semester_term = semester_term
        self.section = section
        self.time = time

        # If days is a string like "MWF", it converts to ['M', 'W', 'F'].
        # This makes it easier to check if a course meets on a specific day.
        if isinstance(dates, str):
            self.dates = list(dates)
        else:
            if dates:
                self.dates = dates
            else:
                self.dates = []

        self.category = category

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
        if time is None:
            return 0
            
        if "-" not in time:
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
        
    def conflicts_with(self, other):
        """Checks if this course conflicts with another based on days and time."""
        
        common_days = set(self.dates) & set(other.dates)
        if common_days and self.start_minutes == other.start_minutes:
            return True
        return False
    
    def __str__(self):
        """Returns a readable string of the course."""
        return f"Course: {self.name}, Section: {self.section}, Time: {self.time}"
    

class AdvisorRecommendation:
    """
    Wraps a Course object with advisor-specific priority.
    This allows advisors to provide recommendations for students.
    """
    def __init__(self, course_obj, priority=1, notes=""):
        self.course = course_obj
        self.priority = priority
        self.notes = notes

    @classmethod
    def from_csv_row(cls, row):
        """
        A factory method to create an instance from a CSV dictionary.
        This is a class method because it acts on the class itself
        to return a new object.
        """
        # We extract and convert data types here so the rest of the 
        # program doesn't have to deal with raw CSV strings.
        temp_course = Course(
            name=row['course_name'],
            credits=int(row['credits']),
            category=row['category'],
            dates=row.get('days', ""),
            time=row.get('time', "")
        )
        return cls(temp_course, priority=int(row.get('priority', 1)), 
                   notes=row.get('notes', ""))
    
       
class Major:
    def __init__(self, name, required_courses=None, elective_courses=None):
        """
        Initializes a Major instance.

        Args:
            name (str): The name of the major.
            required_courses (list): Courses required for graduation.
            elective_courses (list): Available elective courses.
        """
        self.name = name

        if required_courses:
            self.required_courses = required_courses
        else:
            self.required_courses = []
            
        if elective_courses:
            self.elective_courses = elective_courses
        else:
            self.elective_courses = []


if __name__ == "__main__":
    print("Academic Scheduler Data Model loaded successfully.")
    
    # Simple test case
    test_course = Course("INST326", 3, time="14:00-15:15", 
                         prerequisites=["INST126"])
    print(f"Test Course: {test_course.name}, Start Minutes: {test_course.start_minutes}")