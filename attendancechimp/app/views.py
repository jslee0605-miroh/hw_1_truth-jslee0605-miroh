"""
views.py — HTTP request handlers for AttendanceChimp.

Each view corresponds to one URL endpoint.  Views receive an HTTP request,
interact with the database via models.py, and return an HTTP response.
"""

from django.shortcuts import render, redirect
from django.http import (HttpResponse, HttpResponseForbidden,
                         HttpResponseBadRequest, JsonResponse)
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from datetime import datetime
import zoneinfo
import json
import io

# from .models import (InstructorProfile, StudentProfile, Course, Enrollment,
#                      Lecture, QRCodeUpload, is_instructor, is_student,
#                      getUploadsForCourse)

CDT = zoneinfo.ZoneInfo("America/Chicago")


# ---------------------------------------------------------------------------
# HW2  — index, time, sum
# ---------------------------------------------------------------------------

def index(request):
    """Render the home page (index.html)."""

    context = {}
    return render(request, 'app/index.html', context)

def time_view(request):
    """Return the current time in CDT in the form HH:MM and return it as a HTTPResponse object."""

    if request.method == 'GET':
        curr_time = datetime.now(
            zoneinfo.ZoneInfo("America/Chicago")
        ).strftime("%H:%M:%S")
        return HttpResponse(curr_time)
    return HttpResponseBadRequest("Invalid request method. Use GET to get current CDT.")

def sum_view(request):
    """Returns the sum of the two numbers passed as query parameters and returns it as a JSON response."""
    
    if request.method == 'GET':
        num1 = request.GET.get('n1')
        num2 = request.GET.get('n2')

        return JsonResponse({'sum': int(num1) + int(num2)})

    return HttpResponseBadRequest("Invalid request method. Use GET to get the sum of 2 numbers.")

# ---------------------------------------------------------------------------
# HW4  — user creation
# ---------------------------------------------------------------------------



# ---------------------------------------------------------------------------
# HW5  — courses, lectures, QR uploads, dump
# ---------------------------------------------------------------------------



# ---------------------------------------------------------------------------
# HW6  — getUploads
# ---------------------------------------------------------------------------



