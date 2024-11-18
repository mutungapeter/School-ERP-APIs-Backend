from rest_framework import serializers
from apps.exams.models import MarksData
from django.db import IntegrityError
from apps.main.serializers import ClassLevelSerializer, TermSerializer
from apps.students.serializers import StudentListSerializer,AllStudentsFieldsSerializer, StudentSubjectSerializer

class MarkListSerializer(serializers.ModelSerializer):
    
    grade = serializers.SerializerMethodField()
    points = serializers.SerializerMethodField()
    remarks = serializers.SerializerMethodField()
    student =  AllStudentsFieldsSerializer()
    student_subject = StudentSubjectSerializer()
    term = TermSerializer()
    
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

class MarkSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarksData
        fields = ['student', 'student_subject', 'cat_mark','term', 'exam_mark']

 
    
