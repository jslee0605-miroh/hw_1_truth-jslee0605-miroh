"""
models.py — Data model for AttendanceChimp.

AttendanceChimp is an electronic class attendance tool.  Instructors create
courses and lectures; each lecture is assigned a random QR code.  Students
photograph the QR code and upload the image.  The system decodes the QR code,
matches it to a lecture, and records the attendance.

Entities
--------
- CourseProfile   : extends Django User → instructor-specific data
- StudentProfile  : extends Django User → student-specific data
- Course          : a course taught by one instructor
- Enrollment      : junction table linking students to courses
- Lecture         : a single class meeting (has a QR-code identifier)
- QRCodeUpload    : a student's uploaded QR-code photograph
"""

import uuid

from django.db import models
from django.contrib.auth.models import User

from django.utils import timezone
import logging
import string
import random

logger = logging.getLogger(__name__) # set up tracking, auditing, and debugging
                                                               # allows using logger.warning(), logger.error(), 
                                                               # logger.info(), etc. Better than print() for debuggin... 


# ---------------------------------------------------------------------------
# User profiles
# ---------------------------------------------------------------------------
class InstructorProfile(models.Model):
    """InstructorProfile extends the Django User model to include instrutor-specific data.
    
    InstructorProfile-specific Attributes:
    - department: the academic department the instructor belongs to. 
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, related_name='instructor_profile')
    department = models.CharField(max_length=100, null=True, blank=True)

class StudentProfile(models.Model):
    """StudentProfile extends the Django User model to include student-specific data. 
    
    StudentProfile-specific Attributes:
    - graduation_year: the year the student is expected to graduate. This is optional, and is a field specific to StudentProfile.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, related_name='student_profile')
    graduation_year = models.IntegerField(null=True, blank=True)


# ---------------------------------------------------------------------------
# Course
# ---------------------------------------------------------------------------

class Course(models.Model):
    """The Course model represents a course taught by an instructor. 
    
    Attributes:
    - name: the name of the course. This serves as the primary key as well, as two classes should not be named the same.
    - instructor: foreign key to the InstructorProfile instance that teaches the course. Note: instructors are welcome to teach more than one course. It was also assumed that only one instructure can teach a given course.
    - meeting_schedule: a string that describes when the class meets. 
    """
    name = models.CharField(max_length=100, primary_key=True)
    instructor = models.ForeignKey(InstructorProfile, on_delete=models.CASCADE)
    meeting_schedule = models.CharField(max_length = 200)


# ---------------------------------------------------------------------------
# Enrollment
# ---------------------------------------------------------------------------

class Enrollment(models.Model):
    """The Enrollment model represents the enrollment of a student in a given course. It is a junction table that links a StudentProfile instance to a Course instance. While many students can be enrolled in many courses, the combination of a (student, course) must be unique.
    
    Attributes:
    - student: foreign key to the StudentProfile instance that is enrolled in the course
    - course: foreign key to the Course instance that the student is enrolled in
    """
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['student', 'course'], name='unique_enrollment')
        ]


# ---------------------------------------------------------------------------
# Lecture
# ---------------------------------------------------------------------------

class Lecture(models.Model):
    """The Lecture model represents a single class of a Course. 
    
    Attributes:
    - course: foreign key to the Course instance that this lecture is a part of
    - date: the date and time of the lecture
    - qr_identifier: a unique identifier for the lecture using a UUID. This generates the QR code for the lecture. 
    """
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    date = models.DateTimeField()
    qr_identifier = models.UUIDField(default = uuid.uuid4, editable=False, unique=True)


# ---------------------------------------------------------------------------
# QR Code Upload
# ---------------------------------------------------------------------------

class QRCodeUpload(models.Model):
    """The QRCodeUpload model represents when a student uploads an image of a QR code to record their attendance to a given lecture. 
    
    Attributes: 
    - student: foreign key to the StudentProfile instance that uploaded the QR code image
    - lecture: foreign key to the Lecture instance that the QR code image is supposed to correspond to. This is optional.
    - qr_image: the image of the QR code that is being uploaded.
    - datetime_uploaded: the date and time that the QR code image was submitted. This ensures that the student uploaded the photo during lecture.
    """

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    lecture = models.ForeignKey(Lecture, on_delete=models.CASCADE, null=True, blank=True)
    qr_image = models.FileField(upload_to='qr_uploads/') #note: I used FileField here instead of ImageField because the latter requires Pillow. Was not sure this was installed by default
    datetime_uploaded = models.DateTimeField(default=timezone.now, editable=False)


# ---------------------------------------------------------------------------
# Helper / API functions
# ---------------------------------------------------------------------------



