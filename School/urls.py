
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    # path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path("api/v1/", include("apps.main.urls")),
    path("api/v1/", include("apps.users.urls")),
    path("api/v1/", include("apps.teachers.urls")),
    path("api/v1/", include("apps.students.urls")),
    path("api/v1/", include("apps.exams.urls")),
]
