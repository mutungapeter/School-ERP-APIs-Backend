# utils.py
from rest_framework.pagination import PageNumberPagination

from apps.students.models import StudentSubject
from apps.main.models import Subject

class DataPagination(PageNumberPagination):
    page_size = 15  
    page_size_query_param = 'page_size'
    max_page_size = 100

def assign_all_subjects(student):
    class_level = student.class_level  
    all_subjects = Subject.objects.filter(class_levels=class_level)
    for subject in all_subjects:
        StudentSubject.objects.get_or_create(
            student=student,
            subject=subject,
            class_level=class_level
        )

def assign_core_subjects(student):
    class_level = student.class_level
    print('class_level in assign_core subjects:', class_level)
    core_subjects = Subject.objects.filter(subject_type='Core', class_levels=class_level)
    print('core_subjects:', core_subjects)
    for subject in core_subjects:
        if not StudentSubject.objects.filter(student=student, subject=subject, class_level=class_level).exists():
            StudentSubject.objects.create(
                student=student,
                subject=subject,
                class_level=class_level
            )


def assign_electives(student, elective_subjects):
    class_level = student.class_level
    for elective in elective_subjects:
        if not StudentSubject.objects.filter(student=student, subject=elective, class_level=class_level).exists():
            StudentSubject.objects.create(
                student=student,
                subject=elective,
                class_level=class_level
            )
def retain_current_student_subjects(student):
    class_level = student.class_level  
    final_student_subjects = Subject.objects.filter(subject_type='Core', class_levels=class_level)
    for subject in final_student_subjects:
        if not StudentSubject.objects.filter(student=student, subject=subject, class_level=class_level).exists():
            StudentSubject.objects.create(
                student=student,
                subject=subject,
                class_level=class_level
            )
   
