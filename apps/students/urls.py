from django.urls import path

from .views import AssignElectivesAPIView,PromoteStudentsToAlumniAPIView,UploadStudentsAPIView, PromoteStudentsAPIView, StudentAPIView, StudentSubjectAPIView,FilterStudentsAPIView



urlpatterns = [
    path('students/', StudentAPIView.as_view(), name='students-list'),
    path('filter-students/', FilterStudentsAPIView.as_view(), name='filter-students-list'),
    path('upload-students/', UploadStudentsAPIView.as_view(), name='upload-students-list'),
    path('students/<int:pk>/', StudentAPIView.as_view(), name='student-detail-update-delete'),
    
    path('student-subjects/', StudentSubjectAPIView.as_view(), name='student-subject-list'),
    path('student-subjects/<int:student_id>/', StudentSubjectAPIView.as_view(), name='student-subject-by-student'),
    path('student-subjects/<int:pk>/', StudentSubjectAPIView.as_view(), name='student-subject-detail'),
    
    path("assign-electives/", AssignElectivesAPIView.as_view(), name="assign-electives"),
    
    path("promote-students/", PromoteStudentsAPIView.as_view(), name="promote-students"),
    path("promote-students-to-alumni/", PromoteStudentsToAlumniAPIView.as_view(), name="promote-students-to-alumni"),

   
]