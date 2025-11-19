# ============================================================================
# FILE: accounts/admin.py
# ============================================================================

from django.contrib import admin
from .models import Department, Subject, TeacherProfile

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'created_at']
    search_fields = ['name', 'code']

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'get_departments_display', 'created_at']
    list_filter = ['departments']
    search_fields = ['name', 'code']
    filter_horizontal = ['departments']
    
    def get_departments_display(self, obj):
        return ", ".join([dept.code for dept in obj.departments.all()])
    get_departments_display.short_description = 'Departments'

@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ['employee_id', 'user', 'department', 'is_active', 'created_at']
    list_filter = ['department', 'is_active']
    search_fields = ['employee_id', 'user__first_name', 'user__last_name']
