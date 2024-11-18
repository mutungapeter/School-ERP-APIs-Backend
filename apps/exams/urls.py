from django.urls import path

from .views import (
    MarksAPIView,
    ClassPerformanceView,
    FilterMarksDataView,
    ReportFormAPIView,
    StudentPerformanceView,
    UploadMarksAPIView
)



urlpatterns = [
    path('marks/', MarksAPIView.as_view(), name='marks-list'),
    path('upload-marks/', UploadMarksAPIView.as_view(), name='marks-list'),
    path('marks/<int:pk>/', MarksAPIView.as_view(), name='marks-detail-update-delete'),
    path('filter-marks/', FilterMarksDataView.as_view(), name='marks-list'),
    path('reports/', ReportFormAPIView.as_view(), name='reports'),
    path('class-performance/', ClassPerformanceView.as_view(), name='class-performance'),
    path('students/<int:pk>/performance/', StudentPerformanceView.as_view(), name='student_performance'),
   
]