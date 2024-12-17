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
from apps.students.serializers import GraduationRecordSerializer, PromoteStudentsSerializer, GraduationRecordsSerializer, PromotionRecordSerializer, PromotionRecordsSerializer ,PromoteStudentsToAlumniSerializer, StudentListSerializer, StudentSerializer, StudentSubjectSerializer
from django.db import transaction
import pandas as pd
from rest_framework.parsers import MultiPartParser

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
        class_level_id = request.query_params.get('class_level_id')
        
        if request.user.role not in ['Admin', 'Principal', 'Teacher']:
            return Response({"error": "You do not have permission to view  students records."}, status=status.HTTP_403_FORBIDDEN)
       
        queryset = Student.objects.filter(status='Active')
        if pk:
            try:
                
                student = Student.objects.filter(status='Active').get(pk=pk)
                current_class_level = student.class_level
                if class_level_id:
                    class_level_filter = ClassLevel.objects.get(id=class_level_id)
                    student_subjects = StudentSubject.objects.filter(student=student, class_level=class_level_filter)
                    if not student_subjects.exists():
                        return Response(
                            {"error": "The student has no subjects registered for the given selected class!."},
                            status=status.HTTP_404_NOT_FOUND,
                        )
                else:
                    student_subjects = StudentSubject.objects.filter(student=student, class_level=current_class_level)
                # student_subjects = StudentSubject.objects.filter(student=student, class_level=current_class_level)
                
                student_data = StudentListSerializer(student).data
                student_data['subjects'] = StudentSubjectSerializer(student_subjects, many=True).data

                return Response(student_data)
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
        data = request.data

        class_level_id = data.get('class_level')
        admission_type = data.get('admission_type')
        admission_number = data.get('admission_number')

        if not  admission_type:
            return Response(
                {"error": "admission_type are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            class_level = ClassLevel.objects.get(id=class_level_id)
        except ClassLevel.DoesNotExist:
            return Response({"error": "Class level does not exist."}, status=status.HTTP_404_NOT_FOUND)

        current_term = None
        
        class_level = ClassLevel.objects.filter(id=class_level_id).first()
        if not class_level:
                    return Response(
                        {"error": f"Class level '{class_level_id}' does not exist."},
                        status=status.HTTP_404_NOT_FOUND
                    )
        current_term = Term.objects.filter(
                    class_level=class_level,
                    status="Active"
                    ).order_by("start_date").first()
        if not current_term:
                    return Response(
                        {"error": "No active term  for the class level. Student should be admitted to a class level with an active Term , check your term dates."},
                        status=status.HTTP_404_NOT_FOUND
                    )
        if Student.objects.filter(admission_number=admission_number).exists():
            return Response(
                {
                "error": "Student with Admission number already exists"
            },
            status=status.HTTP_400_BAD_REQUEST
            )
        data['current_term'] = current_term.id
        serializer = StudentSerializer(data=data)
        if serializer.is_valid():
            student = serializer.save()
            form_level = student.class_level.form_level.level
            print("form_level:", form_level)
            print("student:", student)
            if form_level <= 2:
                assign_all_subjects(student)
            elif form_level == 3:
                core_subjects = Subject.objects.filter(subject_type='Core')
                print(f"Form level {form_level}: Core subjects found: {core_subjects}")
                assign_core_subjects(student, core_subjects)
            elif form_level == 4:
                print(f"Form level {form_level}: Retaining current subjects")
                retain_current_student_subjects(student)
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
        

   
    def delete(self, request):
        if not request.user.is_authenticated:
                return Response(status=status.HTTP_401_UNAUTHORIZED)

            
        if request.user.role not in ['Admin', 'Principal']:
            return Response({"error": "You do not have permission to delete students."}, status=status.HTTP_403_FORBIDDEN)
        print(request.data)
         
        student_ids = request.data if isinstance(request.data, list) else request.data.get('student_ids', [])
        print("student_ids;", student_ids)

            
        if not student_ids:
            return Response({"error": "No student IDs provided."}, status=status.HTTP_400_BAD_REQUEST)

            
        students = Student.objects.filter(id__in=student_ids)
        student_count = students.count()
        if student_count == 0:
            return Response({"error": "No students found with the provided IDs."}, status=status.HTTP_404_NOT_FOUND)

        # Delete the students
        students.delete()

        return Response({"message": f"{student_count} students deleted successfully."}, status=status.HTTP_200_OK)

class UploadStudentsAPIView(APIView):
    renderer_classes = [JSONRenderer, BrowsableAPIRenderer]
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]

    def post(self, request):
        user_role = request.user.role


        if user_role not in ['Admin', 'Principal']:
            return Response(
                {"error": "You do not have permission to upload students."},
                status=status.HTTP_403_FORBIDDEN
            )

        
        
       
       
        data = request.data
        class_level_id = data.get('class_level')
        admission_type = data.get('admission_type')

        if not  admission_type:
            return Response(
                {"error": "admission_type are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            class_level = ClassLevel.objects.get(id=class_level_id)
        except ClassLevel.DoesNotExist:
            return Response({"error": "Class level does not exist."}, status=status.HTTP_404_NOT_FOUND)

        current_term = None
        
        class_level = ClassLevel.objects.filter(id=class_level_id).first()
        if not class_level:
                    return Response(
                        {"error": f"Class level '{class_level_id}' does not exist."},
                        status=status.HTTP_404_NOT_FOUND
                    )
        current_term = Term.objects.filter(
                    class_level=class_level,
                    status="Active"
                    ).order_by("start_date").first()
        if not current_term:
                    return Response(
                        {"error": "No active term  for the class level.Students should be admitted to a class level with an active Term , check your term dates."},
                        status=status.HTTP_404_NOT_FOUND
                    )
        
        students_file = request.FILES.get('students_file')
        if not students_file:
            return Response({"error": "No file uploaded."}, status=status.HTTP_400_BAD_REQUEST)

        errors = []
        successes = []

        try:
            
            file_extension = students_file.name.split('.')[-1].lower()
            if file_extension == 'csv':
                df = pd.read_csv(students_file)
            elif file_extension in ['xls', 'xlsx']:
                df = pd.read_excel(students_file)
            else:
                return Response(
                    {"error": "Invalid file type. Only CSV and Excel are supported."},
                    status=status.HTTP_400_BAD_REQUEST
                )

          
            required_columns = {'first_name', 'last_name', 'gender', 'admission_number', 'kcpe_marks'}
            missing_columns = required_columns - set(df.columns)
            if missing_columns:
                return Response(
                    {"error": f"The following required columns are missing: {', '.join(missing_columns)}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            
            for index, row in df.iterrows():
                try:
                    first_name = row.get('first_name')
                    last_name = row.get('last_name')
                    gender = row.get('gender')
                    admission_number = row.get('admission_number')
                    kcpe_marks = row.get('kcpe_marks')

                   
                    if pd.isnull(first_name) or pd.isnull(last_name) or pd.isnull(gender) or pd.isnull(admission_number) or pd.isnull(kcpe_marks):
                        errors.append(f"Missing data in row {index + 1}.")
                        continue

                    
                    if Student.objects.filter(admission_number=admission_number).exists():
                        errors.append(f"Student with admission number {admission_number} already exists.")
                        continue

                   
                    form_level = class_level.form_level.level

                   
                    student = Student.objects.create(
                        admission_number=admission_number,
                        first_name=first_name,
                        last_name=last_name,
                        gender=gender,
                        kcpe_marks=kcpe_marks,
                        class_level=class_level,
                        current_term=current_term,
                        admission_type=admission_type,
                        
                    )

                    if form_level <= 2:
                        assign_all_subjects(student)
                    else:
                        core_subjects = Subject.objects.filter(subject_type='Core')
                        assign_core_subjects(student, core_subjects)

                    successes.append(f"Student {first_name} {last_name} (Admission: {admission_number}) uploaded successfully.")

                except Exception as e:
                    errors.append(f"Error processing student {first_name} {last_name} (Admission: {admission_number}): {str(e)}")

            # Prepare response
            response_data = {}
            if successes:
                response_data["message"] = "Some students were uploaded successfully."
                response_data["successes"] = successes
            if errors:
                response_data["errors"] = errors

            status_code = status.HTTP_207_MULTI_STATUS if successes and errors else (
                status.HTTP_201_CREATED if successes else status.HTTP_400_BAD_REQUEST
            )
            return Response(response_data, status=status_code)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

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
                        "error": f"Student  with that admission number {admission_number} has no the given subject {student_subject_exists.subject.subject_name} in the selected class {class_exists.form_level.name}{f'({class_exists.stream.name})' if class_exists.stream else ''}. "}, status=status.HTTP_404_NOT_FOUND
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
        print("data", data)
        current_active_term = None
        calendar_year =  None
        source_class_level_id = data.get('source_class_level')
        target_class_level_id = data.get('target_class_level')
        

            
       
        try:
            target_class_level = ClassLevel.objects.get(id=target_class_level_id)
        except ClassLevel.DoesNotExist:
            return Response(
                    {"error": "Class level does not exist."},
                    status=status.HTTP_404_NOT_FOUND
                )
        try:
            source_class_level = ClassLevel.objects.get(id=source_class_level_id)
        except ClassLevel.DoesNotExist:
            return Response(
                    {"error": "Class level does not exist."},
                    status=status.HTTP_404_NOT_FOUND
                )
       
        
        current_active_term = Term.objects.filter(
                    class_level=target_class_level,
                    status="Active"
                    ).order_by("start_date").first()
        if not current_active_term:
                    return Response(
                        {"error": "No active term exists for the class level."},
                        status=status.HTTP_404_NOT_FOUND
                    )
        calendar_year = target_class_level.calendar_year
        students = Student.objects.filter(class_level=source_class_level_id)
        print("classLevel---->", source_class_level)
        promotion_records = []
        for student in students:
            student_data = {
                    "student": student.id,
                    "source_class_level": source_class_level_id,
                    "target_class_level": target_class_level_id,
                    "year": calendar_year,
                }

        # for student in students:
        #         PromotionRecord.objects.create(
        #             student=student,
        #             source_class_level=source_class_level,
        #             target_class_level=target_class_level,
        #             year=calendar_year
        #         )
          
        serializer = PromotionRecordSerializer(data=student_data)
        if serializer.is_valid():
            promotion_records.append(
                PromotionRecord(
                    student=student,
                    source_class_level_id=source_class_level_id,
                    target_class_level_id=target_class_level_id,
                    year=calendar_year,
                )
            )
        else:
            return Response(
                {"error": serializer.errors, "student_id": student.id},
                status=status.HTTP_400_BAD_REQUEST,
            )

    #    Bulk create promotion records
        PromotionRecord.objects.bulk_create(promotion_records)

        
        for student in students:
                student.class_level = target_class_level
                student.current_term = current_active_term
                student.save()

                form_level = target_class_level.form_level.level
                print("form_level", form_level)
                if form_level <= 2:
                    assign_all_subjects(student)
                elif form_level == 3:
                    core_subjects = Subject.objects.filter(subject_type='Core')
                    assign_core_subjects(student, core_subjects)
                elif form_level == 4:
                    retain_current_student_subjects(student)
    
        return Response({"message": "Students successfully promoted"}, status=status.HTTP_201_CREATED)
        # return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
       
    # @transaction.atomic
    # def post(self, request, *args, **kwargs):
    #     data = request.data
    #     print("data", data)
    #     serializer = self.serializer_class(data=data)
        
    #     if serializer.is_valid(raise_exception=True):
    #         source_class_level = serializer.validated_data['source_class_level']
    #         terms_data = serializer.validated_data.get('terms', [])
            
    #         next_calendar_year = data.get('next_calendar_year')
    #         target_form_level = data.get('target_form_level')
    #         terms_data = data.get('terms', [])
    #         stream = source_class_level.stream

    #         target_form_level_instance = FormLevel.objects.get(id=target_form_level)
    #         print("target_form_level_instance", target_form_level_instance)
    #         target_class_level, created = ClassLevel.objects.get_or_create(
    #                 form_level=target_form_level_instance,
    #                 stream=stream,
    #                 calendar_year=next_calendar_year
    #             )
    #         created_terms = []
    #         for term_data in terms_data:
    #             term = Term.objects.create(
    #                 term=term_data["term"],
    #                 start_date=term_data["start_date"],
    #                 end_date=term_data["end_date"],
    #                 status="Active",  
    #                 class_level=target_class_level, 
    #             )
    #             created_terms.append(term)
                
    #         term_1 = None
    #         for term in created_terms:
    #             if term.term == "Term 1":
    #                 term_1 = term
    #                 break
    #         students = Student.objects.filter(class_level=source_class_level)
          
    #         for student in students:
    #             PromotionRecord.objects.create(
    #                 student=student,
    #                 source_class_level=source_class_level,
    #                 target_class_level=target_class_level,
    #                 year=next_calendar_year
    #             )
          
           
    #         for student in students:
    #             student.class_level = target_class_level
    #             student.current_term = term_1
    #             student.save()

    #             form_level = target_form_level_instance.level
    #             print("form_level", form_level)
    #             if form_level <= 2:
    #                 assign_all_subjects(student)
    #             elif form_level == 3:
    #                 core_subjects = Subject.objects.filter(subject_type='Core')
    #                 assign_core_subjects(student, core_subjects)
    #             elif form_level == 4:
    #                 retain_current_student_subjects(student)
    
    #         return Response({"message": "Students successfully promoted"}, status=status.HTTP_201_CREATED)
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
  
class PromoteStudentsToNextTermAPIView(APIView):
    renderer_classes = [JSONRenderer, BrowsableAPIRenderer]
    def post(self, request):
        class_level_id = request.data.get("class_level")
        term_id = request.data.get("term")

        if not class_level_id or not term_id:
            return Response(
                {"error": "Both 'class' and 'term' are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            class_level = ClassLevel.objects.get(id=class_level_id)
            next_term = Term.objects.get(id=term_id, status="Upcoming")
        except ClassLevel.DoesNotExist:
            return Response(
                {"error": "The specified class level does not exist."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Term.DoesNotExist:
            return Response(
                {"error": "The specified term does not exist or is not 'Upcoming'."},
                status=status.HTTP_404_NOT_FOUND,
            )
        students = Student.objects.filter(class_level=class_level, status="Active")
        if not students.exists():
            return Response(
                {"message": "No active students found in the specified class level."},
                status=status.HTTP_200_OK,
            )

        students.update(current_term=next_term)

        return Response(
            {
                "message": f"Successfully promoted {students.count()} students in class level {class_level} to term {next_term}.",
            },
            status=status.HTTP_200_OK,
        )

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
        final_class_level_id = data.get('final_class_level')  
        if not final_class_level_id:
                return Response(
                    {"error": "final_class_level is required."},
                    status=status.HTTP_400_BAD_REQUEST
                )

          
        try:
            final_class_level = ClassLevel.objects.get(id=final_class_level_id)
        except ClassLevel.DoesNotExist:
            return Response(
                    {"error": "Class level does not exist."},
                    status=status.HTTP_404_NOT_FOUND
                )

           
        graduation_year = final_class_level.calendar_year
        if not graduation_year:
                return Response(
                    {"error": "Calendar year for the class level is not set."},
                    status=status.HTTP_400_BAD_REQUEST
                )

         
        students = Student.objects.filter(class_level=final_class_level_id)
        if not students.exists():
                return Response(
                    {"error": "No students found for the given class level."},
                    status=status.HTTP_404_NOT_FOUND
                )


        serialized_data = []
        graduation_records = []
        for student in students:
                
                student_data = {
                    "student": student.id,
                    "final_class_level": final_class_level_id,
                    "graduation_year": graduation_year
                }

        serializer = GraduationRecordSerializer(data=student_data)
        if serializer.is_valid():
                    graduation_records.append(
                        GraduationRecord(
                        student=student,
                        final_class_level=final_class_level,
                        graduation_year=graduation_year
                        )
                    )
        else:
                   
                    return Response(
                        {"error": serializer.errors, "student_id": student.id},
                        status=status.HTTP_400_BAD_REQUEST
                    )

        GraduationRecord.objects.bulk_create(graduation_records)
        for student in students:
                student.status = 'Graduated'
                student.class_level = None  
                student.save()

        return Response(
                {
                    "message": "Students successfully completed school and promoted to Alumni.",
                    "graduation_records": serialized_data
                },
                status=status.HTTP_201_CREATED
            )
 
 
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