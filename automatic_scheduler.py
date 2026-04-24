import csv
import re
import json
import datetime
import requests
import random

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

def grab_umd_courses(course_id, semester):
    """
    Fetches course data from the UMD API for a given department and semester.
    Returns section-level data including section_id, meetings, days, and times.

    Returns:
        list: JSON response containing course data if successful, otherwise empty list.
    
    Uses the resource https://api.umd.io/v1/courses?department=DEPT&semester=SEMESTER, where DEPT is the department code
    (e.g., "INST") and SEMESTER is the semester code (e.g., "202408" for Fall 2024). Also uses 
    https://www.cbtnuggets.com/blog/technology/programming for understanding how to make API requests in Python using the requests library.
        course_id (str): The course ID to fetch sections for.
        semester (str): The semester code to filter courses (default is "202408" for Fall 2024).
    """
    url = f"https://api.umd.io/v1/courses/sections?course_id={course_id}&semester={semester}"

    response = requests.get(url)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching sections for {course_id}: {response.status_code}")
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
    def __init__(self, name, credits, prerequisites=None, semester_term=None, section=None, time=None, dates=None, category=None, open_seats=None):
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
        self.open_seats = open_seats

        # Convert time string to numeric minutes for conflict detection.
        self.start_minutes = self.convert_time_to_minutes(time)

    def convert_time_to_minutes(self, time):
        """
        Converts a course start time into minutes since midnight.

        Supports formats like:
        - 14:00-15:15
        - 4:00pm-4:50pm
        - 9:30am-10:45am

        """
        if time is None or "-" not in time:
            return 0
        
        # We use a try-except to ensure 
        # it won't crash if the input data is incorrectly formatted.
        try:
            # .split("-") cuts the string "10:30-12:00" into a list: ["10:30", "12:00"].
            # We use [0] to grab only the first element (the start time).
            start = time.split("-")[0].strip().lower()

            # Handle am/pm format
            if "am" in start or "pm" in start:
                dt = datetime.datetime.strptime(start, "%I:%M%p")
                return dt.hour * 60 + dt.minute
            
            # Handle 24-hour format
            hours, minutes = map(int, start.split(":"))
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
        return f"Course: {self.name}, Section: {self.section}, Days: {''.join(self.dates)}, Time: {self.time}"

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


def convert_api_sections_to_courses(section_data):
    """
    Converts UMD API section data into Course objects with time and date information.
    Converts raw UMD API course data into Course objects.

    Handles:
    - Missing or malformed credit values
    - Default credit fallback (3 credits)
    - Extraction of course ID from API response

    Returns:
        list[Course]: List of Course objects created from API data.

    """

    section_courses = []

    for item in section_data:
        try:
            course_name = item.get("course", "Unknown")
            section_id = item.get("section_id", "")
            meetings = item.get("meetings", [])

            open_seats = int(item.get("open_seats", 0))

            # Default values in case meeting info is missing
            days = []
            time = None

            if meetings:
                first_meeting = meetings[0]
                raw_days = first_meeting.get("days", "")
                start_time = first_meeting.get("start_time", "")
                end_time = first_meeting.get("end_time", "")

                if raw_days:
                    days = list(raw_days)

                if start_time and end_time:
                    time = f"{start_time}-{end_time}"

                course = Course(
                    name=course_name,
                    credits=3,
                    section=section_id,
                    time=time,
                    dates=days,
                    open_seats=open_seats
                )

                section_courses.append(course)

        except Exception as e:
            print("Error converting section:", item, e)

    return section_courses

