from django.db import IntegrityError
from django.shortcuts import get_object_or_404, render
from apps.users.serializers import UserListSerializer
from apps.users.utils.authentication import CustomAuthentication
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer

from apps.main.models import ClassLevel, Subject
from apps.users.models import User
from apps.teachers.models import Teacher, TeacherSubject
from apps.teachers.serializers import TeacherListSerializer, TeacherSerializer, TeacherSubjectCreateSerializer, TeacherSubjectSerializer
from apps.utils import DataPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication


class TeacherAPIView(APIView):
    renderer_classes = [JSONRenderer, BrowsableAPIRenderer]
    serializer_class = TeacherSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, pk=None):
        if not request.user.is_authenticated:
            return Response({"error": "Authentication credentials were not provided."}, status=status.HTTP_401_UNAUTHORIZED)

        staff_no = request.query_params.get('staff_no')
        teacher_id = request.query_params.get('id')

        if pk:
            try:
                teacher = Teacher.objects.get(pk=pk)
                serializer = TeacherListSerializer(teacher)
                return Response(serializer.data)
            except Teacher.DoesNotExist:
                return Response({"error": "Teacher not found. Teacher may not have been registered as a teacher."}, status=status.HTTP_404_NOT_FOUND)

        if request.user.role == 'Teacher':
            try:
                teacher = Teacher.objects.get(user=request.user)
                serializer = TeacherListSerializer(teacher)
                return Response(serializer.data)
            except Teacher.DoesNotExist:
                return Response({"error": "Teacher profile not found for the current user."}, status=status.HTTP_404_NOT_FOUND)
        if request.user.role in ['Admin', 'Principal']:
            if staff_no:
                teachers = Teacher.objects.filter(staff_no=staff_no)
            elif teacher_id:
                teachers = Teacher.objects.filter(id=teacher_id)
            else:
                teachers = Teacher.objects.all()
                
            teachers = teachers.order_by('-created_at')
            page = request.query_params.get('page')
            page_size = request.query_params.get('page_size')

            if page or page_size:
                paginator = DataPagination()
                paginated_teachers = paginator.paginate_queryset(
                    teachers, request)
                serializer = TeacherListSerializer(
                    paginated_teachers, many=True)
                return paginator.get_paginated_response(serializer.data)
            else:
                serializer = TeacherListSerializer(teachers, many=True)
                return Response(serializer.data)
    def post(self, request):
        
        if not request.user.is_authenticated:
            return Response({"error": "Authentication credentials were not provided."}, status=status.HTTP_401_UNAUTHORIZED)

        if request.user.role not in ['Admin', 'Principal']:
            return Response({"error": "You do not have permission to create a teacher."}, status=status.HTTP_403_FORBIDDEN)

        staff_no = request.data.get('staff_no')
        username = request.data.get('username')
        email = request.data.get("email")
        if Teacher.objects.filter(staff_no=staff_no).exists():
            return Response({"error": f"A teacher with staff number {staff_no} already exists."}, status=status.HTTP_400_BAD_REQUEST)
        
        if User.objects.filter(username=username).exists():
            return Response({"error": "A user with this username already exists."}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(email=email).exists():
            return Response({"error": "A user with this email already exists."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = TeacherSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def put(self, request, pk):
        
        if not request.user.is_authenticated:
            return Response({"error": "Authentication credentials were not provided."}, status=status.HTTP_401_UNAUTHORIZED)

        if request.user.role not in ['Admin', 'Principal']:
            return Response({"error": "You do not have permission to update a teacher."}, status=status.HTTP_403_FORBIDDEN)


        try:
            teacher = Teacher.objects.get(pk=pk)
        except Teacher.DoesNotExist:
            return Response({"error": "Teacher not found."}, status=status.HTTP_404_NOT_FOUND)

        new_username = request.data.get('username')
        new_email = request.data.get('email')
        new_staff_no = request.data.get('staff_no')

        if new_username and new_username != teacher.user.username and User.objects.filter(username=new_username).exists():
            return Response({"error": "A user with this username already exists."}, status=status.HTTP_400_BAD_REQUEST)

        if new_email and new_email != teacher.user.email and User.objects.filter(email=new_email).exists():
            return Response({"error": "A user with this email already exists."}, status=status.HTTP_400_BAD_REQUEST)

        if new_staff_no and new_staff_no != teacher.staff_no and Teacher.objects.filter(staff_no=new_staff_no).exists():
            return Response({"error": f"A teacher with staff number {new_staff_no} already exists."}, status=status.HTTP_400_BAD_REQUEST)

        
        serializer = TeacherSerializer(teacher, data=request.data, partial=True)  # Set partial=True to allow partial updates
        if serializer.is_valid():
            updated_teacher = serializer.save()  
            return Response({"message": "Teacher updated successfully", "teacher": serializer.data}, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

  
    def delete(self, request):
        if not request.user.is_authenticated:
                return Response(status=status.HTTP_401_UNAUTHORIZED)

            
        if request.user.role not in ['Admin', 'Principal']:
            return Response({"error": "You do not have permission to delete Teachers."}, status=status.HTTP_403_FORBIDDEN)
        print(request.data)
         
        teacher_ids = request.data if isinstance(request.data, list) else request.data.get('student_ids', [])
        # print("teacher_ids;", teacher_ids)

            
        if not teacher_ids:
            return Response({"error": "No teachers  provided."}, status=status.HTTP_400_BAD_REQUEST)

            
        teachers = Teacher.objects.filter(id__in=teacher_ids)
        teacher_count = teachers.count()
        if teacher_count == 0:
            return Response({"error": "Selected Teachers not found!."}, status=status.HTTP_404_NOT_FOUND)

        
        for teacher in teachers:
            teacher.user.delete()

        teachers.delete()

        return Response({"message": f"{teacher_count} Teachers deleted successfully."}, status=status.HTTP_200_OK)


class TeacherSubjectAPIView(APIView):
    renderer_classes = [JSONRenderer, BrowsableAPIRenderer]
    serializer_class = TeacherSubjectSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request):
        teacher_id = request.query_params.get('teacher_id') 
        staff_no = request.query_params.get('staff_no') 
        print(f"Received teacher_id: {teacher_id}")

        if teacher_id:
            try:
                teacher_subjects = TeacherSubject.objects.filter(teacher_id=teacher_id)
                serializer = TeacherSubjectSerializer(teacher_subjects, many=True) 
                return Response(serializer.data)
            except TeacherSubject.DoesNotExist:
                return Response({"error": "Teacher subjects not found."}, status=status.HTTP_404_NOT_FOUND)
    
        if request.user.role not in ['Admin', 'Principal']:
            return Response({"error": "You do not have permission to view teacher-subject relationships."}, status=status.HTTP_403_FORBIDDEN)

        teacher_subject_id = request.query_params.get('teacher_subject_id')

        if teacher_subject_id:
            try:
                teacher_subject = TeacherSubject.objects.get(id=teacher_subject_id)
                serializer = TeacherSubjectSerializer(teacher_subject)
                return Response(serializer.data)
            except TeacherSubject.DoesNotExist:
                return Response({"error": "TeacherSubject not found."}, status=status.HTTP_404_NOT_FOUND)

        teacher_subjects = TeacherSubject.objects.all()
        serializer = TeacherSubjectSerializer(teacher_subjects, many=True)
        return Response(serializer.data)

    def post(self, request):

        if request.user.role not in ['Admin', 'Principal']:
            return Response({"error": "You do not have permission to create teacher-subject relationships."}, status=status.HTTP_403_FORBIDDEN)

        data = request.data
        teacher_id = data.get('teacher')
        subject_id = data.get('subject')
        class_level_id = data.get('class_level')

        try:
            teacher = Teacher.objects.get(pk=teacher_id)
            subject = Subject.objects.get(pk=subject_id)
            class_level = ClassLevel.objects.get(pk=class_level_id)
        except Teacher.DoesNotExist:
            return Response({"error": "Teacher not found."}, status=status.HTTP_400_BAD_REQUEST)
        except Subject.DoesNotExist:
            return Response({"error": "Subject not found."}, status=status.HTTP_400_BAD_REQUEST)
        except ClassLevel.DoesNotExist:
            return Response({"error": "ClassLevel not found."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            teacher_subject = TeacherSubject.objects.create(
                teacher=teacher,
                subject=subject,
                class_level=class_level
            )
            serializer = TeacherSubjectSerializer(teacher_subject)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except IntegrityError:
            return Response({"error": "This relationship already exists."}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, pk):

        if request.user.role not in ['Admin', 'Principal']:
            return Response({"error": "You do not have permission to update teacher-subject relationships."}, status=status.HTTP_403_FORBIDDEN)

        data = request.data
        subject_id = data.get('subject')
        class_level_id = data.get('class_level')

        try:
            teacher_subject = TeacherSubject.objects.get(pk=pk)
            if subject_id:
                try:
                    subject = Subject.objects.get(pk=subject_id)
                    teacher_subject.subject = subject
                except Subject.DoesNotExist:
                    return Response({"error": "Subject not found."}, status=status.HTTP_400_BAD_REQUEST)

            if class_level_id:
                try:
                    class_level = ClassLevel.objects.get(pk=class_level_id)
                    teacher_subject.class_level = class_level
                except ClassLevel.DoesNotExist:
                    return Response({"error": "ClassLevel not found."}, status=status.HTTP_400_BAD_REQUEST)

            teacher_subject.save()
            serializer = TeacherSubjectSerializer(teacher_subject)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except TeacherSubject.DoesNotExist:
            return Response({"error": "TeacherSubject not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, pk):

        if request.user.role not in ['Admin', 'Principal']:
            return Response({"error": "You do not have permission to delete teacher-subject relationships."}, status=status.HTTP_403_FORBIDDEN)

        try:
            teacher_subject = TeacherSubject.objects.get(pk=pk)
            teacher_subject.delete()
            return Response({"message": "TeacherSubject successfully deleted."}, status=status.HTTP_204_NO_CONTENT)
        except TeacherSubject.DoesNotExist:
            return Response({"error": "TeacherSubject not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AssignTeacherView(APIView):
    def post(self, request):
        data = request.data

        teacher_id = data.get('teacher')
        teacher = Teacher.objects.get(id=teacher_id)

        subjects = data.get('subjects', [])
        if not subjects:
            return Response({"error": "You must select  a subject and a class or classes "}, status=status.HTTP_400_BAD_REQUEST)

        for subject_data in subjects:
            subject_id = subject_data.get('subject')
            class_ids = subject_data.get('classes', [])

            if not subject_id or not class_ids:
                return Response({"error": f"Subject  must have at least one class selected."}, status=status.HTTP_400_BAD_REQUEST)

            subject_instance = Subject.objects.get(id=subject_id)

            for class_id in class_ids:

                try:
                    class_instance = ClassLevel.objects.get(id=class_id)
                except ClassLevel.DoesNotExist:
                    return Response({"error": f"Class with ID {class_id} not found."}, status=status.HTTP_404_NOT_FOUND)

                if TeacherSubject.objects.filter(teacher=teacher, subject=subject_instance, class_level=class_instance).exists():
                    stream_name = class_instance.stream.name if class_instance.stream else ""
                    return Response({
                        "error": f"Failed to assign subject and class because this Teacher is already assigned to {subject_instance.subject_name} in {class_instance.form_level.name} {stream_name}."
                    }, status=status.HTTP_400_BAD_REQUEST)

                serializer = TeacherSubjectCreateSerializer(data={
                    'teacher': teacher.id,
                    'subject': subject_instance.id,
                    'class_level': class_instance.id
                })

                if serializer.is_valid():
                    serializer.save()
                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response({"message": "Subjects and classes assigned successfully"}, status=status.HTTP_200_OK)

    def put(self, request):
        data = request.data
    
        teacher_id = data.get('teacher')
        
        try:
            teacher = Teacher.objects.get(id=teacher_id)
        except Teacher.DoesNotExist:
            return Response({"error": "Teacher not found."}, status=status.HTTP_404_NOT_FOUND)

        subjects = data.get('subjects', [])
        if not subjects:
            current_assignments = TeacherSubject.objects.filter(teacher=teacher)
            current_assignments.delete() 
            return Response({"message": "All subjects unassigned successfully"}, status=status.HTTP_200_OK)

     
        new_assignments = []

        for subject_data in subjects:
            subject_id = subject_data.get('subject')
            class_ids = subject_data.get('classes', [])

            if not subject_id or not class_ids:
                return Response({"error": f"Subject must have at least one class selected."}, status=status.HTTP_400_BAD_REQUEST)

            subject_instance = Subject.objects.get(id=subject_id)

            for class_id in class_ids:
                try:
                    class_instance = ClassLevel.objects.get(id=class_id)
                except ClassLevel.DoesNotExist:
                    return Response({"error": f"Class with ID {class_id} not found."}, status=status.HTTP_404_NOT_FOUND)

                
                new_assignments.append({
                    'teacher': teacher,
                    'subject': subject_instance,
                    'class_level': class_instance
                })

        
        current_assignments = TeacherSubject.objects.filter(teacher=teacher)

       
        for assignment in current_assignments:
            if not any((
                assignment.subject.id == new_assignment['subject'].id and
                assignment.class_level.id == new_assignment['class_level'].id
            ) for new_assignment in new_assignments):
                assignment.delete()

       
        for new_assignment in new_assignments:
            if not TeacherSubject.objects.filter(
                teacher=new_assignment['teacher'],
                subject=new_assignment['subject'],
                class_level=new_assignment['class_level']
            ).exists():
                serializer = TeacherSubjectCreateSerializer(data={
                    'teacher': new_assignment['teacher'].id,
                    'subject': new_assignment['subject'].id,
                    'class_level': new_assignment['class_level'].id
                })

                if serializer.is_valid():
                    serializer.save()
                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response({"message": "Subjects and classes updated successfully"}, status=status.HTTP_200_OK)
