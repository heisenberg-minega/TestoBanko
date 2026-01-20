# ============================================================================
# FILE: questionnaires/views.py
# ============================================================================

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.http import FileResponse, Http404, JsonResponse
from .models import Questionnaire, ExtractedQuestion, QuestionType
from .forms import QuestionnaireUploadForm, QuestionnaireEditForm, QuestionnaireFilterForm
from accounts.models import TeacherProfile, Department, Subject
from .services import QuestionnaireExtractor

def is_admin(user):
    return user.is_authenticated and user.is_staff

def is_teacher(user):
    return user.is_authenticated and not user.is_staff and hasattr(user, 'teacher_profile')

@login_required
def upload_questionnaire(request):
    if request.user.is_staff:
        messages.error(request, 'Admins cannot upload questionnaires')
        return redirect('accounts:admin_dashboard')
    
    teacher = get_object_or_404(TeacherProfile, user=request.user)
    
    if request.method == 'POST':
        form = QuestionnaireUploadForm(request.POST, request.FILES, user=request.user)
        
        if form.is_valid():
            questionnaire = form.save(commit=False)
            questionnaire.uploader = teacher
            questionnaire.save()
            
            # Check if auto-extraction is enabled
            auto_extract = form.cleaned_data.get('auto_extract')
            question_types = form.cleaned_data.get('question_types')
            
            if auto_extract and question_types:
                try:
                    questionnaire.extraction_status = 'processing'
                    questionnaire.save()
                    
                    # Get selected question types
                    type_names = [qt.name for qt in question_types]
                    
                    # Extract questions using AI
                    extractor = QuestionnaireExtractor()
                    created_questions = extractor.process_questionnaire(
                        questionnaire, 
                        type_names
                    )
                    
                    questionnaire.extraction_status = 'completed'
                    questionnaire.is_extracted = True
                    questionnaire.save()
                    
                    messages.success(
                        request, 
                        f'Successfully uploaded and extracted {len(created_questions)} questions!'
                    )
                    
                    # Redirect to review extracted questions
                    return redirect('questionnaires:review_extracted', pk=questionnaire.pk)
                
                except Exception as e:
                    questionnaire.extraction_status = 'failed'
                    questionnaire.extraction_error = str(e)
                    questionnaire.save()
                    
                    messages.warning(
                        request,
                        f'File uploaded but extraction failed: {str(e)}. You can retry extraction later.'
                    )
                    return redirect('questionnaires:my_uploads')
            else:
                messages.success(request, 'Questionnaire uploaded successfully!')
                return redirect('questionnaires:my_uploads')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = QuestionnaireUploadForm(user=request.user)
    
    return render(request, 'teacher_dashboard/upload_questionnaire.html', {
        'form': form
    })


@login_required
def review_extracted_questions(request, pk):
    """Review and edit extracted questions before finalizing"""
    questionnaire = get_object_or_404(Questionnaire, pk=pk)
    
    # Check permissions
    if request.user.is_staff:
        can_view = True
    elif hasattr(request.user, 'teacher_profile'):
        can_view = questionnaire.uploader == request.user.teacher_profile
    else:
        can_view = False
    
    if not can_view:
        messages.error(request, 'You do not have permission to view this.')
        return redirect('questionnaires:browse_questionnaires')
    
    extracted_questions = questionnaire.extracted_questions.select_related('question_type').all()
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'approve_all':
            extracted_questions.update(is_approved=True)
            messages.success(request, 'All questions approved!')
            return redirect('questionnaires:my_uploads')
        
        elif action == 'delete_question':
            question_id = request.POST.get('question_id')
            ExtractedQuestion.objects.filter(id=question_id, questionnaire=questionnaire).delete()
            messages.info(request, 'Question deleted.')
            return redirect('questionnaires:review_extracted', pk=pk)
        
        elif action == 'retry_extraction':
            # Allow retry extraction
            return redirect('questionnaires:retry_extraction', pk=pk)
    
    # Calculate statistics
    total_points = sum(q.points for q in extracted_questions)
    question_types_count = extracted_questions.values('question_type').distinct().count()
    
    context = {
        'questionnaire': questionnaire,
        'questions': extracted_questions,
        'total_points': total_points,
        'question_types_count': question_types_count,
    }
    
    return render(request, 'teacher_dashboard/review_extracted.html', context)


