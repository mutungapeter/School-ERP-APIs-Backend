from django.contrib import admin
from .models import Teacher, TeacherSubject
# Register your models here.


# class TeacherSubjectAdmin(admin.ModelAdmin):
#     list_display = ('teacher', 'class_level',)

# admin.site.register(TeacherSubject, TeacherSubjectAdmin)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ( 'id','full_name', 'username','staff_no', 'gender',)

admin.site.register(Teacher, TeacherAdmin)


@admin.register(TeacherSubject)
class TeacherSubjectAdmin(admin.ModelAdmin):
    pass