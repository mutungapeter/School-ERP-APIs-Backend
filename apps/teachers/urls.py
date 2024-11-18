from django.urls import path

from .views import AssignTeacherView, TeacherAPIView, TeacherSubjectAPIView

urlpatterns = [
    path('teachers/', TeacherAPIView.as_view(), name='teachers-list'),
    path('teachers/<int:pk>/', TeacherAPIView.as_view(), name='teacher-detail-update-delete'),
    
    path('assign-teachers-to-subject/', AssignTeacherView.as_view(), name='assign-teachers-to-subject'),
    path('assign-teacher/<int:pk>/', AssignTeacherView.as_view(), name='update-teacher-assignments'),

    path('teacher-subjects/', TeacherSubjectAPIView.as_view(), name='teacher-subjects-list'),
    # path('teacher-subjects/<int:pk>/', TeacherSubjectAPIView.as_view(), name='teacher-subject-detail-update-delete'),
    # path('teacher-subjects/<int:teacher_id>/', TeacherSubjectAPIView.as_view(), name='teacher-subject-detail-update-delete'),
    
]