@login_required
def retry_extraction(request, pk):
    """Retry question extraction for a questionnaire"""
    questionnaire = get_object_or_404(Questionnaire, pk=pk)
    
    # Check permissions
    if request.user.is_staff:
        can_retry = True
    elif hasattr(request.user, 'teacher_profile'):
        can_retry = questionnaire.uploader == request.user.teacher_profile
    else:
        can_retry = False
    
    if not can_retry:
        messages.error(request, 'You do not have permission to retry extraction.')
        return redirect('questionnaires:browse_questionnaires')
    
    if request.method == 'POST':
        # Get question types from form
        question_type_ids = request.POST.getlist('question_types')
        
        if not question_type_ids:
            messages.error(request, 'Please select at least one question type.')
            return redirect('questionnaires:retry_extraction', pk=pk)
        
        try:
            # Delete old extracted questions
            questionnaire.extracted_questions.all().delete()
            
            questionnaire.extraction_status = 'processing'
            questionnaire.save()
            
            # Get question types
            question_types = QuestionType.objects.filter(id__in=question_type_ids)
            type_names = [qt.name for qt in question_types]
            
            # Extract questions
            extractor = QuestionnaireExtractor()
            created_questions = extractor.process_questionnaire(questionnaire, type_names)
            
            questionnaire.extraction_status = 'completed'
            questionnaire.is_extracted = True
            questionnaire.extraction_error = None
            questionnaire.save()
            
            messages.success(request, f'Successfully extracted {len(created_questions)} questions!')
            return redirect('questionnaires:review_extracted', pk=questionnaire.pk)
        
        except Exception as e:
            questionnaire.extraction_status = 'failed'
            questionnaire.extraction_error = str(e)
            questionnaire.save()
            
            messages.error(request, f'Extraction failed: {str(e)}')
            return redirect('questionnaires:retry_extraction', pk=pk)
    
    question_types = QuestionType.objects.filter(is_active=True)
    
    return render(request, 'teacher_dashboard/retry_extraction.html', {
        'questionnaire': questionnaire,
        'question_types': question_types,
    })


@login_required
def my_uploads(request):
    if request.user.is_staff:
        return redirect('accounts:admin_dashboard')
    
    teacher = get_object_or_404(TeacherProfile, user=request.user)
    questionnaires = Questionnaire.objects.filter(uploader=teacher).select_related('department', 'subject')
    
    search_query = request.GET.get('search', '')
    if search_query:
        questionnaires = questionnaires.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(subject__name__icontains=search_query)
        )
    
    paginator = Paginator(questionnaires, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
    }
    return render(request, 'teacher_dashboard/my_uploads.html', context)


@login_required
def edit_questionnaire(request, pk):
    questionnaire = get_object_or_404(Questionnaire, pk=pk)
    
    # Check permissions
    if request.user.is_staff:
        can_edit = True
    elif hasattr(request.user, 'teacher_profile'):
        can_edit = questionnaire.uploader == request.user.teacher_profile
    else:
        can_edit = False
    
    if not can_edit:
        messages.error(request, 'You do not have permission to edit this questionnaire')
        return redirect('questionnaires:browse_questionnaires')
    
    if request.method == 'POST':
        form = QuestionnaireEditForm(request.POST, instance=questionnaire)
        if form.is_valid():
            form.save()
            messages.success(request, 'Questionnaire updated successfully')
            if request.user.is_staff:
                return redirect('questionnaires:all_questionnaires')
            return redirect('questionnaires:my_uploads')
    else:
        form = QuestionnaireEditForm(instance=questionnaire)
    
    return render(request, 'teacher_dashboard/edit_questionnaire.html', {
        'form': form,
        'questionnaire': questionnaire
    })


