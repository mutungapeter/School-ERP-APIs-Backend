from django.urls import path

from .views import (
    AllClassLevelsAPIView,
    SubjectAPIView,
    SubjectCategoryAPIView,
    FormLevelAPIView,
    StreamAPIView,
    ClassLevelAPIView,
    GradingConfigAPIView,
    TermsAPIView,
    MeanGradeConfigAPIView,
    GraduatingClassAPIView,
    ActiveTermsAPIView,
    UpcomingTermsAPIView,
    CurrentCompletedClassesWaitingPromotionsAPIView,
    TargetClassReadyToReceivePromotedStudentsAPIView
)



urlpatterns = [
    path('subjects/', SubjectAPIView.as_view(), name='subject-list'),
    path('subjects/<int:pk>/', SubjectAPIView.as_view(), name='subject-detail-update-delete'),
    
    path('subject-categories/', SubjectCategoryAPIView.as_view(), name='subject-categories-list'),
    path('subject-categories/<int:pk>/', SubjectCategoryAPIView.as_view(), name='subject-category-detail-update-delete'),
    
    path('form-levels/', FormLevelAPIView.as_view(), name='form-levels-list'),
    path('form-levels/<int:pk>/', FormLevelAPIView.as_view(), name='form-level-detail-update-delete'),
    
    path('streams/', StreamAPIView.as_view(), name='streams-list'),
    path('streams/<int:pk>/', StreamAPIView.as_view(), name='stream-detail-update-delete'),
    
    path('terms/', TermsAPIView.as_view(), name='terms-list'),
    path('terms/<int:pk>/', TermsAPIView.as_view(), name='detail-update-delete'),
    path('active-terms/', ActiveTermsAPIView.as_view(), name='active-terms-list'),
    path('upcoming-terms/', UpcomingTermsAPIView.as_view(), name='upcoming-terms-list'),
    
    path('class-levels/', ClassLevelAPIView.as_view(), name='class-levels-list'),
    path('all-class-levels/', AllClassLevelsAPIView.as_view(), name='al-class-levels-list'),
    path('current-class-levels/', CurrentCompletedClassesWaitingPromotionsAPIView.as_view(), name='current-class-levels-list'),
    path('target-class-levels/', TargetClassReadyToReceivePromotedStudentsAPIView.as_view(), name='target-class-levels-list'),
    path('graduating-classes/', GraduatingClassAPIView.as_view(), name='graduating-class-levels-list'),
    path('class-levels/<int:pk>/', ClassLevelAPIView.as_view(), name='class-level-detail-update-delete'),
    
    path('grading-configs/', GradingConfigAPIView.as_view(), name='grading-configs-list'),
    path('grading-configs/<int:pk>/', GradingConfigAPIView.as_view(), name='grading-config-detail-update-delete'),
    
    path('mean-grade-configs/', MeanGradeConfigAPIView.as_view(), name='mean-grade-configs-list'),
    path('mean-grade-configs/<int:pk>/', MeanGradeConfigAPIView.as_view(), name='mean-grade-config-detail-update-delete'),
    
]