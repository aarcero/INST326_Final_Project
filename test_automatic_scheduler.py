from automatic_scheduler import (Course, Student, extract_course_code, convert_api_to_courses, AdvisorRecommendation)

# Student Tests

def test_can_student_take_course_with_all_prereqs():
    student = Student("John", "InfoSci", completed_courses=["INST126"])
    course = Course("INST326", 3, prerequisites=["INST126"])
    assert student.check_if_can_take(course)

def test_can_student_take_course_with_no_prereqs():
    student = Student("Jane", "InfoSci")
    course = Course("INST201", 3)
    assert student.check_if_can_take(course)

def test_cannot_take_course_missing_prereq():
    student = Student("John", "InfoSci", completed_courses=["INST126"])
    course = Course("INST327", 3, prerequisites=["INST201"])
    assert not student.check_if_can_take(course)

# Advisor Recommendation Tests
def test_advisor_recommendation_priority():
    row = {
        "Course": "INST 326 Object-Oriented Programming",
        "Credits": "3",
        "Category": "Core",
        "Subcategory": "INST Core"
    }

    rec = AdvisorRecommendation.from_csv_row(row)

    assert rec.course.name == "INST326"
    assert rec.priority == 2

# Course Time Tests

def test_valid_time_conversion():
    course = Course("INST326", 3, time="12:00-1:15")
    assert course.start_minutes == 720

def test_invalid_time_format():
    course = Course("INST326", 3, time="invalid")
    assert course.start_minutes == 0

# Date Tests

def test_dates_string_to_list():
    course = Course("INST326", 3, dates="MWF")
    assert course.dates == ["M", "W", "F"]

def test_not_overwriting_valid_input():
    course = Course("INST326", 3, dates=["T", "R"])
    assert course.dates == ["T", "R"]

# Regular Expression Tests

def test_extract_course_code():
    course_name = "Introduction to Information Science INST326"
    assert extract_course_code(course_name) == "INST326"

def test_extract_course_code_with_letter():
    course_name = "Introduction to Information Science INST326A"
    assert extract_course_code(course_name) == "INST326A"

def test_extract_course_code_with_space():
    course_name = "Introduction to Information Science INST 326"
    assert extract_course_code(course_name) == "INST326"   

def test_extract_course_code_no_match():
    course_name = "Introduction to Information Science"
    assert extract_course_code(course_name) == "Introduction to Information Science"

def test_extract_course_code_empty_string():
    assert extract_course_code("") == ""

# API Conversion Tests

def test_convert_api_to_courses():
    api_data = [
        {
            "course_id": "INST326",
            "credits": 3
        }
    ]

    courses = convert_api_to_courses(api_data)

    assert len(courses) == 1
    course = courses[0]

    assert course.name == "INST326"
    assert course.credits == 3
    assert course.prerequisites == []
    assert course.time is None
    assert course.start_minutes == 0
    assert course.dates == []

# CSV to Object Tests
def test_csv_to_object():
    csv_data = "name,credits,prerequisites,time,dates\nIntroduction to Information Science INST326,3,INST126,12:00-1:15,MWF"
    lines = csv_data.splitlines()
    header = lines[0].split(",")
    values = lines[1].split(",")
    course_data = dict(zip(header, values))
    course = Course(
        name=course_data["name"],
        credits=int(course_data["credits"]),
        prerequisites=course_data["prerequisites"].split(";") if course_data["prerequisites"] else [],
        time=course_data["time"],
        dates=course_data["dates"]
    )
    assert course.name == "Introduction to Information Science INST326"
    assert course.credits == 3
    assert course.prerequisites == ["INST126"]
    assert course.time == "12:00-1:15"
    assert course.dates == ["M", "W", "F"]
