import datetime
from django.db import models
from django.utils import timezone
from datetime import datetime
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator

current_year = datetime.now().year
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
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Active')
    class_level = models.ForeignKey(
        'ClassLevel',
        on_delete=models.CASCADE,
        related_name='terms'
    ) 
    
    def save(self, *args, **kwargs):
        if isinstance(self.start_date, str):
            self.start_date = datetime.strptime(self.start_date, '%Y-%m-%d').date()
        if isinstance(self.end_date, str):
            self.end_date = datetime.strptime(self.end_date, '%Y-%m-%d').date()
        today = timezone.now().date()
        if self.start_date and self.end_date:
            if self.start_date > today:
                self.status = 'Upcoming'
            elif self.end_date < today:
                self.status = 'Ended'
            else:
                self.status = 'Active'
        
        super().save(*args, **kwargs)
    def __str__(self):
        return f"{self.term} ({self.start_date} - {self.end_date}) - {self.class_level}"
    

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
        return f"{self.name} - {self.level}"
    
    def number_of_streams(self):
        return ClassLevel.objects.filter(form_level=self).count()
    
class Stream(AbstractBaseModel):
    name = models.CharField(max_length=10, unique=True)
    
    def __str__(self):
        return self.name
class ClassLevel(AbstractBaseModel):
    form_level = models.ForeignKey(FormLevel, on_delete=models.CASCADE)
    stream = models.ForeignKey(Stream, on_delete=models.SET_NULL, null=True, blank=True)
    calendar_year = models.IntegerField(
    validators=[MinValueValidator(1900), MaxValueValidator(current_year + 10)],
    help_text="Enter a valid year.",
    null=True
    )
    class Meta:
        unique_together = ('stream', 'form_level', 'calendar_year') 


        
    def __str__(self):
        return f"{self.form_level} {self.stream}- {self.calendar_year}"
    
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
