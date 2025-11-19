from django.contrib import admin
from .models import Questionnaire

@admin.register(Questionnaire)
class QuestionnaireAdmin(admin.ModelAdmin):
    list_display = ['title', 'subject', 'department', 'uploader', 'file_type', 'uploaded_at']
    list_filter = ['department', 'subject', 'file_type', 'uploaded_at']
    search_fields = ['title', 'description', 'subject__name', 'uploader__user__first_name']
    date_hierarchy = 'uploaded_at'