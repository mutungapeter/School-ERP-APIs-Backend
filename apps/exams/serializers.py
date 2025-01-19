from rest_framework import serializers
from apps.exams.models import MarksData
from django.db import IntegrityError
from apps.main.serializers import ClassLevelSerializer, TermSerializer,TermListSerializer
from apps.students.serializers import StudentListSerializer,AllStudentsFieldsSerializer, StudentSubjectSerializer
from apps.teachers.models import TeacherSubject
class MarkListSerializer(serializers.ModelSerializer):
    
    grade = serializers.SerializerMethodField()
    points = serializers.SerializerMethodField()
    remarks = serializers.SerializerMethodField()
    student =  AllStudentsFieldsSerializer()
    student_subject = StudentSubjectSerializer()
    term = TermListSerializer()
    
    class Meta:
        model = MarksData
        fields = '__all__'

    
    def get_grade(self, obj):
        return obj.grade()

    def get_points(self, obj):
        return obj.points()

    def get_remarks(self, obj):
        return obj.remarks()
    
    
class ReportMarkListSerializer(serializers.ModelSerializer):
    
    grade = serializers.SerializerMethodField()
    points = serializers.SerializerMethodField()
    remarks = serializers.SerializerMethodField()
    student =  AllStudentsFieldsSerializer()
    student_subject = StudentSubjectSerializer()
    term = TermSerializer()
    teacher = serializers.SerializerMethodField()
    # class_level = ClassLevelSerializer()
    class Meta:
        model = MarksData
        fields = '__all__'

    
    def get_grade(self, obj):
        return obj.grade()

    def get_points(self, obj):
        return obj.points()

    def get_remarks(self, obj):
        return obj.remarks()
    def get_teacher(self, obj):
        try:
            teacher_subject = TeacherSubject.objects.get(
                subject=obj.student_subject.subject,
                class_level=obj.student_subject.student.class_level
            )
            return {
                "id": teacher_subject.teacher.id,
                "first_name": teacher_subject.teacher.user.first_name,
                "last_name": teacher_subject.teacher.user.last_name,
            }
        except TeacherSubject.DoesNotExist:
            return None

class MarkSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarksData
        fields = ['student', 'student_subject', 'cat_mark','term', 'exam_mark']

 
    
