from django.urls import path
from .views import (
    get_teacher_by_id,
    get_teacher_daily_schedule,
    get_teacher_monthly_hours,
    register_teacher,
    update_teacher_monthly_hours,
    submit_attendance,  # Import the submit_attendance view
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path("register/", register_teacher, name="register_teacher"),
    path("login/", TokenObtainPairView.as_view(), name="access_token"),
    path("refresh/", TokenRefreshView.as_view(), name="refresh_token"),
    path("teacher/<int:teacher_id>/", get_teacher_by_id, name="get_teacher_by_id"),
    path(
        "update_monthly_hours/",
        update_teacher_monthly_hours,
        name="update_monthly_hours",
    ),
    path(
        "submit_attendance/",
        submit_attendance,
        name="submit_attendance",  # Added endpoint for attendance submission
    ),
    path(
        "get_daily_schedule/",
        get_teacher_daily_schedule,
        name="get_teacher_daily_schedule",
    ),
    path(
        "get_monthly_hours/",
        get_teacher_monthly_hours,
        name="get_teacher_monthly_hours",
    ),
]
