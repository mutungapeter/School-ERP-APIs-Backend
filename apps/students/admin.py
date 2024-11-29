from django.contrib import admin
from .models import PromotionRecord, Student,GraduationRecord, StudentSubject
# Register your models here.

class StudentAdmin(admin.ModelAdmin):
    list_display = ('id', 'first_name', 'last_name', 'admission_number', 'current_term', 'gender', 'class_level', 'admission_type','kcpe_marks', 'status', 'created_at',)
    def created_at(self, obj):
        return obj.created_at
    created_at.short_description = 'Admission Date'
admin.site.register(Student, StudentAdmin)

class StudentSubjectAdmin(admin.ModelAdmin):
    list_display = ('id', 'student', 'subject', 'class_level' )

admin.site.register(StudentSubject, StudentSubjectAdmin)
class PromotionRecordAdmin(admin.ModelAdmin):
    list_display = ('id','student', 'source_class_level', 'target_class_level','year', 'created_at',)

admin.site.register(PromotionRecord, PromotionRecordAdmin)
class GraduationRecordAdmin(admin.ModelAdmin):
    list_display = ('id','student', 'final_class_level','graduation_year', 'created_at',)

admin.site.register(GraduationRecord, GraduationRecordAdmin)
