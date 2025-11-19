# ============================================================================
# FILE: questionnaires/urls.py
# ============================================================================

from django.urls import path
from . import views

app_name = 'questionnaires'

urlpatterns = [
    path('upload/', views.upload_questionnaire, name='upload_questionnaire'),
    path('my-uploads/', views.my_uploads, name='my_uploads'),
    path('browse/', views.browse_questionnaires, name='browse_questionnaires'),
    path('all/', views.all_questionnaires, name='all_questionnaires'),
    path('edit/<int:pk>/', views.edit_questionnaire, name='edit_questionnaire'),
    path('delete/<int:pk>/', views.delete_questionnaire, name='delete_questionnaire'),
    path('download/<int:pk>/', views.download_questionnaire, name='download_questionnaire'),
]
