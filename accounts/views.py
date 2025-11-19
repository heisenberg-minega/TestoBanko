# ============================================================================
# FILE: accounts/views.py
# ============================================================================

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q
from .models import TeacherProfile, Department, Subject
from .forms import TeacherCreationForm, TeacherEditForm, DepartmentForm, SubjectForm

def is_admin(user):
    return user.is_authenticated and user.is_staff

def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            if user.is_staff:
                return redirect('accounts:admin_dashboard')
            else:
                return redirect('accounts:teacher_dashboard')
        else:
            messages.error(request, 'Invalid username or password')
    
    return render(request, 'accounts/login.html')

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'Logged out successfully')
    return redirect('home')

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    total_teachers = TeacherProfile.objects.count()
    active_teachers = TeacherProfile.objects.filter(is_active=True).count()
    total_departments = Department.objects.count()
    total_subjects = Subject.objects.count()
    
    context = {
        'total_teachers': total_teachers,
        'active_teachers': active_teachers,
        'total_departments': total_departments,
        'total_subjects': total_subjects,
    }
    return render(request, 'admin_dashboard/dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def manage_teachers(request):
    teachers = TeacherProfile.objects.select_related('user', 'department').all()
    
    search_query = request.GET.get('search', '')
    if search_query:
        teachers = teachers.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(employee_id__icontains=search_query)
        )
    
    context = {'teachers': teachers, 'search_query': search_query}
    return render(request, 'admin_dashboard/manage_teachers.html', context)

@login_required
@user_passes_test(is_admin)
def add_teacher(request):
    if request.method == 'POST':
        form = TeacherCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Teacher added successfully')
            return redirect('accounts:manage_teachers')
    else:
        form = TeacherCreationForm()
    
    return render(request, 'admin_dashboard/add_teacher.html', {'form': form})

@login_required
@user_passes_test(is_admin)
def edit_teacher(request, pk):
    teacher = get_object_or_404(TeacherProfile, pk=pk)
    
    if request.method == 'POST':
        form = TeacherEditForm(request.POST, instance=teacher)
        if form.is_valid():
            teacher = form.save()
            teacher.user.first_name = form.cleaned_data['first_name']
            teacher.user.last_name = form.cleaned_data['last_name']
            teacher.user.email = form.cleaned_data['email']
            teacher.user.save()
            messages.success(request, 'Teacher updated successfully')
            return redirect('accounts:manage_teachers')
    else:
        form = TeacherEditForm(instance=teacher)
    
    return render(request, 'admin_dashboard/edit_teacher.html', {'form': form, 'teacher': teacher})

@login_required
@user_passes_test(is_admin)
def delete_teacher(request, pk):
    teacher = get_object_or_404(TeacherProfile, pk=pk)
    if request.method == 'POST':
        user = teacher.user
        teacher.delete()
        user.delete()
        messages.success(request, 'Teacher deleted successfully')
        return redirect('accounts:manage_teachers')
    
    return render(request, 'admin_dashboard/delete_teacher.html', {'teacher': teacher})

@login_required
@user_passes_test(is_admin)
def manage_departments(request):
    departments = Department.objects.all()
    
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Department added successfully')
            return redirect('accounts:manage_departments')
    else:
        form = DepartmentForm()
    
    context = {'departments': departments, 'form': form}
    return render(request, 'admin_dashboard/manage_departments.html', context)

@login_required
@user_passes_test(is_admin)
def edit_department(request, pk):
    department = get_object_or_404(Department, pk=pk)
    
    if request.method == 'POST':
        form = DepartmentForm(request.POST, instance=department)
        if form.is_valid():
            form.save()
            messages.success(request, 'Department updated successfully')
            return redirect('accounts:manage_departments')
    else:
        form = DepartmentForm(instance=department)
    
    return render(request, 'admin_dashboard/edit_department.html', {'form': form, 'department': department})

@login_required
@user_passes_test(is_admin)
def delete_department(request, pk):
    department = get_object_or_404(Department, pk=pk)
    if request.method == 'POST':
        department.delete()
        messages.success(request, 'Department deleted successfully')
        return redirect('accounts:manage_departments')
    
    return render(request, 'admin_dashboard/delete_department.html', {'department': department})

@login_required
@user_passes_test(is_admin)
def manage_subjects(request):
    subjects = Subject.objects.prefetch_related('departments').all()
    
    if request.method == 'POST':
        form = SubjectForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Subject added successfully')
            return redirect('accounts:manage_subjects')
    else:
        form = SubjectForm()
    
    context = {'subjects': subjects, 'form': form}
    return render(request, 'admin_dashboard/manage_subjects.html', context)

@login_required
@user_passes_test(is_admin)
def edit_subject(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    
    if request.method == 'POST':
        form = SubjectForm(request.POST, instance=subject)
        if form.is_valid():
            form.save()
            messages.success(request, 'Subject updated successfully')
            return redirect('accounts:manage_subjects')
    else:
        form = SubjectForm(instance=subject)
    
    return render(request, 'admin_dashboard/edit_subject.html', {'form': form, 'subject': subject})

@login_required
@user_passes_test(is_admin)
def delete_subject(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    if request.method == 'POST':
        subject.delete()
        messages.success(request, 'Subject deleted successfully')
        return redirect('accounts:manage_subjects')
    
    return render(request, 'admin_dashboard/delete_subject.html', {'subject': subject})

@login_required
def teacher_dashboard(request):
    if request.user.is_staff:
        return redirect('accounts:admin_dashboard')
    
    teacher = get_object_or_404(TeacherProfile, user=request.user)
    my_uploads = teacher.questionnaires.count()
    
    context = {
        'teacher': teacher,
        'my_uploads': my_uploads,
    }
    return render(request, 'teacher_dashboard/dashboard.html', context)