@login_required
def delete_questionnaire(request, pk):
    questionnaire = get_object_or_404(Questionnaire, pk=pk)
    
    # Check permissions
    if request.user.is_staff:
        can_delete = True
    elif hasattr(request.user, 'teacher_profile'):
        can_delete = questionnaire.uploader == request.user.teacher_profile
    else:
        can_delete = False
    
    if not can_delete:
        messages.error(request, 'You do not have permission to delete this questionnaire')
        return redirect('questionnaires:browse_questionnaires')
    
    if request.method == 'POST':
        questionnaire.file.delete()
        questionnaire.delete()
        messages.success(request, 'Questionnaire deleted successfully')
        if request.user.is_staff:
            return redirect('questionnaires:all_questionnaires')
        return redirect('questionnaires:my_uploads')
    
    return render(request, 'teacher_dashboard/delete_questionnaire.html', {
        'questionnaire': questionnaire
    })


@login_required
def browse_questionnaires(request):
    if request.user.is_staff:
        return redirect('questionnaires:all_questionnaires')
    
    questionnaires = Questionnaire.objects.select_related('department', 'subject', 'uploader__user').all()
    
    # Filtering
    department_id = request.GET.get('department')
    subject_id = request.GET.get('subject')
    search_query = request.GET.get('search', '')
    
    if department_id:
        questionnaires = questionnaires.filter(department_id=department_id)
    
    if subject_id:
        questionnaires = questionnaires.filter(subject_id=subject_id)
    
    if search_query:
        questionnaires = questionnaires.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(subject__name__icontains=search_query) |
            Q(subject__code__icontains=search_query)
        )
    
    # Get statistics
    departments = Department.objects.annotate(count=Count('questionnaires'))
    subjects = Subject.objects.all()
    
    paginator = Paginator(questionnaires, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'departments': departments,
        'subjects': subjects,
        'selected_department': department_id,
        'selected_subject': subject_id,
        'search_query': search_query,
    }
    return render(request, 'teacher_dashboard/browse_questionnaires.html', context)


@login_required
@user_passes_test(is_admin)
def all_questionnaires(request):
    questionnaires = Questionnaire.objects.select_related('department', 'subject', 'uploader__user').all()
    
    # Filtering
    department_id = request.GET.get('department')
    subject_id = request.GET.get('subject')
    search_query = request.GET.get('search', '')
    
    if department_id:
        questionnaires = questionnaires.filter(department_id=department_id)
    
    if subject_id:
        questionnaires = questionnaires.filter(subject_id=subject_id)
    
    if search_query:
        questionnaires = questionnaires.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(subject__name__icontains=search_query) |
            Q(uploader__user__first_name__icontains=search_query) |
            Q(uploader__user__last_name__icontains=search_query)
        )
    
    departments = Department.objects.all()
    subjects = Subject.objects.all()
    
    paginator = Paginator(questionnaires, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'departments': departments,
        'subjects': subjects,
        'selected_department': department_id,
        'selected_subject': subject_id,
        'search_query': search_query,
    }
    return render(request, 'admin_dashboard/all_questionnaires.html', context)


def get_client_ip(request):
    """Get the client's IP address from the request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@login_required
def download_questionnaire(request, pk):
    from .models import Download
    questionnaire = get_object_or_404(Questionnaire, pk=pk)
    
    # Create download record
    Download.objects.create(
        questionnaire=questionnaire,
        user=request.user if request.user.is_authenticated else None,
        ip_address=get_client_ip(request)
    )
    
    try:
        return FileResponse(
            questionnaire.file.open('rb'),
            as_attachment=True,
            filename=questionnaire.file.name.split('/')[-1]
        )
    except FileNotFoundError:
        raise Http404("File not found")


@login_required
def get_subjects_ajax(request):
    """AJAX endpoint to get subjects by department"""
    department_id = request.GET.get('department')
    
    if department_id:
        subjects = Subject.objects.filter(departments__id=department_id).values('id', 'code', 'name')
        return JsonResponse({'subjects': list(subjects)})
    
    return JsonResponse({'subjects': []})