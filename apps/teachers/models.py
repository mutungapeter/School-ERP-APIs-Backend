from django.db import models
from apps.main.models import ClassLevel, Subject, AbstractBaseModel
from apps.users.models import User
# Create your models here.

class Teacher(AbstractBaseModel):
    GENDER_CHOICES = [
    ('Male', 'Male'),
    ('Female', 'Female'),
]
    user = models.OneToOneField(User, on_delete=models.CASCADE, limit_choices_to={'role': 'Teacher'})
    staff_no = models.CharField(max_length=20, unique=True)
    gender = models.CharField(max_length=255, choices=GENDER_CHOICES)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"
    
    @property
    def full_name(self):
        first_name = self.user.first_name if self.user.first_name else "missing first_name"
        last_name = self.user.last_name if self.user.last_name else "missing last_namee"
        return f"{first_name} {last_name}"
    
    @property
    def username(self):
        return self.user.username if self.user.username else "Unknown"

    def __str__(self):
        return self.full_name



    

   
class TeacherSubject(models.Model):
    teacher = models.ForeignKey(Teacher, related_name='teachersubject_set', on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    class_level = models.ForeignKey(ClassLevel, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('teacher', 'subject', 'class_level')

    def __str__(self):
        return f"{self.teacher.user.first_name} {self.teacher.user.last_name} teaches {self.subject.subject_name} in {self.class_level}"
