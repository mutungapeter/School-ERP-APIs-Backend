from decimal import Decimal
from django.db import models
from django.db.models import Q,Avg
from apps.main.models import GradingConfig, MeanGradeConfig, Term
from apps.students.models import Student, StudentSubject
import logging
# Create your models here.
class MarksData(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    student_subject = models.ForeignKey(StudentSubject, on_delete=models.CASCADE)
    term = models.ForeignKey(Term, on_delete=models.CASCADE, null=True)
    cat_mark = models.FloatField()
    exam_mark = models.FloatField()
    total_score = models.FloatField(editable=False) 
    
    
    class Meta:
        unique_together = ('student', 'student_subject', 'term') 
        
    
    def save(self, *args, **kwargs):  
        self.total_score = self.cat_mark + self.exam_mark
        super().save(*args, **kwargs)
    
   
    
    def grade(self):
        subject_category = self.student_subject.subject.category
        logging.info(f"Subject Category: {subject_category}, Total Score: {self.total_score}")

        grade_config = GradingConfig.objects.filter(
            Q(subject_category=subject_category)&
            Q(min_marks__lte=self.total_score)&
            Q(max_marks__gte=self.total_score)
        
        ).first()
   
        return grade_config.grade if grade_config else "No Grade"
    
    def points(self):
        subject_category = self.student_subject.subject.category
        grade_config = GradingConfig.objects.filter(
            Q(subject_category=subject_category)&
            Q(min_marks__lte=self.total_score)&
            Q(max_marks__gte=self.total_score)
        
        ).first()
        return grade_config.points if grade_config else "No Points for the marks range"
    
    def remarks(self):
        subject_category = self.student_subject.subject.category
        grade_config = GradingConfig.objects.filter(
            Q(subject_category=subject_category)&
            Q(min_marks__lte=self.total_score)&
            Q(max_marks__gte=self.total_score)
        
        ).first()
   
        return grade_config.remarks if grade_config else "No Remarks"
    
    @classmethod
    def calculate_mean_grade(cls, student, term):
        all_marks = cls.objects.filter(student=student, term=term)
        
        english_mark = all_marks.filter(student_subject__subject__subject_name="English").first()
        kiswahili_mark = all_marks.filter(student_subject__subject__subject_name="Kiswahili").first()

        
        student_level = student.class_level.form_level.level
        if student_level >= 3:
            
            if english_mark and kiswahili_mark:
                best_language = english_mark if english_mark.total_score >= kiswahili_mark.total_score else kiswahili_mark
                worst_language = kiswahili_mark if english_mark.total_score >= kiswahili_mark.total_score else english_mark
            else:
                best_language = english_mark or kiswahili_mark  
                worst_language = kiswahili_mark or english_mark

            
            compulsory_subjects = all_marks.filter(
                student_subject__subject__subject_name__in=[
                    "Mathematics"
                ]
            )
            if best_language is None:
                raise ValueError("best_language is unexpectedly None")
            
            remaining_subjects = all_marks.exclude(
                    student_subject__subject__subject_name__in=[
                        "Mathematics", best_language.student_subject.subject.subject_name,
                        
                    ]
                )
                       
            remaining_subjects = list(remaining_subjects) + [worst_language]

            top_5_remaining = sorted(remaining_subjects, key=lambda x: x.total_score, reverse=True)[:5]

            
            subjects_for_calculation = list(compulsory_subjects) + [best_language] + top_5_remaining
        else:
           
            subjects_for_calculation = all_marks

      
        total_marks = sum(subject.total_score for subject in subjects_for_calculation)
        grand_total = len(subjects_for_calculation) * 100
        total_points = sum(subject.points() for subject in subjects_for_calculation)
        mean_marks = total_marks / len(subjects_for_calculation) if subjects_for_calculation else 0
        if mean_marks is not None:
            mean_marks = round(mean_marks, 2)
        else:
            mean_marks = "No marks"

        
        mean_grade_config = MeanGradeConfig.objects.filter(
            Q(min_mean_marks__lte=mean_marks) &
            Q(max_mean_marks__gte=mean_marks)
        ).first()
        kcpe_average = student.kcpe_marks / 5 if student.kcpe_marks else 0
        if mean_grade_config:
            return {
                "mean_grade": str(mean_grade_config.grade),
                "mean_points": float(mean_grade_config.points),
                "mean_remarks": str(mean_grade_config.remarks),
                "mean_marks": f"{mean_marks:.2f}",
                "total_points": total_points,  
                "total_marks": total_marks,    
                "grand_total": grand_total,
                "kcpe_average": kcpe_average 
            }
        
        return {
            "mean_grade": "No Grade",
            "mean_points": 0,
            "mean_remarks": "No remarks",
            "mean_marks": f"{mean_marks:.2f}" if mean_marks is not None else "No marks",
            "total_points": 0,
            "total_marks": 0,
            "grand_total": 0,
            "kcpe_average": kcpe_average
            
        }
