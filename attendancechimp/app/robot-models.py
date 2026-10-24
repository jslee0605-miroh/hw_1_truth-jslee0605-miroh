"""
MODEL: CLAUDE OPUS 5.5

My prompt was: "Generate a models.py for Django based on these specifications: <inserted screenshot of HW3 steps 1 and 2.>"

Data model for AttendanceChimp.

AttendanceChimp tracks class attendance with QR codes. An instructor
creates a course and its lectures; each lecture has a unique QR
identifier. Students prove attendance by uploading a photo of that QR
code during class.

Entities and relationships
--------------------------
    User (django.contrib.auth) 1 ── 1 InstructorProfile
    User (django.contrib.auth) 1 ── 1 StudentProfile

    InstructorProfile 1 ── * Course
    StudentProfile    * ── * Course       (through Enrollment)
    Course            1 ── * Lecture
    StudentProfile    1 ── * QRCodeUpload
    Lecture           1 ── * QRCodeUpload (optional link: lecture may be NULL)

Why InstructorProfile / StudentProfile instead of one Users table?
------------------------------------------------------------------
Instructors and students have different data (department and office vs.
student ID and major) and different permissions. Keeping Django's built-in
``User`` for authentication only, and attaching a role-specific profile with
a OneToOneField, means:

* no columns that are NULL for half the rows,
* foreign keys can point at exactly the right role (a Course's instructor
  can never accidentally be a student),
* Django's auth system (passwords, sessions, admin) is reused unchanged,
* a person who is both (e.g. a TA) can simply have both profiles.

Note: ``QRCodeUpload.image`` uses ImageField, which requires Pillow
(``pip install Pillow``).
"""

import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


# ---------------------------------------------------------------------------
# User profiles
# ---------------------------------------------------------------------------

class InstructorProfile(models.Model):
    """
    Instructor-specific data attached to a Django ``User``.

    Attributes:
        user:       One-to-one link to the authentication user.
        department: Academic department, e.g. "Computer Science".
        office:     Office location, optional.
        created_at: When the profile was created.

    Relationships:
        courses (reverse of Course.instructor): courses this person teaches.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="instructor_profile",
    )
    department = models.CharField(max_length=100, blank=True)
    office = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["user__last_name", "user__first_name"]

    def __str__(self):
        return self.user.get_full_name() or self.user.username

    def active_courses(self):
        """Return this instructor's courses as a queryset."""
        return self.courses.all()


