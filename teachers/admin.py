from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Teacher

admin.site.register(Teacher, UserAdmin)
