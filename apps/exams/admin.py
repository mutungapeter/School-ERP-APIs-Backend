from django.contrib import admin
from .models import MarksData
# Register your models here.

class MarksDataAdmin(admin.ModelAdmin):
    list_display = ('student__id', 'term','student', 'student_subject', 'cat_mark', 'exam_mark', 'total_score', 'grade', 'points', 'remarks')

admin.site.register(MarksData, MarksDataAdmin)