class StudentProfile(models.Model):
    """
    Student-specific data attached to a Django ``User``.

    Attributes:
        user:            One-to-one link to the authentication user.
        student_id:      Institution-issued ID; unique.
        major:           Field of study, optional.
        graduation_year: Expected graduation year, optional.
        created_at:      When the profile was created.

    Relationships:
        enrollments (reverse of Enrollment.student)
        courses     (reverse of Course.students, via Enrollment)
        uploads     (reverse of QRCodeUpload.student)
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="student_profile",
    )
    student_id = models.CharField(max_length=20, unique=True)
    major = models.CharField(max_length=100, blank=True)
    graduation_year = models.PositiveSmallIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["user__last_name", "user__first_name"]

    def __str__(self):
        name = self.user.get_full_name() or self.user.username
        return f"{name} ({self.student_id})"

    def is_enrolled_in(self, course):
        """Return True if the student is enrolled in ``course``."""
        return self.enrollments.filter(course=course).exists()

    def attended_lectures(self, course=None):
        """
        Return the lectures this student has a valid upload for,
        optionally restricted to one course.
        """
        qs = Lecture.objects.filter(uploads__student=self).distinct()
        if course is not None:
            qs = qs.filter(course=course)
        return qs

    def attendance_rate(self, course):
        """
        Fraction (0.0–1.0) of ``course``'s past and present lectures
        that this student attended. Returns 0.0 if no lectures have
        happened yet.
        """
        held = course.lectures.filter(date__lte=timezone.localdate()).count()
        if held == 0:
            return 0.0
        attended = self.attended_lectures(course).filter(
            date__lte=timezone.localdate()
        ).count()
        return attended / held


# ---------------------------------------------------------------------------
# Courses and enrollment
# ---------------------------------------------------------------------------

class Course(models.Model):
    """
    A course taught by one instructor on a weekly schedule.

    Attributes:
        name:         Course title, e.g. "Intro to Web Development".
        code:         Catalog code, e.g. "CS 341"; unique per term.
        term:         Semester label, e.g. "Fall 2026".
        instructor:   The InstructorProfile teaching the course.
        meeting_days: Weekday letters the class meets, using
                      M=Mon, T=Tue, W=Wed, R=Thu, F=Fri, S=Sat, U=Sun
                      (e.g. "MWF" or "TR").
        start_time:   Class start time.
        end_time:     Class end time.
        location:     Room or building, optional.
        students:     Many-to-many to StudentProfile through Enrollment.

    Relationships:
        lectures    (reverse of Lecture.course)
        enrollments (reverse of Enrollment.course)
    """

    DAY_CODES = {"M": 0, "T": 1, "W": 2, "R": 3, "F": 4, "S": 5, "U": 6}
    DAY_NAMES = {
        "M": "Mon", "T": "Tue", "W": "Wed", "R": "Thu",
        "F": "Fri", "S": "Sat", "U": "Sun",
    }

    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20)
    term = models.CharField(max_length=20)
    instructor = models.ForeignKey(
        InstructorProfile,
        on_delete=models.PROTECT,  # don't silently delete courses
        related_name="courses",
    )
    meeting_days = models.CharField(
        max_length=7,
        help_text="Weekday letters: M T W R F S U, e.g. 'MWF' or 'TR'.",
    )
    start_time = models.TimeField()
    end_time = models.TimeField()
    location = models.CharField(max_length=100, blank=True)
    students = models.ManyToManyField(
        StudentProfile,
        through="Enrollment",
        related_name="courses",
        blank=True,
    )

    class Meta:
        ordering = ["term", "code"]
        constraints = [
            models.UniqueConstraint(
                fields=["code", "term"], name="unique_course_code_per_term"
            ),
            models.CheckConstraint(
                condition=models.Q(end_time__gt=models.F("start_time")),
                name="course_end_after_start",
            ),
        ]

    def __str__(self):
        return f"{self.code}: {self.name} ({self.term})"

    def meeting_weekdays(self):
        """Return meeting days as Python weekday ints (Mon=0 … Sun=6)."""
        return [self.DAY_CODES[c] for c in self.meeting_days.upper()
                if c in self.DAY_CODES]

    def meets_on(self, day):
        """Return True if the course is scheduled to meet on ``day`` (a date)."""
        return day.weekday() in self.meeting_weekdays()

    def schedule_display(self):
        """Human-readable schedule, e.g. 'Mon/Wed/Fri 10:00–10:50'."""
        days = "/".join(self.DAY_NAMES[c] for c in self.meeting_days.upper()
                        if c in self.DAY_NAMES)
        return (f"{days} {self.start_time:%H:%M}–{self.end_time:%H:%M}")

    def enroll(self, student):
        """Enroll ``student``; returns the Enrollment (existing or new)."""
        enrollment, _ = Enrollment.objects.get_or_create(
            course=self, student=student
        )
        return enrollment

    def todays_lecture(self):
        """Return today's Lecture for this course, or None."""
        return self.lectures.filter(date=timezone.localdate()).first()


class Enrollment(models.Model):
    """
    Join table linking students to courses (many-to-many).

    Attributes:
        student:     The enrolled StudentProfile.
        course:      The Course enrolled in.
        enrolled_at: When the enrollment was created.

    A student can be enrolled in a given course only once.
    """

    student = models.ForeignKey(
        StudentProfile, on_delete=models.CASCADE, related_name="enrollments"
    )
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="enrollments"
    )
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["course", "student"]
        constraints = [
            models.UniqueConstraint(
                fields=["student", "course"], name="unique_enrollment"
            ),
        ]

    def __str__(self):
        return f"{self.student} → {self.course.code}"


