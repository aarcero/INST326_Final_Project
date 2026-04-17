from automatic_scheduler import Course, Student


def test_can_student_take_course_with_all_prereqs():
    student = Student("John", "InfoSci", completed_courses=["INST126"])
    course = Course("INST326", 3, prerequisites=["INST126"])
    assert student.check_if_can_take(course)

def test_can_student_take_course_with_no_prereqs():
    student = Student("Jane", "InfoSci")
    course = Course("INST201", 3)
    assert student.check_if_can_take(course)

def test_valid_time_conversion():
    course = Course("INST326", 3, time="12:00-1:15")
    assert course.start_minutes == 720

def test_invalid_time_format():
    course = Course("INST326", 3, time="invalid")
    assert course.start_minutes == 0

def test_dates_string_to_list():
    course = Course("INST326", 3, dates="MWF")
    assert course.dates == ["M", "W", "F"]

def test_not_overwriting_valid_input():
    course = Course("INST326", 3, dates=["T", "R"])
    assert course.dates == ["T", "R"]

