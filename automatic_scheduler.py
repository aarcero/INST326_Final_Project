import sys
import csv
import re

def extract_course_code(course_name):
    match = re.search(r'([A-Z]+\s?\d+[A-Z]?)', course_name)
    """
    Uses re.search to find the first occurrence of a course code pattern
    within the input string.

    The regular expression '([A-Z]+\s?\d+[A-Z]?)' matches:
    - [A-Z]+: One or more uppercase letters (the department code).
    - \s?: An optional space (some course codes have a space, e.g., "INST 126").
    - \d+: One or more digits (the course number).
    - [A-Z]?: An optional uppercase letter (for courses like "MATH115A").
    The parentheses create a capture group, allowing the matched course code
    to be extracted using match.group(1).
    """
    if match:
        return match.group(1).replace(" ", "")
    return course_name

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
        if time is None or "-" not in time:
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


class AdvisorRecommendation:
    """Wraps a Course object with advisor-specific details using composition."""
    def __init__(self, course_obj, category=None, subcategory=None, priority=1):
        self.course = course_obj
        self.category = category
        self.subcategory = subcategory
        self.priority = priority

    @classmethod
    def from_csv_row(cls, row):
        """Factory method to create a recommendation from a CSV dictionary row."""
        try:
            # Strip whitespace and handle potential missing keys
            raw_credits = row.get('Credits', '0').strip()
            credits_val = int(raw_credits) if raw_credits.isdigit() else 0
        except ValueError:
            credits_val = 0

        # Create the Course object using CSV column names
        raw_name = row.get('Course', '').strip()

        if not raw_name:
            print("DEBUG: Missing course name in row:", row)
            raw_name = "Unknown Course"

        course_code = extract_course_code(raw_name)

        temp_course = Course(
            name=course_code,
            credits=credits_val
        )
        
        category_val = row.get('Category', 'General').strip()
        
        # Priority logic
        if "Benchmark" in category_val:
            priority_val = 3
        else:
            if "Core" in category_val:
                priority_val = 2
            else:
                priority_val = 1
            
        return cls(temp_course, category_val, row.get('Subcategory'), priority_val)
    
def load_courses_from_csv(file_path):
    """Loads course data and returns AdvisorRecommendation objects."""
    recommendations = []
    try:
        with open(file_path, mode='r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)

            for row in reader:
                rec = AdvisorRecommendation.from_csv_row(row)
                recommendations.append(rec)

    except FileNotFoundError:
        print(f"Error: {file_path} not found.")
    except Exception as e:
        print(f"An error occurred: {e}")
    return recommendations

if __name__ == "__main__":
    print("Academic Scheduler starting\n")

    test_course = Course("INST326", 3, time="14:00-15:15", prerequisites=["INST126"])
    print(f"[TEST] {test_course.name} starts at {test_course.start_minutes} minutes\n")

    file_path = "infosci_program.csv"

    courses = load_courses_from_csv(file_path)
    print(f"Loaded {len(courses)} courses.\n")

    student = Student(
        name="Test Student",
        major="InfoSci",
        completed_courses=["INST126", "MATH115"]
    )

    print("Courses student can take:\n")
    for rec in courses:
        if student.check_if_can_take(rec.course):
            print(f"{rec.course} (Priority: {rec.priority})")