# ---------------------------------------------------------------------------
# Lectures and attendance
# ---------------------------------------------------------------------------

class Lecture(models.Model):
    """
    A single class meeting of a course.

    Attributes:
        course:  The Course this lecture belongs to.
        date:    Calendar date of the meeting.
        qr_code: Unique, unguessable identifier encoded in the QR code
                 shown in class. Generated automatically.
        topic:   Optional lecture topic.

    Relationships:
        uploads (reverse of QRCodeUpload.lecture): student check-ins.

    A course has at most one lecture per date.
    """

    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="lectures"
    )
    date = models.DateField()
    qr_code = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    topic = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["course", "date"]
        constraints = [
            models.UniqueConstraint(
                fields=["course", "date"], name="one_lecture_per_course_per_day"
            ),
        ]

    def __str__(self):
        return f"{self.course.code} – {self.date:%Y-%m-%d}"

    def is_today(self):
        """Return True if this lecture takes place today."""
        return self.date == timezone.localdate()

    def attendees(self):
        """Return the StudentProfiles who checked in to this lecture."""
        return StudentProfile.objects.filter(uploads__lecture=self).distinct()

    def attendance_count(self):
        """Number of distinct students who checked in."""
        return self.attendees().count()

    def absentees(self):
        """Return enrolled students with no check-in for this lecture."""
        return self.course.students.exclude(uploads__lecture=self)

    def regenerate_qr_code(self):
        """Issue a fresh QR identifier (e.g. if the old one leaked)."""
        self.qr_code = uuid.uuid4()
        self.save(update_fields=["qr_code"])
        return self.qr_code


def qr_upload_path(instance, filename):
    """Store uploads as qr_uploads/<student_id>/<YYYY-MM-DD>/<filename>."""
    day = timezone.localdate().isoformat()
    return f"qr_uploads/{instance.student.student_id}/{day}/{filename}"


class QRCodeUpload(models.Model):
    """
    A student's photo of a lecture QR code, used as proof of attendance.

    Attributes:
        student:      The StudentProfile who uploaded the image (required).
        lecture:      The Lecture this upload counts for. Optional: it is
                      NULL until the QR code is decoded and matched, or if
                      the code didn't match any lecture.
        image:        The uploaded photo.
        decoded_code: The value read from the QR code, if decoding succeeded.
        uploaded_at:  Upload timestamp.

    Use ``match_lecture()`` after decoding to link the upload to its lecture.
    """

    student = models.ForeignKey(
        StudentProfile, on_delete=models.CASCADE, related_name="uploads"
    )
    lecture = models.ForeignKey(
        Lecture,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploads",
    )
    image = models.ImageField(upload_to=qr_upload_path)
    decoded_code = models.UUIDField(null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        target = self.lecture or "unmatched"
        return f"{self.student} @ {target} ({self.uploaded_at:%Y-%m-%d %H:%M})"

    def match_lecture(self, save=True):
        """
        Link this upload to the Lecture whose ``qr_code`` equals
        ``decoded_code``, but only if the student is enrolled in that
        course and the lecture is today. Returns the Lecture or None.
        """
        if self.decoded_code is None:
            return None
        lecture = Lecture.objects.filter(qr_code=self.decoded_code).first()
        if (lecture is None
                or not lecture.is_today()
                or not self.student.is_enrolled_in(lecture.course)):
            return None
        self.lecture = lecture
        if save:
            self.save(update_fields=["lecture"])
        return lecture

    @property
    def is_valid(self):
        """True if the upload is linked to a lecture and its code matches."""
        return (self.lecture is not None
                and self.decoded_code == self.lecture.qr_code)