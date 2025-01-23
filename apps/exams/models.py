from decimal import Decimal
from django.db import models
from django.db.models import Q,Avg
from apps.main.models import GradingConfig, MeanGradeConfig, Term
from apps.students.models import Student, StudentSubject
import logging
# Create your models here.
class MarksData(models.Model):
    MIDTERM = 'Midterm'
    ENDTERM = 'Endterm'
    QUIZ = 'Quiz'
    PRACTICAL = 'Practical'

    EXAM_TYPE_CHOICES = [
        (MIDTERM, 'Midterm'),
        (ENDTERM, 'Endterm'),
        (QUIZ, 'Quiz'),
        (PRACTICAL, 'Practical'),
    ]
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    student_subject = models.ForeignKey(StudentSubject, on_delete=models.CASCADE)
    term = models.ForeignKey(Term, on_delete=models.CASCADE, null=True)
    exam_type = models.CharField(max_length=20, choices=EXAM_TYPE_CHOICES)
    total_score = models.FloatField()
    
    
    class Meta:
        unique_together = ('student', 'student_subject', 'term', 'exam_type') 
        
    
    
    
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
        if grade_config:
            pass
            # print(f"Points for {self.student_subject.subject.subject_name}: {grade_config.points}")
        else:
            pass
            # print(f"No grade config found for {self.student_subject.subject.subject_name}")
        return grade_config.points if grade_config else 0
    
    def remarks(self):
        subject_category = self.student_subject.subject.category
        grade_config = GradingConfig.objects.filter(
            Q(subject_category=subject_category)&
            Q(min_marks__lte=self.total_score)&
            Q(max_marks__gte=self.total_score)
        
        ).first()
   
        return grade_config.remarks if grade_config else "No remarks"
    
    @classmethod
    def calculate_mean_grade(cls, student, term, exam_type=None):
        filters = {'student': student, 'term': term}
        if exam_type:
            filters['exam_type'] = exam_type
        # all_marks = cls.objects.filter(student=student, term=term)
        all_marks = cls.objects.filter(**filters)
        english_mark = all_marks.filter(student_subject__subject__subject_name="English").first()
        kiswahili_mark = all_marks.filter(student_subject__subject__subject_name="Kiswahili").first()

        
        student_level = student.class_level.level
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

        total_points = sum(float(subject.points()) for subject in subjects_for_calculation)
        mean_points = total_points / len(subjects_for_calculation) if subjects_for_calculation else 0.00
        # mean_points = round(mean_points, 2) if mean_points else 0.00
        # print(f"Mean points: {mean_points}")
        mean_marks = total_marks / len(subjects_for_calculation) if subjects_for_calculation else 0
        if mean_marks is not None:
            mean_marks = round(mean_marks, 2)
        else:
            mean_marks = "No marks"

        if mean_points is not None:
            mean_points = round(mean_points, 2)
        # print(f"Mean points: {mean_points}")
        mean_grade_config = MeanGradeConfig.objects.filter(
            Q(min_mean_points__lte=mean_points) &
            Q(max_mean_points__gte=mean_points)
        ).first()

        # if mean_grade_config:
        #     print(f"Found grade config: {mean_grade_config.grade} for mean points: {mean_points}")
        # else:
        #     print(f"No grade config found for mean points: {mean_points}")

        kcpe_average = student.kcpe_marks / 5 if student.kcpe_marks else 0
        if mean_grade_config:
            return {
                "mean_grade": str(mean_grade_config.grade),
                # "mean_points": float(mean_grade_config.points),
                "mean_points": mean_points,
                "mean_remarks": str(mean_grade_config.remarks),
                "principal_remarks": str(mean_grade_config.principal_remarks),
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
            "principal_remarks": "No principal remarks",
            "mean_marks": f"{mean_marks:.2f}" if mean_marks is not None else "No marks",
            "total_points": 0,
            "total_marks": 0,
            "grand_total": 0,
            "kcpe_average": kcpe_average
            
        }
