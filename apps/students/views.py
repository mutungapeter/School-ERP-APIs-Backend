from django.db import IntegrityError
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from apps.main.models import Subject, FormLevel,ClassLevel, Term
from apps.utils import DataPagination, assign_all_subjects, assign_core_subjects, assign_electives,retain_current_student_subjects
from apps.students.models import PromotionRecord,GraduationRecord, Student, StudentSubject
from apps.students.serializers import PromoteStudentsSerializer, GraduationRecordsSerializer, PromotionRecordsSerializer ,PromoteStudentsToAlumniSerializer, StudentListSerializer, StudentSerializer, StudentSubjectSerializer
from django.db import transaction

class StudentAPIView(APIView):
    renderer_classes = [JSONRenderer, BrowsableAPIRenderer]
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, pk=None):
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        admission_number = request.query_params.get('admission_number')
        class_level_id = request.query_params.get('class_level_id')
        page = request.query_params.get('page')
        page_size = request.query_params.get('page_size')
        
        if request.user.role not in ['Admin', 'Principal', 'Teacher']:
            return Response({"error": "You do not have permission to view  students records."}, status=status.HTTP_403_FORBIDDEN)
       
        # queryset = None
        queryset = Student.objects.filter(status='Active')
        if pk:
            try:
                
                student = Student.objects.filter(status='Active').get(pk=pk)
                serializer = StudentListSerializer(student)
                return Response(serializer.data)
            except Student.DoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND)
        
        
       
        if admission_number:
            if queryset is None:
                queryset = Student.objects.filter(admission_number=admission_number, status='Active' )
            else:
                queryset = Student.objects.filter(admission_number=admission_number)
            
        if class_level_id:
            if queryset is None:
                queryset = Student.objects.filter(class_level_id=class_level_id, status='Active' )
            else:
                queryset = queryset.filter(class_level_id=class_level_id)
              
        if not queryset.exists():
            if admission_number and class_level_id:
                return Response(
                    {"error": "No student found with that admission number and class level."},
                    status=status.HTTP_404_NOT_FOUND
                )
            if admission_number:
                return Response(
                    {"error": "No student found with that admission number."},
                    status=status.HTTP_404_NOT_FOUND
                )
            if class_level_id:
                return Response(
                    {"error": "No students found in this class."},
                    status=status.HTTP_404_NOT_FOUND
                )
        queryset = queryset.order_by('-created_at')
        if page or page_size:
            paginator = DataPagination()
            paginated_students = paginator.paginate_queryset(queryset, request)
            serializer = StudentListSerializer(paginated_students, many=True)
            return paginator.get_paginated_response(serializer.data)
        else:
            serializer = StudentListSerializer(queryset, many=True)
            return Response(serializer.data)
    def post(self, request):
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        
        if request.user.role not in ['Admin', 'Principal']:
            return Response({"error": "You do not have permission to create a student."}, status=status.HTTP_403_FORBIDDEN)

        serializer = StudentSerializer(data=request.data)
        if serializer.is_valid():
            student = serializer.save()
            form_level = student.class_level.form_level.level
            print("form_level:", form_level)
            print("student:", student)
            if form_level <= 2:
                assign_all_subjects(student)
            else:
                core_subjects = Subject.objects.filter(subject_type='Core')
                assign_core_subjects(student, core_subjects)
                electives = request.data.get('electives', [])
                if electives:
                    elective_subjects = Subject.objects.filter(id__in=electives, subject_type='Elective')
                    assign_electives(student, elective_subjects)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        
        if request.user.role not in ['Admin', 'Principal']:
            return Response({"error": "You do not have permission to create a student."}, status=status.HTTP_403_FORBIDDEN)
        try:
            student = Student.objects.get(pk=pk)
        except Student.DoesNotExist:
            return Response({"error": "Student not found."}, status=status.HTTP_404_NOT_FOUND)

        
        new_admission_number = request.data.get('admission_number')

        if new_admission_number and new_admission_number != student.admission_number and student.objects.filter(new_admission_number=new_admission_number).exists():
            return Response({"error": "A Student with this username admission number already exists."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = StudentSerializer(student, data=request.data, partial=True) 
        if serializer.is_valid():
            updated_student = serializer.save()  
            form_level = student.class_level.form_level.level
            if form_level <= 2:
                assign_all_subjects(student)
            else:
                core_subjects = Subject.objects.filter(subject_type='Core')
                assign_core_subjects(student, core_subjects)
            return Response({"message": "Student updated successfully", "teacher": serializer.data}, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        

    def delete(self, request, pk=None):
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        if request.user.role not in ['Admin', 'Principal']:
            return Response({"error": "You do not have permission to delete a student."}, status=status.HTTP_403_FORBIDDEN)

        try:
            student = Student.objects.get(pk=pk)
        except Student.DoesNotExist:
            return Response({"error": "Student not found."}, status=status.HTTP_404_NOT_FOUND)
        student.delete()

        return Response({"message": "Student deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
    
class FilterStudentsAPIView(APIView):
    permission_classes = [IsAuthenticated]  
    def get(self, request):
        admission_number = request.query_params.get('admission_number')
        subject_id = request.query_params.get('subject_id')
        class_level_id = request.query_params.get('class_level_id')
        user = request.user
        
        queryset = None
        student_exists = None
        if admission_number:
            student_exists = Student.objects.filter(admission_number=admission_number).first()
            if not student_exists:
                return Response(
                    {"error": f"Student with admission number {admission_number} not found."},
                    status=status.HTTP_404_NOT_FOUND
                )
        class_exists = None
        if class_level_id:
            class_exists = ClassLevel.objects.filter(id=class_level_id).first()
            if not class_exists:
                return Response(
                    {"error": "Class not found."},
                    status=status.HTTP_404_NOT_FOUND
                )
        student_subject_exists = None
        if subject_id:
            student_subject_exists = StudentSubject.objects.filter(id=subject_id).first()
            if not student_subject_exists:
                return Response(
                    {"error": f"Subject  not found."},
                    status=status.HTTP_404_NOT_FOUND
                )

        if admission_number and user.role in ['Admin', 'Principal']:
            if not student_exists:
                return Response(
                    {"error": f"Student with admission number {admission_number} does not exist."},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            queryset = StudentSubject.objects.filter(student=student_exists).select_related('student', 'subject')
            
            if subject_id and class_level_id:
                queryset = queryset.filter(
                    student__admission_number=admission_number,
                    subject_id=subject_id,
                    student__class_level_id=class_level_id
                )
            elif subject_id:
                queryset = StudentSubject.objects.filter(
                    student__admission_number=admission_number,
                    subject_id=subject_id
                )
            elif class_level_id:
                queryset = StudentSubject.objects.filter(
                    student__admission_number=admission_number,
                    student__class_level_id=class_level_id
                )
            student_with_subject_exists = queryset.exists()
            if not student_with_subject_exists:
                if admission_number and subject_id and class_level_id:
                    return Response({
                        "error": f"No student found with that admission number {admission_number} has no the given subject {student_subject_exists.subject.subject_name} in the selected class {class_exists.form_level.name}{f'({class_exists.stream.name})' if class_exists.stream else ''}. "}, status=status.HTTP_404_NOT_FOUND
                    )
                if admission_number and subject_id:
                    return Response({
                        "error": f"No student found with that admission number  {admission_number} has the given subject {student_subject_exists.subject.subject_name}."}, status=status.HTTP_404_NOT_FOUND
                    )
                if admission_number and class_level_id:
                    return Response({
                        "error": f"student with admission number  {admission_number} does not belong to  the selected class {class_exists.form_level.name}{f'({class_exists.stream.name})' if class_exists.stream else ''} ."}, status=status.HTTP_404_NOT_FOUND
                    )
                if admission_number:
                    return Response({
                                "error": f"No student found with that admission number {admission_number}.",
                            }, status=status.HTTP_404_NOT_FOUND
                            )

        elif admission_number and user.role not in ['Admin', 'Principal']:
            if not student_exists:
                return Response(
                    {"error": f"Student with admission number {admission_number} does not exist."},
                    status=status.HTTP_404_NOT_FOUND
                )
            if admission_number and not subject_id or not class_level_id:
                return Response(
                    {"error": "You must provide both subject and class when using admission_number.Unless You are Admin or the Principal"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            queryset = StudentSubject.objects.filter(
                student__admission_number=admission_number,
                subject_id=subject_id,
                student__class_level_id=class_level_id
            ).select_related('student', 'subject')
            if subject_id and class_level_id:
                    queryset = StudentSubject.objects.filter(
                    student__admission_number=admission_number,
                    subject_id=subject_id,
                    student__class_level_id=class_level_id
                )
            elif subject_id:
                queryset = StudentSubject.objects.filter(
                    student__admission_number=admission_number,
                    subject_id=subject_id
                )
            elif class_level_id:
                queryset = StudentSubject.objects.filter(
                    student__admission_number=admission_number,
                    student__class_level_id=class_level_id
                )
            student_with_subject_exists = queryset.exists()
            if not student_with_subject_exists:
                if admission_number:
                    return Response({
                        "error": f"No student found with that admission number {admission_number}.",
                    }, status=status.HTTP_404_NOT_FOUND
                    )
                if admission_number and subject_id and class_level_id:
                    return Response({
                        "error": f"No student found with that admission number {admission_number} has the given subject in the selected class {class_exists.form_level.name}{f'({class_exists.stream.name})' if class_exists.stream else ''}."}, status=status.HTTP_404_NOT_FOUND
                    )
                if admission_number and subject_id:
                    return Response({
                        "error": f"No student found with that admission number  {admission_number} has the given subject {student_subject_exists.subject.subject_name}."}, status=status.HTTP_404_NOT_FOUND
                    )
                

        elif subject_id and class_level_id:
            queryset = StudentSubject.objects.filter(
                subject_id=subject_id,
                student__class_level_id=class_level_id
            ).select_related('student', 'subject')
            students_exists = queryset.exists()
            if not students_exists:
                if subject_id and class_level_id:
                    return Response({
                        "error": f"No students found within that class {class_exists.form_level.name}{f'({class_exists.stream.name})' if class_exists.stream else ''} and subject {student_subject_exists.subject.subject_name}."},
                                    status=status.HTTP_404_NOT_FOUND
                                    )    

        else:
            return Response(
                {"error": "You must provide either admission_number or both subject and class."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = StudentSubjectSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class StudentSubjectAPIView(APIView):
    renderer_classes = [JSONRenderer, BrowsableAPIRenderer]
    serializer_class = StudentSubjectSerializer
    def get(self, request, pk=None, student_id=None):
        if pk:
            try:
                student_subject = StudentSubject.objects.get(pk=pk)
                serializer = StudentSubjectSerializer(student_subject)
                return Response(serializer.data)
            except StudentSubject.DoesNotExist:
                return Response({"error": "Subject not found in this student."}, status=status.HTTP_404_NOT_FOUND)
        
        elif student_id:
            try:
                student = Student.objects.get(pk=student_id)
            except Student.DoesNotExist:
                return Response({"error": "Student not found."}, status=status.HTTP_404_NOT_FOUND)

            student_subjects = StudentSubject.objects.filter(student=student)
            serializer = StudentSubjectSerializer(student_subjects, many=True)
            return Response(serializer.data)

        else:
            student_subjects = StudentSubject.objects.all()
            serializer = StudentSubjectSerializer(student_subjects, many=True)
            return Response(serializer.data)

    def post(self, request):
        serializer = StudentSubjectSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk=None, student_id=None):
        if pk:
            try:
                student_subject = StudentSubject.objects.get(pk=pk)
            except StudentSubject.DoesNotExist:
                return Response({"error": "StudentSubject not found."}, status=status.HTTP_404_NOT_FOUND)

            serializer = StudentSubjectSerializer(student_subject, data=request.data)
        elif student_id:
            try:
                student_subject = StudentSubject.objects.filter(student_id=student_id).first()
                if not student_subject:
                    return Response({"error": "No subjects found for this student."}, status=status.HTTP_404_NOT_FOUND)
            except StudentSubject.DoesNotExist:
                return Response({"error": "No subjects found."}, status=status.HTTP_404_NOT_FOUND)

            serializer = StudentSubjectSerializer(student_subject, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk=None, student_id=None):
      
        if pk:
            try:
                student_subject = StudentSubject.objects.get(pk=pk)
            except StudentSubject.DoesNotExist:
                return Response({"error": "StudentSubject not found."}, status=status.HTTP_404_NOT_FOUND)
            student_subject.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        
        elif student_id:
            try:
                student = Student.objects.get(pk=student_id)
            except Student.DoesNotExist:
                return Response({"error": "Student not found."}, status=status.HTTP_404_NOT_FOUND)

            student_subjects = StudentSubject.objects.filter(student=student)
            student_subjects.delete()
            return Response({"message": "All subjects for the student deleted successfully."}, status=status.HTTP_204_NO_CONTENT)

        return Response({"error": "StudentSubject or student_id is required."}, status=status.HTTP_400_BAD_REQUEST)


class PromoteStudentsAPIView(APIView):
    renderer_classes = [JSONRenderer, BrowsableAPIRenderer]
    serializer_class = PromoteStudentsSerializer
    def get(self, request, *args, **kwargs):
        source_form_level = request.query_params.get('source_form_level')
        year = request.query_params.get('year')
        
        if not source_form_level or not year:
            return Response({
                "error": "Please provide a form level and a year."
            }, status=400)

        queryset = None
        form_level = get_object_or_404(FormLevel, pk=source_form_level)
        queryset = PromotionRecord.objects.filter(
            source_class_level__form_level=source_form_level,
            year=year
        ).order_by('created_at')
        if not queryset.exists():
            return Response(
                {"message": f"No Promotion records found for {form_level.name}  for the year    {year}."},
                status=status.HTTP_404_NOT_FOUND
            )
        page = request.query_params.get('page')
        page_size = request.query_params.get('page_size')
            
        if page or page_size:
            paginator = DataPagination()
            paginated_records = paginator.paginate_queryset(queryset, request)
            serializer = PromotionRecordsSerializer(paginated_records, many=True)
            return paginator.get_paginated_response(serializer.data)
        else:
            serializer = PromotionRecordsSerializer(queryset, many=True)
            return Response(serializer.data)
       
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        data = request.data
        serializer = self.serializer_class(data=data)
        
        if serializer.is_valid(raise_exception=True):
            source_class_level = serializer.validated_data['source_class_level']
            target_class_level = serializer.validated_data['target_class_level']
            current_term_id = serializer.validated_data.get('current_term')
            students = Student.objects.filter(class_level=source_class_level)
            
            for student in students:
                student.current_term = Term.objects.get(id=current_term_id)  
                student.save()
                PromotionRecord.objects.create(
                    student=student,
                    source_class_level=source_class_level,
                    target_class_level=target_class_level,
                    year=serializer.validated_data['year']
                )
                
            student.class_level = target_class_level
            student.save()
            
            
            form_level = target_class_level.form_level.level
            if form_level <= 2:
                assign_all_subjects(student)
            elif form_level == 3:
                core_subjects = Subject.objects.filter(subject_type='Core')
                assign_core_subjects(student, core_subjects)
            elif form_level == 4:
                retain_current_student_subjects(student)
    
            return Response({"message": "Students successfully promoted"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class PromoteStudentsToAlumniAPIView(APIView):
    renderer_classes = [JSONRenderer, BrowsableAPIRenderer]
    serializer_class = PromoteStudentsToAlumniSerializer
    def get(self, request):
        year = request.query_params.get('graduation_year')
        user = request.user
        queryset = None
        

        if not year:
            return Response(
                {"error": "You must provide graduation year."},
                status=status.HTTP_400_BAD_REQUEST
            )

        
        queryset = GraduationRecord.objects.filter(
            graduation_year=year
        ).order_by('created_at','student__first_name', 'student__last_name')
        if not queryset.exists():
            return Response(
                {"message": f"No alumni records found for the year {year}."},
                status=status.HTTP_404_NOT_FOUND
            )
        page = request.query_params.get('page')
        page_size = request.query_params.get('page_size')
            
        if page or page_size:
            paginator = DataPagination()
            paginated_records = paginator.paginate_queryset(queryset, request)
            serializer = GraduationRecordsSerializer(paginated_records, many=True)
            return paginator.get_paginated_response(serializer.data)
        else:
            serializer = GraduationRecordsSerializer(queryset, many=True)
            return Response(serializer.data)
        

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        data = request.data
        serializer = self.serializer_class(data=data)
        
        if serializer.is_valid(raise_exception=True):
            final_class_level = serializer.validated_data['final_class_level']
            
            
            students = Student.objects.filter(class_level=final_class_level)
            
            for student in students:
                GraduationRecord.objects.create(
                    student=student,
                    final_class_level=final_class_level,
                    graduation_year=serializer.validated_data['graduation_year']
                )
                
            student.status = 'Graduated'
            student.class_level = None  
            student.save()
           
            return Response({"message": "Students successfully Completed school and promoted to Alumni."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
 
 
 
class AssignElectivesAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        if not request.user.is_authenticated:
            return Response({"error": "You must be authenticated to assign electives."}, status=status.HTTP_401_UNAUTHORIZED)
        
        if request.user.role not in ['Admin', 'Principal']:
            return Response({"error": "You do not have permission to assign electives."}, status=status.HTTP_403_FORBIDDEN)
        student_id = request.data.get('student_id')
        if not student_id:
            return Response({"error": "student_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            student = Student.objects.get(pk=student_id)
        except Student.DoesNotExist:
            return Response({"error": "Student not found."}, status=status.HTTP_404_NOT_FOUND)
        
        form_level = student.class_level.form_level.level
        if form_level not in [3, 4]:
            return Response({"error": f"Electives can only be assigned to students in form levels 3 or 4. Current form level: {form_level}"}, status=status.HTTP_400_BAD_REQUEST)
        
     
        electives = request.data.get('electives', [])
        if not electives:
            return Response({"error": "No electives were provided."}, status=status.HTTP_400_BAD_REQUEST)
        
        
        elective_subjects = Subject.objects.filter(id__in=electives, subject_type='Elective')
        
        if not elective_subjects.exists():
            return Response({"error": "No valid elective subjects found."}, status=status.HTTP_400_BAD_REQUEST)
        
        assign_electives(student, elective_subjects)
        
        return Response({"message": "Electives successfully assigned to the student."}, status=status.HTTP_200_OK)
    def put(self, request):
        if not request.user.is_authenticated:
            return Response({"error": "You must be authenticated to assign electives."}, status=status.HTTP_401_UNAUTHORIZED)

        if request.user.role not in ['Admin', 'Principal']:
            return Response({"error": "You do not have permission to assign electives."}, status=status.HTTP_403_FORBIDDEN)

        student_id = request.data.get('student_id')
        if not student_id:
            return Response({"error": "student_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            student = Student.objects.get(pk=student_id)
        except Student.DoesNotExist:
            return Response({"error": "Student not found."}, status=status.HTTP_404_NOT_FOUND)

        form_level = student.class_level.form_level.level
        if form_level not in [3, 4]:
            return Response({"error": f"Electives can only be assigned to students in form levels 3 or 4. Current form level: {form_level}"}, status=status.HTTP_400_BAD_REQUEST)

        electives = request.data.get('electives', [])
        if not electives:
            return Response({"error": "No electives were provided."}, status=status.HTTP_400_BAD_REQUEST)

        elective_subjects = Subject.objects.filter(id__in=electives, subject_type='Elective')

        if not elective_subjects.exists():
            return Response({"error": "No valid elective subjects found."}, status=status.HTTP_400_BAD_REQUEST)

        assign_electives(student, elective_subjects)

        return Response({"message": "Electives successfully updated for the student."}, status=status.HTTP_200_OK)