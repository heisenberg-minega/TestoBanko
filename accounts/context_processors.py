# accounts/context_processors.py
from .models import ActivityLog

def notifications_context(request):
    """Add notifications to all templates"""
    if request.user.is_authenticated:
        if request.user.is_staff:
            # ADMIN: Get ALL activities from all users
            all_activities = ActivityLog.objects.all().select_related('user').order_by('-created_at')[:50]
            unread_count = ActivityLog.objects.filter(is_read=False).count()
        else:
            # TEACHER: Get only THEIR OWN activities, exclude login activities
            all_activities = ActivityLog.objects.filter(
                user=request.user
            ).exclude(
                activity_type='user_login'
            ).select_related('user').order_by('-created_at')[:50]
            unread_count = ActivityLog.objects.filter(
                user=request.user,
                is_read=False
            ).exclude(
                activity_type='user_login'
            ).count()
        
        # Format for template
        formatted_activities = []
        for activity in all_activities:
            # Determine icon and color based on activity type
            if activity.activity_type == 'user_login' or 'logged in' in activity.description.lower():
                icon = 'bi-box-arrow-in-right'
                color = 'green'
                title = 'User Login'
            elif 'created' in activity.activity_type:
                icon = 'bi-plus-circle-fill'
                color = 'green'
                title = 'New Addition'
            elif 'updated' in activity.activity_type or 'edited' in activity.activity_type:
                icon = 'bi-pencil-fill'
                color = 'blue'
                title = 'Update'
            elif 'deleted' in activity.activity_type:
                icon = 'bi-trash-fill'
                color = 'red'
                title = 'Deletion'
            elif 'upload' in activity.activity_type:
                icon = 'bi-cloud-upload-fill'
                color = 'purple'
                title = 'Upload'
            elif 'teacher' in activity.activity_type:
                icon = 'bi-person-badge-fill'
                color = 'blue'
                title = 'Teacher Activity'
            elif 'department' in activity.activity_type:
                icon = 'bi-building'
                color = 'indigo'
                title = 'Department Activity'
            elif 'subject' in activity.activity_type:
                icon = 'bi-book-fill'
                color = 'purple'
                title = 'Subject Activity'
            else:
                icon = 'bi-info-circle-fill'
                color = 'gray'
                title = activity.get_activity_type_display() if hasattr(activity, 'get_activity_type_display') else 'Activity'
            
            formatted_activities.append({
                'id': activity.id,
                'title': title,
                'description': activity.description,
                'time': activity.created_at,
                'read': activity.is_read,
                'icon': icon,
                'color': color,
                'activity_type': activity.activity_type,
                'user': activity.user.get_full_name() if activity.user else 'System'
            })
        
        return {
            'recent_activities': formatted_activities,
            'unread_notification_count': unread_count
        }
    
    return {
        'recent_activities': [],
        'unread_notification_count': 0
    }