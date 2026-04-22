import sys
import csv
import re
import json
import datetime
import requests

def extract_course_code(course_name):
    """
    Extracts a standardized course code from a course name string.

    Supports formats such as:
    - INST326
    - INST 326
    - INST326A

    explained regex patterns:
    - [A-Z]+: Matches one or more uppercase letters (the department code).
    - \s?: Optionally matches a single space (to allow for formats like "INST 326").
    - \d+: Matches one or more digits (the course number).
    - [A-Z]?: Optionally matches a single uppercase letter (for course variations like "INST326A").

    Returns:
        str: Cleaned course code without spaces.

    Uses the resource https://www.geeksforgeeks.org/python/python-extract-words-from-given-string/ for regular expression syntax and 
    usage as well as https://www.w3schools.com/python/python_regex.asp for additional regex examples and explanations.
    """
    match = re.search(r'([A-Z]+\s?\d+[A-Z]?)', course_name)
    if match:
        return match.group(1).replace(" ", "")
    return course_name

def grab_umd_courses(department="INST", semester="202408"): 
    """
    Fetches course data from the UMD API for a given department and semester.

    Returns:
        list: JSON response containing course data if successful, otherwise empty list.
    
    Uses the resource https://api.umd.io/v1/courses?department=DEPT&semester=SEMESTER, where DEPT is the department code
    (e.g., "INST") and SEMESTER is the semester code (e.g., "202408" for Fall 2024). Also uses 
    https://www.cbtnuggets.com/blog/technology/programming for understanding how to make API requests in Python using the requests library.
        department (str): The department code to filter courses (default is "INST").
        semester (str): The semester code to filter courses (default is "202408" for Fall 2024).
    """
    url = f"https://api.umd.io/v1/courses?department={department}&semester={semester}"
    
    response = requests.get(url)

    if response.status_code == 200:
        return response.json()
    else:
        print("Error fetching courses:", response.status_code)
        return []

def build_semester_code(year, term):
    """
    Converts a year + term into a UMD API semester code.
    """
    term_map = {
        "spring": "01",
        "summer": "05",
        "fall": "08"
    }

    term = term.strip().lower()

    if term not in term_map:
        raise ValueError("Invalid term. Choose Spring, Summer, or Fall.")

    return f"{year}{term_map[term]}"

class Person:
    """Parent class for all individuals in the system."""
    def __init__(self, name, directory_id=None):
        self.name = name
        self.directory_id = directory_id

class Student(Person):
    """
    Determines whether a student is eligible to take a course based on prerequisites.

    Prerequisite formats supported:
    - AND logic: "INST126,INST201"
    - OR logic: "INST126|INST201"
    - Course level requirement: "INST200+"

    Returns:
        bool: True if all prerequisite groups are satisfied, False otherwise.
    """
    def __init__(self, name, major, directory_id=None, completed_courses=None):
        super().__init__(name, directory_id)
        self.major = major
        if completed_courses:
            self.completed_courses = completed_courses
        else:
            self.completed_courses = []

    def check_if_can_take(self, course_object):
        prerequisites = course_object.prerequisites

        #not all courses have prerequisites, so we check if the list is empty first
        if not prerequisites:
            return True
        
        if isinstance(prerequisites, list):
            and_group = prerequisites
        else:
            and_group = prerequisites.split(",")

        for group in and_group:
            group = group.strip()

            options = group.split("|")

            satisfied = False

            for option in options:
                option = option.strip()
                
                if option.endswith("+"):
                    base_course = option[:-1]

                    for completed in self.completed_courses:
                        if completed.startswith(base_course[:4]):
                            try:
                                if int(completed[4:]) >= int(base_course[4:]):
                                    satisfied = True
                                    break
                            except:
                                continue

                else:
                    for completed in self.completed_courses:
                        if completed.startswith(option):
                            satisfied = True
                            break
                
                if satisfied:
                    break

            if not satisfied:
                return False 
        return True

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
        Converts a course start time into minutes since midnight.

        Expected format:
            "HH:MM-HH:MM"

        Returns:
            int: Start time in minutes, or 0 if invalid format.
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
            
    def is_conflicting(self, other_course):
        """check if this course conflicts with another course based on time and days."""
        # check if they have any common days
        common_days = set(self.dates) & set(other_course.dates)
        if not common_days:
            return False
        
        return self.start_minutes == other_course.start_minutes
        
    def __str__(self):
        """Returns a readable string of the course."""
        return f"Course: {self.name}, Section: {self.section}, Time: {self.time}" 

class ProgramCourse:
    def __init__(self, course, category, priority):
        self.course = course
        self.category = category
        self.priority = priority

    @classmethod
    def from_csv_row(cls, row):
        # Get values from CSV
        raw_credits = row.get("Credits", "0").strip()
        credits_value = int(raw_credits) if raw_credits.isdigit() else 0

        raw_name = row.get("Course", "").strip()
        course_code = extract_course_code(raw_name)

        prereq_string = row.get("Prerequisites", "").strip()
        category_value = row.get("Category", "General").strip()

        # Create Course object
        temp_course = Course(
            name=course_code,
            credits=credits_value,
            prerequisites=prereq_string,
            category=category_value
        )
        # Priority logic
        if "Benchmark" in category_value:
            priority_value = 3
        elif "Core" in category_value:
            priority_value = 2
        else:
            priority_value = 1

        return cls(temp_course, category_value, priority_value)

def convert_api_to_courses(api_data):
    """
    Converts raw UMD API course data into Course objects.

    Handles:
    - Missing or malformed credit values
    - Default credit fallback (3 credits)
    - Extraction of course ID from API response

    Returns:
        list[Course]: List of Course objects created from API data.
    """
    course_objects = []