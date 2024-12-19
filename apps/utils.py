# utils.py
from rest_framework.pagination import PageNumberPagination

from apps.students.models import StudentSubject
from apps.main.models import Subject

class DataPagination(PageNumberPagination):
    page_size = 15  
    page_size_query_param = 'page_size'
    max_page_size = 100

def assign_all_subjects(student):
    all_subjects = Subject.objects.all()
    class_level = student.class_level  
    for subject in all_subjects:
        StudentSubject.objects.get_or_create(
            student=student,
            subject=subject,
            class_level=class_level
        )

def assign_core_subjects(student, core_subjects):
    class_level = student.class_level 
    filtered_core_subjects = core_subjects.filter(class_levels=class_level) 
    for subject in filtered_core_subjects:
        if not StudentSubject.objects.filter(student=student, subject=subject, class_level=class_level).exists():
            StudentSubject.objects.create(
                student=student,
                subject=subject,
                class_level=class_level
            )

def assign_electives(student, selected_electives):
    
    StudentSubject.objects.filter(student=student, subject__subject_type='Elective').delete()

    class_level = student.class_level 
    for elective in selected_electives:
        StudentSubject.objects.get_or_create(
            student=student,
            subject=elective,
            class_level=class_level
        )

def retain_current_student_subjects(student):
    current_student_subjects = StudentSubject.objects.filter(student=student)
    class_level = student.class_level  

    for student_subject in current_student_subjects:
        if not StudentSubject.objects.filter(student=student, subject=student_subject.subject, class_level=class_level).exists():
            StudentSubject.objects.create(
                student=student,
                subject=student_subject.subject,
                class_level=class_level
            )
