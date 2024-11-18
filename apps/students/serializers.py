from rest_framework import serializers

from apps.main.serializers import ClassLevelListSerializer, ClassLevelSerializer, SubjectSerializer
from apps.students.models import PromotionRecord, Student, StudentSubject,GraduationRecord

    

        
class StudentSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Student
        fields = ['first_name', 'last_name', 'gender', 'admission_number','kcpe_marks',  'class_level', 'current_term', 'admission_type']
    

class AllStudentsFieldsSerializer(serializers.ModelSerializer):
    # class_level = ClassLevelListSerializer()
    class Meta:
        model = Student
        fields = '__all__'


class StudentSubjectSerializer(serializers.ModelSerializer):
    subject = serializers.SerializerMethodField()
    student = AllStudentsFieldsSerializer()
    class Meta:
        model = StudentSubject
        fields = ['id','student', 'subject']
        
    def get_subject(self, obj):
        subject = obj.subject  
        return {
            "id": subject.id,
            "subject_name": subject.subject_name,
            "subject_type": subject.subject_type,
            "category": subject.category.name if subject.category else None
        }
class StudentListSerializer(serializers.ModelSerializer):
    subjects = StudentSubjectSerializer(source='studentsubject_set', many=True, )
    class_level = ClassLevelListSerializer()
    class Meta:
        model = Student
        fields = ['id', 'first_name', 'last_name','kcpe_marks', 'gender', 'admission_number',  'class_level', 'admission_type', 'subjects','status','created_at']
    
class StudentReportSerializer(serializers.ModelSerializer):
    
    class_level = ClassLevelListSerializer()
    class Meta:
        model = Student
        fields = ['id', 'first_name', 'last_name','kcpe_marks', 'gender', 'admission_number',  'class_level', 'admission_type','created_at']
    
class PromoteStudentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromotionRecord
        fields = ["source_class_level", "target_class_level", "year"]
class PromoteStudentsToAlumniSerializer(serializers.ModelSerializer):
    class Meta:
        model = GraduationRecord
        fields = ["final_class_level", "graduation_year"]
class GraduationRecordsSerializer(serializers.ModelSerializer):
    student = AllStudentsFieldsSerializer()
    final_class_level = ClassLevelListSerializer()
    class Meta:
        model = GraduationRecord
        fields = "__all__"
class PromotionRecordsSerializer(serializers.ModelSerializer):
    student = AllStudentsFieldsSerializer()
    source_class_level = ClassLevelListSerializer()
    target_class_level = ClassLevelListSerializer()
    class Meta:
        model = PromotionRecord
        fields = ['student','source_class_level','target_class_level','year' ]