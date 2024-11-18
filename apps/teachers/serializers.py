from apps.main.serializers import ClassLevelListSerializer, ClassLevelSerializer, SubjectDetailSerializer, SubjectSerializer
from apps.users.models import User
from rest_framework import serializers

from apps.users.serializers import UserSerializer
from apps.teachers.models import Teacher, TeacherSubject


class TeacherSubjectCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeacherSubject
        fields = "__all__"
class TeacherSubjectAssignSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = TeacherSubject
        fields = ['teacher', 'subject', 'class_level']
    def create(self, validated_data):
        
        return TeacherSubject.objects.create(**validated_data)



class TeacherSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(write_only=True)
    last_name = serializers.CharField(write_only=True)
    username = serializers.CharField(write_only=True)
    email = serializers.EmailField(write_only=True)
    phone_number = serializers.CharField(write_only=True, allow_blank=True, required=False) 

    password = serializers.CharField(write_only=True)
    class Meta:
        model = Teacher
        fields = ['first_name', 'last_name', 'username', 'email','phone_number', 'password', 'staff_no', 'gender']
    def create(self, validated_data):
        user_data = {
            'first_name': validated_data.pop('first_name'),
            'last_name': validated_data.pop('last_name'),
            'username': validated_data.pop('username'),
            'email': validated_data.pop('email'),
            'phone_number': validated_data.pop('phone_number', None),
            'role': 'Teacher',  
        }
        password = validated_data.pop('password')

        user = User.objects.create(**user_data)
        user.set_password(password) 
        user.save()

        teacher = Teacher.objects.create(user=user, **validated_data)
        return teacher
    def update(self, instance, validated_data):
        user_data = {
            'first_name': validated_data.pop('first_name', instance.user.first_name),
            'last_name': validated_data.pop('last_name', instance.user.last_name),
            'username': validated_data.pop('username', instance.user.username),
            'email': validated_data.pop('email', instance.user.email),
            'phone_number': validated_data.pop('phone_number', instance.user.phone_number),
        }

        
        for attr, value in user_data.items():
            setattr(instance.user, attr, value)
        instance.user.save()

        
        if 'staff_no' in validated_data:
            instance.staff_no = validated_data['staff_no']
        
        if 'gender' in validated_data:
            instance.gender = validated_data['gender']
        instance.save()
        return instance

class TeacherDetailSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Teacher
        fields = "__all__"

class TeacherSubjectSerializer(serializers.ModelSerializer):
    subject =  SubjectDetailSerializer()
    class_level = ClassLevelSerializer()
    # subject = serializers.StringRelatedField()
    # class_level = serializers.StringRelatedField()
    teacher = TeacherDetailSerializer() 
    class Meta:
        model = TeacherSubject
        fields = ['teacher', 'subject', 'class_level']
class TeacherSubjectDetailSerializer(serializers.ModelSerializer):
    subject =  SubjectDetailSerializer()
    class_level = ClassLevelListSerializer()
    teacher = TeacherDetailSerializer() 
    class Meta:
        model = TeacherSubject
        fields = ['teacher', 'subject', 'class_level']
        
class TeacherListSerializer(serializers.ModelSerializer):
    user = UserSerializer() 
    subjects = TeacherSubjectDetailSerializer(source='teachersubject_set', many=True, read_only=True)  

    class Meta:
        model = Teacher
        fields = ['id', 'user', 'staff_no', 'gender', 'subjects']