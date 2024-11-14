import datetime
from django.forms import ValidationError
from django.shortcuts import render

from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status

from classes.models import Class
from .models import DailyHourEntry, Teacher  # Directly import Teacher model
from rest_framework_simplejwt.tokens import RefreshToken


@api_view(["POST"])
@permission_classes([AllowAny])
def register_teacher(request):
    username = request.data.get("username")
    password = request.data.get("password")
    name = request.data.get("name")  # Getting the name from the request data

    # Ensure username, password, and name are provided
    if not username or not password or not name:
        return Response(
            {"error": "Username, password, and name are required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        # Create a new teacher user with the provided name
        teacher = Teacher.objects.create_user(
            username=username,
            password=password,
            first_name=name,  # Storing the name in the first_name field
        )

        # Generate JWT token
        refresh = RefreshToken.for_user(teacher)
        return Response(
            {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            },
            status=status.HTTP_201_CREATED,
        )

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_teacher_by_id(request, teacher_id):
    try:
        # Retrieve the teacher using the provided teacher_id
        teacher = Teacher.objects.get(id=teacher_id)
    except Teacher.DoesNotExist:
        return Response(
            {"error": "Teacher not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    # Prepare the response data with the teacher's details
    teacher_data = {
        "id": teacher.id,
        "username": teacher.username,
        "first_name": teacher.first_name,
        "email": teacher.email,
        "monthly_hours": teacher.monthly_hours,
    }

    return Response(teacher_data, status=status.HTTP_200_OK)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_teacher(request, teacher_id):
    teacher = get_object_or_404(Teacher, id=teacher_id)
    teacher.delete()
    return Response(
        {"message": "Teacher deleted successfully."}, status=status.HTTP_204_NO_CONTENT
    )


# Endpoint to update monthly hours (based on added hours)
@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def update_teacher_monthly_hours(request):
    teacher = request.user  # The logged-in teacher (the one making the request)
    new_hours = request.data.get("added monthly hours")

    if new_hours is None:
        return Response(
            {"error": "Hours are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        new_hours = int(new_hours)  # Ensure the hours are an integer
    except ValueError:
        return Response(
            {"error": "Invalid hours value. It must be an integer."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Ensure hours added is between 1 and 7
    if not (1 <= new_hours <= 7):
        return Response(
            {"error": "You can only add between 1 and 7 hours in one request."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Check if the teacher has already added hours for today
    today = request.data.get("date", None)
    if not today:
        today = str(datetime.date.today())

    daily_entry = DailyHourEntry.objects.filter(teacher=teacher, date=today).first()

    # If a daily entry already exists for today, check if we exceed the 7-hour limit
    if daily_entry:
        if daily_entry.hours_added + new_hours > 7:
            return Response(
                {"error": "You cannot add more than 7 hours for today."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # Update the existing daily entry with the new hours
        daily_entry.hours_added += new_hours
        daily_entry.save()
    else:
        # If no entry exists for today, create a new daily entry
        DailyHourEntry.objects.create(
            teacher=teacher, date=today, hours_added=new_hours
        )

    # Update the teacher's monthly hours
    teacher.monthly_hours += new_hours
    teacher.save()

    return Response(
        {"message": f"Successfully updated monthly hours to {teacher.monthly_hours}."},
        status=status.HTTP_200_OK,
    )


# Endpoint to submit attendance for the classes the teacher was present in
@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def submit_attendance(request):
    teacher = request.user
    date = request.data.get("date", str(datetime.date.today()))  # Default to today
    class_attendances = request.data.get("classes", [])  # List of class attendance data

    if not class_attendances:
        return Response(
            {"error": "No class attendance data provided."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    total_hours_added = 0  # To track the total hours based on the attendance marked
    for class_data in class_attendances:
        class_id = class_data.get("class_id")
        was_present = class_data.get("was_present", False)

        try:
            class_instance = Class.objects.get(id=class_id, teacher=teacher)
        except Class.DoesNotExist:
            return Response(
                {
                    "error": f"Class with id {class_id} not found or does not belong to the teacher."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # Check if an attendance entry already exists for this class and date
        attendance, created = attendance.objects.get_or_create(
            teacher=teacher, class_instance=class_instance, date=date
        )
        attendance.was_present = was_present
        attendance.save()

        if was_present:
            total_hours_added += 1  # Assuming each class period is 1 hour

    # Now update the teacher's monthly hours
    today = date
    daily_entry = DailyHourEntry.objects.filter(teacher=teacher, date=today).first()

    if daily_entry:
        # Add the new hours to the existing daily entry
        if daily_entry.hours_added + total_hours_added > 7:
            return Response(
                {"error": "You cannot add more than 7 hours for today."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        daily_entry.hours_added += total_hours_added
        daily_entry.save()
    else:
        # If no entry exists, create a new one for today
        DailyHourEntry.objects.create(
            teacher=teacher, date=today, hours_added=total_hours_added
        )

    # Update the teacher's monthly hours
    teacher.monthly_hours += total_hours_added
    teacher.save()

    return Response(
        {"message": "Attendance and monthly hours updated successfully."},
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_teacher_daily_schedule(request):
    teacher = request.user  # Get the currently logged-in teacher
    today = str(datetime.date.today())  # Get today's date

    # Get all classes taught by the teacher today
    classes_today = Class.objects.filter(teacher=teacher, schedule__date=today)

    # Get the teacher's total hours for today
    daily_entry = DailyHourEntry.objects.filter(teacher=teacher, date=today).first()

    total_hours_today = daily_entry.hours_added if daily_entry else 0

    # Prepare the response data
    class_list = [
        {"class_name": cls.name, "class_time": cls.schedule.time()}
        for cls in classes_today
    ]

    return Response(
        {
            "today_schedule": class_list,
            "total_hours_added": total_hours_today,
        },
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_teacher_monthly_hours(request):
    teacher = request.user  # Get the currently logged-in teacher
    current_month = datetime.date.today().month  # Get the current month

    # Get all daily hour entries for the current month
    monthly_entries = DailyHourEntry.objects.filter(
        teacher=teacher, date__month=current_month
    )

    total_hours_this_month = sum(entry.hours_added for entry in monthly_entries)

    return Response(
        {
            "total_hours_this_month": total_hours_this_month,
        },
        status=status.HTTP_200_OK,
    )
