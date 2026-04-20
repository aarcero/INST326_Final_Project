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

    Uses the resource  https://www.geeksforgeeks.org/python/python-extract-words-from-given-string/  for regular expression syntax and 
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
        # Get values from CSV (MATCHES YOUR HEADER EXACTLY)
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
            prerequisites=prereq_string
        )

        # Priority logic
        if "Benchmark" in category_value:
            priority_value = 3
        elif "Core" in category_value:
            priority_value = 2
        else:
            priority_value = 1
        return cls(
            temp_course,
            category_value,
            row.get("Subcategory", "").strip(),
            priority_value
        )

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

    for item in api_data:
        try:
            name = item.get("course_id", "Unknown")

            raw_credits = item.get("credits", "0")
            try:
                credits = int(float(raw_credits))
            except:
                credits = 3

            course = Course(
                name=name,
                credits=credits
            )

            course_objects.append(course)

        except Exception as e:
            print("Error converting course:", item, e)

    return course_objects

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

def save_schedule(selected_courses, student_name, filename=None):
    """
    Optimized saving function:
    1. Generates a timestamped filename to prevent overwriting.
    2. Includes a metadata summary for audit/tracking.
    3. Handles file I/O errors gracefully.
    """
    # Generate filename (e.g., Yuanfeng_Schedule_20260420.json)
    if not filename:
        date_str = datetime.datetime.now().strftime("%Y%m%d")
        filename = f"{student_name.replace(' ', '_')}_Schedule_{date_str}.json"
    
    # Calculate total credits for the summary
    total_credits = sum(int(rec.course.credits) for rec in selected_courses)
    
    # Construct structured output
    output_data = {
        "metadata": {
            "student_name": student_name,
            "export_date": str(datetime.datetime.now()),
            "course_count": len(selected_courses),
            "total_credits": total_credits
        },
        "proposed_schedule": []
    }
    
    for rec in selected_courses:
        output_data["proposed_schedule"].append({
            "course_id": rec.course.name,
            "credits": rec.course.credits,
            "category": rec.category,
            "priority_level": rec.priority,
            "time_info": rec.course.time if hasattr(rec.course, 'time') else "N/A"
        })
    
    # Write to file and provide feedback
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=4)
        print("\n" + "="*40)
        print("SUCCESS: Schedule exported successfully!")
        print(f"File saved as: {filename}")
        print(f"Summary: {len(selected_courses)} courses, {total_credits} credits total.")
        print("="*40)
    except IOError as e:
        print(f"\nERROR: Failed to write to file: {e}")

if __name__ == "__main__":
    print("Academic Scheduler starting\n")

    test_course = Course("INST326", 3, time="14:00-15:15", prerequisites=["INST126"])
    print(f"[TEST] {test_course.name} starts at {test_course.start_minutes} minutes\n")

    # Loading CSV data
    file_path = "infosci_program.csv"
    courses = load_courses_from_csv(file_path)
    print(f"Loaded {len(courses)} courses from CSV.\n")

    # Creating a test student with some completed courses

    student_name = input("Enter your name: ").strip()

    has_csv = input("Do you have a 4-year plan CSV? (yes/no): ").strip().lower()

    if has_csv == "yes":
        advisor_name = input("Enter your advisor's name: ").strip()
        file_path = input("Enter the path to your CSV file: ").strip()
    else:
        advisor_name = "Default Advisor"
        file_path = "infosci_program.csv"

    # Load courses from CSV
    courses = load_courses_from_csv(file_path)
    print(f"Loaded {len(courses)} courses from CSV.\n")

    #Extra courses not in CSV but in API
    csv_course_names = {rec.course.name for rec in courses}

    # Ask academic standing
    print("\n--- Semester Selection ---")

    year = input("Enter year (e.g., 2026): ").strip()

    print("\nSelect term:")
    print("1. Spring")
    print("2. Summer")
    print("3. Fall")

    term_choice = input("Enter choice (1/2/3): ").strip()

    term_map_choice = {
        "1": "spring",
        "2": "summer",
        "3": "fall"
    }

    if term_choice not in term_map_choice:
        print("Invalid choice. Defaulting to Fall.")
        term = "fall"
    else:
        term = term_map_choice[term_choice]

    semester = build_semester_code(year, term)

    print(f"\nSelected semester: {semester}")

    # Fetching API data
    courses_data = grab_umd_courses(semester=semester)
    print(f"Fetched {len(courses_data)} courses from UMD API.\n")

    # Converting API data to Course objects
    api_courses = convert_api_to_courses(courses_data)
    print(f"Converted {len(api_courses)} API courses into Course objects.\n")


    # Ask completed courses
    completed_input = input("Enter completed courses separated by commas (e.g., INST126,MATH115): ")
    completed_courses = [c.strip().upper() for c in completed_input.split(",") if c.strip()]

    # Create student
    student = Student(
        name=student_name,
        major="InfoSci",
        completed_courses=completed_courses
    )

    # Show advisor-recommended courses the student can take
    print("Courses from advisor plan student can take (max 15 credits):\n")

    selected_courses = []
    total_credits = 0
    MAX_CREDITS = 15

    """
    Lamba functions are anonymous functions defined with the lambda keyword. In this code, we use a lambda function as the key for sorting 
    the courses based on their priority.

    3 is the highest priority (Benchmark),
    2 is the next (Core),
    1 is the lowest (General).
    
    By sorting in reverse order, we ensure that courses with higher priority are considered first when building the schedule.

    reverse = true means that the sorting will be done in descending order, so courses with higher priority (like Benchmark) will come before
    lower priority courses (like General).

    Learned how to use lambda from https://www.w3schools.com/python/python_lambda.asp.
    """

    sorted_courses = sorted(courses, key=lambda x: x.priority, reverse=True)

    for rec in sorted_courses:
        course = rec.course

        # Skip completed courses
        if course.name in student.completed_courses:
            continue

        # Check prereqs
        if not student.check_if_can_take(course):
            continue

        # Default credits safety
        credits = course.credits if course.credits else 3

        # Stop if adding exceeds limit
        if total_credits + credits > MAX_CREDITS:
            continue

        selected_courses.append(rec)
        total_credits += credits

    # Print final schedule
    for rec in selected_courses:
        print(f"{rec.course} (Credits: {rec.course.credits}, Priority: {rec.priority})")

    print(f"\nTotal Credits: {total_credits}")

    # Show API courses the student can take
    for course in api_courses:
        if not course.name.startswith("INST"):
            continue

        if course.name not in csv_course_names:
            print(f"API course not in CSV: {course.name} (Ask advisor if this is a good option for the student.)")
            continue

    # Skip completed
        if course.name in student.completed_courses:
            continue

        if student.check_if_can_take(course):
            print(f"Student can take API course: {course.name}")

    # Save schedule to file    
    if selected_courses:
        save_choice = input("\nWould you like to export this schedule to JSON? (y/n): ").lower().strip()
        if save_choice == 'y':
            # Call the function
            save_schedule(selected_courses, student_name)
