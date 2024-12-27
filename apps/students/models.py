from django.db import models

from apps.main.models import ClassLevel, Stream, Subject
from django.utils import timezone
from django.core.exceptions import ValidationError
from apps.main.models import Term
class AbstractBaseModel(models.Model):
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
# Create your models here.
ADMISSION_TYPE_CHOICES = [
        ('New Admission', 'New Admission'),
        ('Transfer', 'Transfer')
    ]
GENDER_CHOICES = [
    ('Male', 'Male'),
    ('Female', 'Female'),
]
STATUS_CHOICES = [
    ('Active', 'Active'),
    ('Graduated', 'Graduated'),
    ('Transferred', 'Transferred'),
]
class Student(AbstractBaseModel):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    admission_number = models.CharField(max_length=255, unique=True)
    kcpe_marks = models.IntegerField(default=0)
    gender = models.CharField(max_length=255, choices=GENDER_CHOICES)
    class_level = models.ForeignKey(ClassLevel, null=True, blank=True, on_delete=models.CASCADE)  
    admission_type = models.CharField(max_length=255, choices=ADMISSION_TYPE_CHOICES, default='New Admission')
    status = models.CharField(max_length=255, choices=STATUS_CHOICES, default='Active')
    current_term = models.ForeignKey(Term, on_delete=models.CASCADE)
    
    def __str__(self):
         return f"{self.first_name} {self.last_name} "

class StudentSubject(AbstractBaseModel):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    class_level = models.ForeignKey(ClassLevel, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('student', 'subject', 'class_level')

    def __str__(self):
        
        return f"{self.student} - {self.subject} -{self.class_level}"
    
class PromotionRecord(AbstractBaseModel):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    source_class_level = models.ForeignKey(ClassLevel, on_delete=models.SET_NULL, null=True, related_name="source_promotion_records")
    target_class_level = models.ForeignKey(ClassLevel, on_delete=models.SET_NULL, null=True, related_name="target_promotion_records")
    year = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.student.first_name} {self.student.last_name}"

class GraduationRecord(AbstractBaseModel):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    graduation_year = models.IntegerField(default=0)
    final_class_level = models.ForeignKey(ClassLevel, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        unique_together = ('student', 'graduation_year')
    def __str__(self):
        return f"Graduation - {self.student.first_name} {self.student.last_name} ({self.graduation_year})"
    
   