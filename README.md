# REQUIREMNTS TO RUN PROGRAM

Before running the program, please make sure to install this via terminal 

pip install requests


# HOW THE PROGRAM WORKS

This program is an automatic/assisted academic scheduler designed for Information Science (InfoSci) students.

It allows users to input completed courses and optionally advisor-recommended courses, then generates a semester schedule using:

Degree requirements (from CSV)
Real-time course data (from UMD API)
Prerequisite checking
Seat availability
Credit limits

# PROGRAM FLOW
1. User Input

The system prompts the user to enter:

Name
Semester (year + term)
Completed courses
Whether they have advisor-recommended courses

If yes:

User inputs recommended courses

If no:

System automatically generates a schedule

2. Degree Requirements (CSV)

The program reads a CSV file (infosci_program.csv) which includes:

Course names
Credits
Categories (Benchmark, Core, Elective)
Prerequisites

This is used to determine:

What courses are still needed and the priority of courses

3. API Integration

The system connects to the UMD API:

https://api.umd.io/v1/courses/sections

It retrieves:

Section number
Days (MWF, Tu, etc.)
Time
Open seat availability

4. Course Selection Logic
Recommended Courses

If the user enters recommended courses:

The system finds valid sections

Filters out:
Courses already completed
Sections with no time/days
Sections with no available seats
Adds them to the schedule
Auto-Fill (Filler Courses)

If credits are below the maximum number of credit (15):

The system selects additional courses from the CSV
Courses are prioritized:
Benchmark → Core → Elective
Within each category, courses are randomized
Only valid and available courses are added

(exception to the 15 credits only if certain core classes are not taken for INST upper level electives)

5. Prerequisite Checking

The system supports:

AND logic: INST126,INST201
OR logic: INST126|INST201
Level requirements: INST200+

A course is only added if prerequisites are satisfied.

6. Seat Availability Filtering

The system ensures:

Only sections with available seats are selected
Sections with open_seats = 0 are skipped

7. Schedule Output

The final schedule displays:

Course name
Section
Days
Time
Credits
Priority

8. JSON Export

Users can choose to export the schedule.

The JSON file includes:

Student name
Total credits
Course list with:
Course ID
Section
Days
Time
Open seats

# FEATURES
API-based real-time scheduling
Automatic course generation
Advisor-assisted scheduling
Randomized elective selection
Seat availability filtering
Prerequisite validation
JSON export functionality

# LIMITATIONS
Only uses first valid section found (no optimization)
It does not account for electives outside of INST. (Lower level electives a freshman or sophmore might take)
Relies on UMD API availability
Designed specifically for InfoSci program structure
Uses the infosci_program.csv to check benchmark and core courses instead of pulling directly from API.
Does not ask user if they are interested in any course to add into the scheduler

# FUTURE IMPROVEMENTS
Optimal schedule selection (best time spacing)
UI / web interface
Multi-semester planning
Integration with Testudo or additional APIs
Multi-Degree scheduling
Selection of elective before implementing scheudles
Description of courses
Implementation of Planet Terp professor reviews and optimization

