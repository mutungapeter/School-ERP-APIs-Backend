import datetime
from django.db import models
from django.utils import timezone
from datetime import datetime
from django.core.exceptions import ValidationError

class AbstractBaseModel(models.Model):
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Term(AbstractBaseModel):
    TERM_CHOICES = [
        ('Term 1', 'Term 1'),
        ('Term 2', 'Term 2'),
        ('Term 3', 'Term 3'),
    ]
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Ended', 'Ended'),
        ('Upcoming', 'Upcoming'),
    ]
    term = models.CharField(max_length=10, choices=TERM_CHOICES)
    calendar_year = models.IntegerField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Active')
 
    class Meta:
        unique_together = ('term', 'calendar_year')
    
    def __str__(self):
        return f"{self.term} - {self.calendar_year}"
    def clean(self):
            super().clean()
            min_year = 1900
            max_year = timezone.now().year + 100  
            if self.calendar_year is not None:
                if not (min_year <= self.calendar_year <= max_year):
                    raise ValidationError(f"Year must be between {min_year} and {max_year}.")

    def save(self, *args, **kwargs):
        if not self.calendar_year:
          self.calendar_year = timezone.now().year
        self.full_clean() 
        super(Term, self).save(*args, **kwargs)

class SubjectCategory(AbstractBaseModel):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name
    
class Subject(AbstractBaseModel):
   
    SUBJECT_TYPE_CHOICES = [
        ('Core', 'Core'),
        ('Elective', 'Elective')
    ]
    subject_name = models.CharField(max_length=50, unique=True)
    subject_type = models.CharField(max_length=20, choices=SUBJECT_TYPE_CHOICES, default='Core')
    category = models.ForeignKey(SubjectCategory, on_delete=models.SET_NULL, null=True) 
    class_levels = models.ManyToManyField('ClassLevel', related_name='subjects') 

    def __str__(self):
        return self.subject_name
    
class FormLevel(AbstractBaseModel):
    name = models.CharField(max_length=10, unique=True)
    level = models.IntegerField(unique=True)
    
    def __str__(self):
        return self.name
    
    def number_of_streams(self):
        return ClassLevel.objects.filter(form_level=self).count()
    
class Stream(AbstractBaseModel):
    name = models.CharField(max_length=10, unique=True)
    
    def __str__(self):
        return self.name
class ClassLevel(AbstractBaseModel):
    form_level = models.ForeignKey(FormLevel, on_delete=models.CASCADE)
    stream = models.ForeignKey(Stream, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        unique_together = ('stream', 'form_level') 
        
    def __str__(self):
        return f"{self.form_level} {self.stream}"
    
class GradingConfig(AbstractBaseModel):
    grade = models.CharField(max_length=255)
    subject_category = models.ForeignKey(SubjectCategory, on_delete=models.CASCADE)
    min_marks = models.FloatField(default=0)
    max_marks = models.FloatField(default=0)
    remarks = models.CharField(max_length=255)
    points = models.IntegerField(default=0)
    
    class Meta:
        unique_together = ('grade', 'subject_category')
    def __str__(self):
        
        return self.grade
    
class MeanGradeConfig(AbstractBaseModel):
    grade = models.CharField(max_length=255)
    min_mean_marks = models.FloatField(default=0)
    max_mean_marks = models.FloatField(default=0)
    remarks = models.CharField(max_length=255)
    points = models.IntegerField(default=0)

    class Meta:
        unique_together = ('grade',)
    def __str__(self):
        return self.grade
