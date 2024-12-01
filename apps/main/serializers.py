from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from apps.main.models import ClassLevel, FormLevel, GradingConfig, MeanGradeConfig, Stream, Subject, SubjectCategory, Term

class SubjectCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SubjectCategory
        fields = '__all__'
        
        
class TermListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Term
        fields = "__all__"  
        

# class TermCreateSerializer(serializers.ModelSerializer):
#     class_levels = serializers.PrimaryKeyRelatedField(
#         queryset=ClassLevel.objects.all(),
#         many=True,  
#         required=False  
#     ) 
#     class Meta:
#         model = Term
#         fields = ['term', 'start_date', 'end_date']  

class FormLevelListSerializer(serializers.ModelSerializer):

    streams_count = serializers.SerializerMethodField()
    class Meta:
        model = FormLevel
        fields = ['id','name', 'level', 'streams_count',]
        
    
    def get_streams_count(self, obj):
        return ClassLevel.objects.filter(form_level=obj, stream__isnull=False).count()


class FormLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormLevel
        fields = "__all__"   
class StreamListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stream
        fields = '__all__'
class StreamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stream
        fields = ['name']
        
  
class ClassLevelListSerializer(serializers.ModelSerializer):
    stream = StreamListSerializer()
    form_level = FormLevelSerializer()
    class Meta:
        model = ClassLevel
        fields = '__all__'
   
class ClassLevelSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ClassLevel
        fields = '__all__'    
         
class TermSerializer(serializers.ModelSerializer):
     
    class Meta:
        model = Term
        fields = ['term',  'status', 'class_level']  
     
class SubjectSerializer(serializers.ModelSerializer):
    class_levels = ClassLevelSerializer(many=True, read_only=True)  

    class Meta:
        model = Subject
        fields = '__all__'   

class SubjectDetailSerializer(serializers.ModelSerializer):
    # class_levels = ClassLevelSerializer(many=True, read_only=True)  

    class Meta:
        model = Subject
        fields = ['id', 'subject_name']  
class ListSubjectSerializer(serializers.ModelSerializer):
    category=SubjectCategorySerializer()
    class_levels = ClassLevelListSerializer(many=True)
    class Meta:
        model = Subject
        fields = '__all__'
class GradingConfigSerializer(serializers.ModelSerializer):

    class Meta:
        model = GradingConfig
        fields=['grade', 'subject_category', 'min_marks', 'max_marks', 'points', 'remarks']
        read_only_fields = ['created_at', 'updated_at']  
        
class GradingConfigListSerializer(serializers.ModelSerializer):
    
    subject_category = SubjectCategorySerializer()
    class Meta:
        model = GradingConfig
        fields="__all__"
class MeanGradeConfigSerializer(serializers.ModelSerializer):

    class Meta:
        model = MeanGradeConfig
        fields="__all__"
        
class StudentMeanGradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MeanGradeConfig
        fields = '__all__'
        