def load_courses_from_csv(file_path):
    """Loads course data and returns ProgramCourse objects."""
    courses = []
    try:
        with open(file_path, mode='r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                rec = ProgramCourse.from_csv_row(row)
                courses.append(rec)
    except FileNotFoundError:
        print(f"Error: {file_path} not found.")
    except Exception as e:
        print(f"An error occurred: {e}")
    return courses

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
            "section": rec.course.section,
            "days": ''.join(rec.course.dates),
            "time_info": rec.course.time if hasattr(rec.course, 'time') else "N/A",
            "open_seats": rec.course.open_seats
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

def get_sections_for_recommended_courses(recommended_courses, semester):
    """
    Fetch section data for all recommended courses and return
    Course objects with date/time/section info.
    """
    all_sections = []

    for course_id in recommended_courses:
        raw_sections = grab_umd_courses(course_id, semester)
        converted_sections = convert_api_sections_to_courses(raw_sections)
        all_sections.extend(converted_sections)

    return all_sections

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

    # Ask completed courses
    completed_input = input("Enter completed courses separated by commas (e.g., INST126,MATH115): ")
    completed_courses = [extract_course_code(c.strip().upper()) for c in completed_input.split(",") if c.strip()]

    has_recommended = input("Do you have classes recommended by your advisor for this semester? (yes/no): ").strip().lower()

    recommended_courses = []

    if has_recommended == "yes":
        recommended_input = input("Enter the classes recommended for this semester separated by commas: ")

        recommended_courses = [
            extract_course_code(c.strip().upper())
            for c in recommended_input.split(",")
            if c.strip()
        ]

    engl_options = {"ENGL391", "ENGL393"}

    has_engl_requirement = any(course in completed_courses for course in engl_options)
    plans_engl_requirement = any(course in recommended_courses for course in engl_options)

    answer = "no"
    if not has_engl_requirement and not plans_engl_requirement:
        answer = input("You have not listed ENGL391 or ENGL393. Will you be taking one of them this semester? (yes/no): ").strip().lower()

    if answer == "yes":
        engl_choice = input("Which one will you take? Enter ENGL391 or ENGL393: ").strip().upper()

        if engl_choice in {"ENGL391", "ENGL393"}:
            recommended_courses.append(engl_choice)

    print("\nThinking about your class options...")

    recommended_api_sections = get_sections_for_recommended_courses(recommended_courses, semester)

    # Create student
    student = Student(
        name=student_name,
        major="InfoSci",
        completed_courses=completed_courses
    )

    selected_courses = []
    total_credits = 0
    MAX_CREDITS = 15

    for section in recommended_api_sections:
        course_name = section.name

        if not section.time or not section.dates:
            continue

        if section.open_seats is not None and section.open_seats <= 0:
            continue

        if course_name in student.completed_courses:
            continue

        if any(existing.course.name == course_name for existing in selected_courses):
            continue

        rec = next((r for r in courses if r.course.name == course_name), None)

        if rec:
            base_course = rec.course
            category = rec.category
            priority = rec.priority
        else:
            # For courses not in CSV (like ENGL)
            base_course = Course(name=course_name, credits=3)
            category = "External"
            priority = 1

        if not student.check_if_can_take(base_course):
            print(f"You cannot take {course_name} due to prerequisites.")
            continue

        credits = base_course.credits if base_course.credits else 3

        if total_credits + credits > MAX_CREDITS:
            continue

        scheduled_course = Course(
            name=base_course.name,
            credits=base_course.credits,
            prerequisites=base_course.prerequisites,
            category=base_course.category,
            section=section.section,
            time=section.time,
            dates=section.dates,
            open_seats=section.open_seats
        )

        scheduled_rec = ProgramCourse(
            course=scheduled_course,
            category=category,
            priority=priority
        )

        selected_courses.append(scheduled_rec)
        total_credits += credits

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

    same_priority_groups = {}
    for rec in sorted_courses:
        same_priority_groups.setdefault(rec.priority, []).append(rec)

    sorted_courses = []
    for priority in sorted(same_priority_groups.keys(), reverse=True):
        group = same_priority_groups[priority]
        random.shuffle(group)
        sorted_courses.extend(group)

    for rec in sorted_courses:
        if total_credits >= MAX_CREDITS:
            break

        course = rec.course

        if course.name in student.completed_courses:
            continue

        if course.name in recommended_courses:
            continue  # already handled

        if any(existing.course.name == course.name for existing in selected_courses):
            continue

        if not student.check_if_can_take(course):
            continue

        credits = course.credits if course.credits else 3

        if total_credits + credits > MAX_CREDITS:
            continue

        section_options = get_sections_for_recommended_courses([course.name], semester)

        chosen_section = None

        for section in section_options:
            if not section.section or not section.time or not section.dates:
                continue

            if section.open_seats is not None and section.open_seats <= 0:
                continue

            chosen_section = section
            break

        if not chosen_section:
            continue

        scheduled_course = Course(
            name=course.name,
            credits=course.credits,
            prerequisites=course.prerequisites,
            category=course.category,
            section=chosen_section.section,
            time=chosen_section.time,
            dates=chosen_section.dates,
            open_seats=chosen_section.open_seats
        )

        scheduled_rec = ProgramCourse(
            course=scheduled_course,
            category=rec.category,
            priority=rec.priority
        )

        print(f"{course.name} added as a filler course. Consider confirming with your advisor.")
        selected_courses.append(scheduled_rec)
        total_credits += credits

    # Print final schedule
    for rec in selected_courses:
        print(f"{rec.course} (Credits: {rec.course.credits}, Priority: {rec.priority})")

    print(f"\nTotal Credits: {total_credits}")

    # Save schedule to file
    if selected_courses:
        save_choice = input("\nWould you like to export this schedule to JSON? (y/n): ").lower().strip()
        if save_choice == 'y':
            save_schedule(selected_courses, student_name)