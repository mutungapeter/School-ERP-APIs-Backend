from django.contrib import admin
from .models import FormLevel, GradingConfig, MeanGradeConfig, Stream, ClassLevel , Subject, SubjectCategory, Term
# Register your models here.

class SubjectAdmin(admin.ModelAdmin):
    list_display = ('id', 'subject_name', 'subject_type', 'category')

admin.site.register(Subject, SubjectAdmin)
class TermAdmin(admin.ModelAdmin):
    list_display = ('id', 'term','class_level', 'start_date', 'end_date', 'status')

admin.site.register(Term, TermAdmin)
class SubjectCategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', )

admin.site.register(SubjectCategory, SubjectCategoryAdmin)
class ClassLevelAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'stream', 'level', 'calendar_year' )

admin.site.register(ClassLevel, ClassLevelAdmin)
class StreamAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', )

admin.site.register(Stream, StreamAdmin)

class FormLevelAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'number_of_streams', 'level' )

admin.site.register(FormLevel, FormLevelAdmin)

class GradingConfigAdmin(admin.ModelAdmin):
    list_display = ('subject_category', 'min_marks', 'max_marks', 'points' ,'grade',  'remarks',)

admin.site.register(GradingConfig, GradingConfigAdmin)

class MeanGradeConfigAdmin(admin.ModelAdmin):
    list_display = ('min_mean_points','max_mean_points' ,'grade',  'remarks', 'principal_remarks')

admin.site.register(MeanGradeConfig, MeanGradeConfigAdmin)

