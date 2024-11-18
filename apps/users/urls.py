from django.urls import path 
from .views import AvailableTeacherUsersAPIView,UserProfileAPIView,ChangePasswordAPIView, LoginAPIView, PermissionViewSet, UserAPIView,PasswordResetRequestAPIView, PasswordResetAPIView
urlpatterns = [
    path('users/', UserAPIView.as_view(), name='users-list'),
    path('users/<int:pk>/', UserAPIView.as_view(), name='user-detail-update-delete'),
    path('profile/', UserProfileAPIView.as_view(), name='user-profile'),
    path('teacher-users/', AvailableTeacherUsersAPIView.as_view(), name='teacher-users'),
    path('login/', LoginAPIView.as_view(), name='login'),
    
    path('password-reset-request/', PasswordResetRequestAPIView.as_view(), name='password-reset-request'),
    path('reset-password/', PasswordResetAPIView.as_view(), name='reset-password'),
    path('change-password/', ChangePasswordAPIView.as_view(), name='change_password'),
    path('permissions/', PermissionViewSet.as_view({'get': 'list'})),
    
]