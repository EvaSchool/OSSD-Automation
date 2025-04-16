from app import create_app, db
from app.models import Course, CourseLevel

def add_courses():
    app = create_app()
    with app.app_context():
        # Create course data
        courses = [
            Course(
                course_code='MATH101',
                course_name='Advanced Mathematics',
                description='Advanced Mathematics Basic Course',
                credit=4.0,
                course_level=CourseLevel.GRADE_10,
                is_compulsory=True
            ),
            Course(
                course_code='ENG101',
                course_name='English',
                description='English Basic Course',
                credit=3.0,
                course_level=CourseLevel.ESL_1,
                is_compulsory=True
            ),
            Course(
                course_code='PHY101',
                course_name='Physics',
                description='Physics Basic Course',
                credit=3.0,
                course_level=CourseLevel.GRADE_10,
                is_compulsory=True
            ),
            Course(
                course_code='CHEM101',
                course_name='Chemistry',
                description='Chemistry Basic Course',
                credit=3.0,
                course_level=CourseLevel.GRADE_10,
                is_compulsory=True
            ),
            Course(
                course_code='BIO101',
                course_name='Biology',
                description='Biology Basic Course',
                credit=3.0,
                course_level=CourseLevel.GRADE_10,
                is_compulsory=True
            ),
            Course(
                course_code='HIS101',
                course_name='History',
                description='History Basic Course',
                credit=2.0,
                course_level=CourseLevel.GRADE_10,
                is_compulsory=True
            ),
            Course(
                course_code='GEO101',
                course_name='Geography',
                description='Geography Basic Course',
                credit=2.0,
                course_level=CourseLevel.GRADE_10,
                is_compulsory=True
            ),
            Course(
                course_code='ART101',
                course_name='Art',
                description='Art Basic Course',
                credit=2.0,
                course_level=CourseLevel.GRADE_10,
                is_compulsory=False
            ),
            Course(
                course_code='MUS101',
                course_name='Music',
                description='Music Basic Course',
                credit=2.0,
                course_level=CourseLevel.GRADE_10,
                is_compulsory=False
            ),
            Course(
                course_code='PE101',
                course_name='Physical Education',
                description='Physical Education Basic Course',
                credit=2.0,
                course_level=CourseLevel.GRADE_10,
                is_compulsory=True
            )
        ]

        # Add to database
        for course in courses:
            db.session.add(course)
        db.session.commit()
        print('Course data added successfully!')

if __name__ == '__main__':
    add_courses() 