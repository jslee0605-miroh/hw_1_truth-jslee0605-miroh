"""
views.py — HTTP request handlers for AttendanceChimp.

Each view corresponds to one URL endpoint.  Views receive an HTTP request,
interact with the database via models.py, and return an HTTP response.
"""

from django.shortcuts import render, redirect
from django.http import (HttpResponse, HttpResponseForbidden,
                         HttpResponseBadRequest, JsonResponse)
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login
from datetime import datetime
from django.contrib.auth.models import User
import zoneinfo
import json
import io
from .models import StudentProfile, InstructorProfile, Course, Enrollment, Lecture, QRCodeUpload

# from .models import (InstructorProfile, StudentProfile, Course, Enrollment,
#                      Lecture, QRCodeUpload, is_instructor, is_student,
#                      getUploadsForCourse)

CDT = zoneinfo.ZoneInfo("America/Chicago")


# ---------------------------------------------------------------------------
# HW2  — index, time, sum
# ---------------------------------------------------------------------------

def index(request):
    """Render the home page (index.html)."""

    context = {
        'current_datetime': datetime.now(CDT).strftime("%H:%M"),
        'is_authenticated': request.user.is_authenticated,
        'username': request.user.username if request.user.is_authenticated else None,
    }
    return render(request, 'app/index.html', context)

def time_view(request):
    """Return the current time in CDT in the form HH:MM and return it as a HTTPResponse object."""

    if request.method == 'GET':
        curr_time = datetime.now(
            zoneinfo.ZoneInfo("America/Chicago")
        ).strftime("%H:%M")
        return HttpResponse(curr_time)
    return HttpResponseBadRequest("Invalid request method. Use GET to get current CDT.")

def sum_view(request):
    """Returns the sum of the two numbers passed as query parameters and returns it as a JSON response."""

    if request.method == 'GET':
        num1 = request.GET.get('n1')
        num2 = request.GET.get('n2')

        return HttpResponse(str(float(num1) + float(num2)))

    return HttpResponseBadRequest("Invalid request method. Use GET to get the sum of 2 numbers.")

# ---------------------------------------------------------------------------
# HW4  — user creation
# ---------------------------------------------------------------------------

def new_user(request):
    if request.method == 'GET':
        return render(request, 'app/new.html')
    return HttpResponseBadRequest("Invalid request method. Use GET to access the new user form.")

@csrf_exempt
def createUser(request):
    if request.method == 'POST':
        new_username = request.POST.get('user_name')
        new_email = request.POST.get('email')
        new_password = request.POST.get('password')
        new_is_student = request.POST.get('is_student')
        if User.objects.filter(email = new_email).exists():
            return HttpResponseBadRequest("A user with this email already exists.")
        new_user = User.objects.create_user(
            username=new_username,
            email=new_email,
            password=new_password,
            is_staff=False,
            is_superuser=False
        )
        if new_is_student == '1':
            StudentProfile.objects.create(user=new_user)
        else:
            InstructorProfile.objects.create(user=new_user)
        return HttpResponse(f"User {new_user.username} created successfully.")
    elif request.method == 'GET':
        return HttpResponseBadRequest("Invalid request method. Use POST to create user.")

# ---------------------------------------------------------------------------
# HW5  — courses, lectures, QR uploads, dump
# ---------------------------------------------------------------------------



# ---------------------------------------------------------------------------
# HW6  — getUploads
# ---------------------------------------------------------------------------



