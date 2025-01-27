from django.db import IntegrityError
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.shortcuts import get_object_or_404

from apps.students.serializers import StudentReportSerializer
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer
from rest_framework.permissions import IsAuthenticated
from apps.utils import DataPagination
from apps.exams.models import MarksData
from apps.exams.serializers import MarkListSerializer,MarkSerializer, ReportMarkListSerializer
from apps.students.models import Student, StudentSubject
from apps.main.models import Subject, ClassLevel,MeanGradeConfig
from apps.main.models import Term
import pandas as pd
from rest_framework.parsers import MultiPartParser
from django.core.exceptions import ValidationError
from apps.teachers.models import Teacher
class MarksAPIView(APIView):
    renderer_classes = [JSONRenderer, BrowsableAPIRenderer]
    serializer_class = MarkListSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, pk=None):
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        
        if request.user.role not in ['Admin', 'Principal']:
            return Response({"error": "You do not have permission to view  marks records."}, status=status.HTTP_403_FORBIDDEN)

        if pk:
            try:
                marks = MarksData.objects.get(pk=pk)
                serializer = MarkListSerializer(marks)
                return Response(serializer.data)
            except MarksData.DoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND)
        else:
            marks = MarksData.objects.all()
            
            page = request.query_params.get('page')
            page_size = request.query_params.get('page_size')
            
            if page or page_size:
                paginator = DataPagination()
                paginated_marks = paginator.paginate_queryset(marks, request)
                serializer = MarkListSerializer(paginated_marks, many=True)
                return paginator.get_paginated_response(serializer.data)
            else:
                serializer = MarkListSerializer(marks, many=True)
                return Response(serializer.data)
    
    def post(self, request):
        serializer = MarkSerializer(data=request.data)
        student_subject_id = request.data.get('student_subject')
        term_id = request.data.get('term')
        student = request.data.get('student')
        student_subject = request.data.get('student_subject')
       
        if not StudentSubject.objects.filter(pk=student_subject_id).exists():
            return Response(
                {"error": "The selected student subject does not exist."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        
        if MarksData.objects.filter(student=student, student_subject=student_subject, term=term_id).exists():
            return Response(
                {"error": "This student already has marks recorded for the selected subject."},
                status=status.HTTP_400_BAD_REQUEST
            )
        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "Marks recorded successfully!",
                "data": serializer.data
                }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    def put(self, request, pk):
        try:
            marksData = MarksData.objects.get(pk=pk)
            
            # markData_Exists = MarksData.objects.filter(pk=pk).exclude(pk=pk).first()
            # if markData_Exists:
            #     return Response({"error": "Marks record for this  Subject and student already  already exists."},
            #             status=status.HTTP_400_BAD_REQUEST)
            serializer = MarkSerializer(marksData, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response( {
                        "message": "Mark record updated successfully",
                        "data": serializer.data  
                    },
                    status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except MarksData.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
    
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

   
    def delete(self, request):
        if not request.user.is_authenticated:
                return Response(status=status.HTTP_401_UNAUTHORIZED)

            
        if request.user.role not in ['Admin', 'Principal']:
            return Response({"error": "You do not have permission to delete Marks records."}, status=status.HTTP_403_FORBIDDEN)
        print(request.data)
         
        marks_ids = request.data if isinstance(request.data, list) else request.data.get('marks_ids', [])
        print("marks_ids;", marks_ids)

            
        if not marks_ids:
            return Response({"error": "No Marks provided for deletion."}, status=status.HTTP_400_BAD_REQUEST)

            
        marks_list = MarksData.objects.filter(id__in=marks_ids)
        marks_count = marks_list.count()
        if marks_count == 0:
            return Response({"error": "No Marks records found or may have been deleted."}, status=status.HTTP_404_NOT_FOUND)

        
        marks_list.delete()

        return Response({"message": f"{marks_count} marks records deleted successfully."}, status=status.HTTP_200_OK)


class UploadMarksAPIView(APIView):
    renderer_classes = [JSONRenderer, BrowsableAPIRenderer]
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]

    def post(self, request):
        class_level_id = request.data.get('class_level')
        term_id = request.data.get('term')  
        exam_type = request.data.get('exam_type')  
        user_role = request.user.role
       
        if user_role in ['Admin', 'Principal']:
            try:
                class_level = ClassLevel.objects.get(id=class_level_id)
            except ClassLevel.DoesNotExist:
                return Response({"error": "Class level does not exist."}, status=status.HTTP_404_NOT_FOUND)
            try:
                term = Term.objects.get(id=term_id)
            except Term.DoesNotExist:
                return Response({"error": "Term does not exist."}, status=status.HTTP_404_NOT_FOUND)
        else:
            teacher = Teacher.objects.get(user=request.user)
            if not ClassLevel.objects.filter(id=class_level_id, teachersubject__teacher=teacher).exists():
                return Response(
                    {"error": "You are not authorized to upload marks for this class level."},
                    status=status.HTTP_403_FORBIDDEN
                )
            class_level = ClassLevel.objects.get(id=class_level_id)
            
            try:
                term = Term.objects.get(id=term_id)
            except Term.DoesNotExist:
                return Response({"error": "Term does not exist."}, status=status.HTTP_404_NOT_FOUND)
                

        marks_file = request.FILES.get('marks_file')
        if not marks_file:
            return Response({"error": "No file uploaded."}, status=status.HTTP_400_BAD_REQUEST)
        
        errors = []
        successes = []
        try:
            file_extension = marks_file.name.split('.')[-1].lower()
            if file_extension == 'csv':
                df = pd.read_csv(marks_file)
            elif file_extension in ['xls', 'xlsx']:
                df = pd.read_excel(marks_file)
            else:
                return Response({"error": "Invalid file type. Only CSV and Excel are supported."}, status=status.HTTP_400_BAD_REQUEST)

            required_columns = {'admission_number', 'subject_name', 'total_score'}
            missing_columns = required_columns - set(df.columns)

            if missing_columns:
                return Response(
                    {"error": f"The following required columns are missing: {', '.join(missing_columns)}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            for index, row in df.iterrows():
                admission_number = row.get('admission_number')
                subject_name = row.get('subject_name')
                total_score = row.get('total_score')
                # cat_mark = row.get('cat_mark')
                # exam_mark = row.get('exam_mark')
                missing_fields = []

                if pd.isnull(admission_number):
                    missing_fields.append("admission_number")
                if pd.isnull(subject_name):
                    missing_fields.append("subject_name")
                if pd.isnull(total_score):
                    missing_fields.append("total_score")
                
                if missing_fields:
                    errors.append(
                        f"Missing data for fields {', '.join(missing_fields)} in row {row.to_dict()}."
                    )
                    continue
                
                try:
                    student = Student.objects.get(admission_number=admission_number)
                except Student.DoesNotExist:
                    errors.append(f"Student with admission number {admission_number} does not exist.")
                    continue
                
                
                if student.class_level is None or student.class_level != class_level:
                    # print("class->",class_level)
                    errors.append(f"Student with admission number {admission_number} is not currently enrolled in the specified class. "
                                f"Class Level: {class_level}")
                    continue
                if student.current_term is None or student.current_term != term:
                    # print("class->",term)
                    errors.append(f"Student with admission number {admission_number} is not currently enrolled in the specified"
                                f"Term: {term}")
                    continue
                
                try:
                    student_subject = StudentSubject.objects.get(
                        student=student,
                        subject__subject_name=subject_name,
                        class_level=class_level
                        )
                except StudentSubject.DoesNotExist:
                    errors.append(f"Subject {subject_name} not found for student {admission_number}.")
                    continue


                if MarksData.objects.filter(student=student, student_subject=student_subject, term_id=term_id, exam_type=exam_type).exists():
                    errors.append(f"Marks already recorded for student {admission_number} in term {term_id} for subject {subject_name}.")
                    continue


             
               
                MarksData.objects.create(
                    student=student,
                    student_subject=student_subject,
                    term_id=term_id,
                    total_score=total_score,
                    exam_type=exam_type
                )
                successes.append(f"Marks uploaded for student {admission_number} in subject {subject_name}.")
            response_data = {}
            if successes:
                response_data["message"] = "Some marks were uploaded successfully."
                response_data["successes"] = successes
            if errors:
                response_data["errors"] = errors

            status_code = status.HTTP_207_MULTI_STATUS if successes and errors else (
                status.HTTP_201_CREATED if successes else status.HTTP_400_BAD_REQUEST
            )
            return Response(response_data, status=status_code)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class FilterMarksDataView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        term_id = request.query_params.get('term')
        subject_id = request.query_params.get('subject')
        class_level_id = request.query_params.get('class_level')
        admission_number = request.query_params.get('admission_number')
        exam_type = request.query_params.get('exam_type')
        if not term_id:
            return Response(
                {"error": "Term is required for filtering."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        
        term = Term.objects.filter(id=term_id).first()
        if not term:
            return Response({"error": "Term not found."}, status=status.HTTP_404_NOT_FOUND)

        
        queryset = None

        
        if admission_number:
            student = Student.objects.filter(admission_number=admission_number).first()
            if not student:
                return Response(
                    {"error": f"Student with admission number {admission_number} not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )
            queryset = MarksData.objects.filter(student=student, term=term, exam_type=exam_type).select_related(
                "student", "student_subject__subject", "student_subject__class_level", "term"
            )

       
        if class_level_id:
            class_level = ClassLevel.objects.filter(id=class_level_id).first()
            if not class_level:
                return Response(
                    {"error": f"Class level with ID {class_level_id} not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )
            if queryset is None:
                queryset = MarksData.objects.filter(term=term, student_subject__class_level=class_level, exam_type=exam_type).select_related(
                    "student", "student_subject__subject", "student_subject__class_level", "term"
                )
            else:
                queryset = queryset.filter(student_subject__class_level=class_level)

        
        if subject_id:
            subject = Subject.objects.filter(id=subject_id).first()
            if not subject:
                return Response(
                    {"error": f"Subject with ID {subject_id} not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )
            if queryset is None:
                queryset = MarksData.objects.filter(term=term, student_subject__subject=subject, exam_type=exam_type).select_related(
                    "student", "student_subject__subject", "student_subject__class_level", "term"
                )
            else:
                queryset = queryset.filter(student_subject__subject=subject)

        
        if queryset is None or not queryset.exists():
            return Response(
                {"error": "No matching records found with the provided criteria."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = MarkListSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class ReportFormAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        user = request.user
        admission_number = request.query_params.get('admission_number')
        class_level_id = request.query_params.get('class_level')
        term_id = request.query_params.get("term")
        exam_type = request.query_params.get('exam_type')
        
        if (admission_number or class_level_id) and not term_id:
            return Response(
                {"error": "You must provide a term when using admission number or class."},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            if class_level_id is not None:
                class_level_id = int(class_level_id)
            else:
                print("Debug: class_level_id is None.")
        except ValueError:
            print("Debug: class_level_id is not integer.")

       
        students_data = []
        if (admission_number or class_level_id or term_id) and not exam_type:
            return Response(
                {"error": "Exam type is needed in order to generate the report forms."},
                status=status.HTTP_400_BAD_REQUEST
            )
        if not admission_number and not class_level_id:
            return Response(
                {"error": "Please provide either an admission number and term or a class level and term to retrieve report data."},
                status=status.HTTP_400_BAD_REQUEST
            )
        student = None
        if admission_number:
            student = Student.objects.filter(admission_number=admission_number).exists()
            if not student:
                return Response(
                        {"error": f"No student found with admission number {admission_number}."},
                        status=status.HTTP_404_NOT_FOUND
                )
        
        term = None
        if term_id:
            term = Term.objects.get(id=term_id)
            if not term:
                return Response(
                    {"error": f"Term not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
        class_level = None
        if class_level_id:
            class_level = ClassLevel.objects.filter(id=class_level_id).exists()
            if not class_level:
                    return Response(
                        {"error": f"Class Not Found."},
                        status=status.HTTP_404_NOT_FOUND
                    ) 
            
        if admission_number and term_id:
            if user.role not in ['Admin', 'Principal', 'Teacher']:
                return Response(
                    {"error": "You have no permission to generate students report forms."},
                    status=status.HTTP_403_FORBIDDEN
                )
            queryset = MarksData.objects.filter(
                student_subject__student__admission_number=admission_number, 
                term=term,
                exam_type=exam_type
                ).select_related(
                'student_subject__subject',
                'student_subject__student',
                'term'
            )
                        
            if not queryset.exists():
                return Response(
                    {"error": f"Student with admission number {admission_number} has no marks for the given term."},
                    status=status.HTTP_404_NOT_FOUND
                )
            first_marks_data = queryset.first()

            if not first_marks_data:
                return Response(
                    {"error": "Marks data not found."},
                    status=status.HTTP_404_NOT_FOUND
                )
            student = Student.objects.filter(admission_number=admission_number).first()
            mean_grade_data = MarksData.calculate_mean_grade(
                student=first_marks_data.student,
                term=term_id,
                exam_type=exam_type
            )
            
            students_in_class = Student.objects.filter(class_level=first_marks_data.student.class_level)
            mean_marks = []

            for class_student in students_in_class:
                student_queryset = MarksData.objects.filter(student=class_student)
                if student_queryset:
                    mean_grade_class_student = MarksData.calculate_mean_grade(
                    class_student, 
                    term=term_id,
                    exam_type=exam_type
                )
                    mean_mark = mean_grade_class_student.get('mean_marks')
                    if mean_mark is not None:
                        mean_marks.append({
                            "student": class_student,
                            "mean_mark": mean_mark
                        })
            
            mean_marks.sort(key=lambda x: x["mean_mark"], reverse=True)
            position = 1
            last_mean_mark = None
            for idx, entry in enumerate(mean_marks):
                if last_mean_mark is None or entry["mean_mark"] != last_mean_mark:
                    position = idx + 1
                last_mean_mark = entry["mean_mark"]

                if entry["student"] == student:
                    mean_grade_data["position"] = position
            term_data = []
            for x in Term.objects.filter(class_level__calendar_year=term.class_level.calendar_year):
                try:
                    m = MarksData.calculate_mean_grade(student, term=x.id)
                    # print("m", m)
                    term_data.append({"term": x.term, "mean_marks": m["mean_marks"]})
                except Exception as e:
                    term_data.append({
                        "term": x.term, 
                        "mean_marks": "N/A"
                    })    
            student_data = {
                "student":StudentReportSerializer(student).data,
                "overall_grading": mean_grade_data,
                "marks": ReportMarkListSerializer(queryset, many=True).data,
                "term_data":term_data
                
            }
            students_data.append(student_data)  
            if not queryset.exists():
                return Response(
                    {"error": f"No marks data found for student with admission number {admission_number}."},
                    status=status.HTTP_404_NOT_FOUND
                )     
        elif class_level_id:
            if user.role not in ['Admin', 'Principal', 'Teacher']:
                return Response(
                    {"error": "You have no permission to generate students report forms."},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            students_in_class = Student.objects.filter(class_level_id=class_level_id)

            mean_marks = []
            for student in students_in_class:
                queryset = MarksData.objects.filter(
                    student=student,
                    term__id=term_id,
                    exam_type=exam_type
                )
                if not queryset.exists():
                    continue            
                term_data = []
                for x in Term.objects.filter(class_level__calendar_year=term.class_level.calendar_year):
                    try:
                        m = MarksData.calculate_mean_grade(student, term=x.id)
                        # print("m", m)
                        term_data.append({"term": x.term, "mean_marks": m["mean_marks"]})
                    except Exception as e:
                        term_data.append({
                            "term": x.term, 
                            "mean_marks": "N/A"
                        })    
                if queryset.exists():
                    mean_grade_data = MarksData.calculate_mean_grade(
                        student,
                        term=term_id,
                        exam_type=exam_type
                     )
                    student_data = {
                        "student": StudentReportSerializer(student).data,
                        "overall_grading": mean_grade_data,
                        "marks": ReportMarkListSerializer(queryset, many=True).data,
                        "term_data":term_data
                        
                    }
                    mean_mark = mean_grade_data.get('mean_marks')  
                    if mean_mark is not None:
                        mean_marks.append({
                            "student": student,
                            "mean_mark": mean_mark,
                            "student_data": student_data,
                            "term_data": term_data
                        })

            mean_marks.sort(key=lambda x: x["mean_mark"], reverse=True)
            position = 1
            last_mean_mark = None
            for idx, entry in enumerate(mean_marks):
                if last_mean_mark is None or entry["mean_mark"] != last_mean_mark:
                    position = idx + 1
                last_mean_mark = entry["mean_mark"]

                entry["student_data"]["overall_grading"]["position"] = position
                students_data.append(entry["student_data"])
        if not students_data:
            return Response(
                {"error": "No marks data available for the selected class and term."},
                status=status.HTTP_404_NOT_FOUND
            )
        response_data = {
            "message": "Data found. You can now generate the report.",
            "students_data": students_data
            }
        return Response(response_data, status=status.HTTP_200_OK)
    
       
class StudentPerformanceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        exam_type = request.query_params.get('exam_type')
        calendar_year = request.query_params.get('calendar_year')
        print("calendar_year", calendar_year)
        if not exam_type:
            return Response(
                {"error": "Exam type is required for querying student performance data."},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            
            student = Student.objects.get(pk=pk)
        except Student.DoesNotExist:
            return Response(
                {"error": f"No student found with ID {pk}."},
                status=status.HTTP_404_NOT_FOUND
            )
        if calendar_year:
            terms = Term.objects.filter(class_level__calendar_year=calendar_year)
        else:
            terms = Term.objects.filter(
                class_level__calendar_year=student.class_level.calendar_year,
                class_level=student.class_level
            )
            

        # Check if no terms are found for the given calendar year
        if not terms.exists():
            return Response(
                {"error": f"No performance data for student in this year {calendar_year}. Confirm whether the student was enrolled/promoted  in this year and did exams this year ."},
                status=status.HTTP_404_NOT_FOUND
            )
        for x in terms:
            print("x", x)
       
        students_data = []
        # current_term = student.current_term
        # term_id = current_term.id if current_term else None
       
        # if not term_id:
        #     return Response(
        #         {"error": "No current term associated with the student."},
        #         status=status.HTTP_400_BAD_REQUEST
        #     )
        # term = Term.objects.get(id=term_id)
        # print("term", term)
        queryset = MarksData.objects.filter(
                student_subject__student=student,
                # student = student,
                # term__id=term_id,
                term__in=terms ,
                exam_type=exam_type
                )
        first_marks_data = queryset.first()
        if not first_marks_data:
            return Response(
                {"error": f"No marks data found for student {student.id} in given term."},
                status=status.HTTP_404_NOT_FOUND
            )
        mean_grade_data = MarksData.calculate_mean_grade(
            student=first_marks_data.student,
            # term=term_id, 
            term=first_marks_data.term.id,
            exam_type=exam_type
            )
            
        students_in_class = Student.objects.filter(class_level=first_marks_data.student.class_level)
        mean_marks = []

        for class_student in students_in_class:
            student_queryset = MarksData.objects.filter(
                student=class_student,
                exam_type=exam_type,
                term__in=terms
                
            )
            if student_queryset:
                mean_grade_class_student = MarksData.calculate_mean_grade(
                    class_student, 
                    # term=term_id, 
                    term=first_marks_data.term.id,
                    exam_type=exam_type
                    )
                mean_mark = mean_grade_class_student.get('mean_marks')
                if mean_mark is not None:
                    mean_marks.append({
                        "student": class_student,
                        "mean_mark": mean_mark
                    })
            
        mean_marks.sort(key=lambda x: x["mean_mark"], reverse=True)
        position = 1
        last_mean_mark = None
        for idx, entry in enumerate(mean_marks):
            if last_mean_mark is None or entry["mean_mark"] != last_mean_mark:
                    position = idx + 1
            last_mean_mark = entry["mean_mark"]

            if entry["student"] == student:
                mean_grade_data["position"] = position
        term_data = []
        # terms = Term.objects.filter(
        #     class_level__calendar_year=term.class_level.calendar_year,
        #     class_level=student.class_level
        # ).distinct()
        # if calendar_year:
        #     terms = Term.objects.filter(class_level__calendar_year=calendar_year)
        # else:
        #     terms = Term.objects.filter(class_level__calendar_year=term.class_level.calendar_year,
        #     class_level=student.class_level
        #     )
        if not terms.exists():
            return Response(
                {"error": f"No terms found for the calendar year {calendar_year}."},
                status=status.HTTP_404_NOT_FOUND
            )
        for x in terms:
            try:
                m = MarksData.calculate_mean_grade(student, term=x.id, exam_type=exam_type)
                if m and m["mean_marks"] is not None:
                    if not any(td["term"] == f"{x.term} - {x.class_level.calendar_year}" for td in term_data):
                        term_data.append({
                            "term": f"{x.term} - {x.class_level.calendar_year}",
                            "mean_marks": m["mean_marks"],
                            "exam_type": m.get("exam_type", ""),
                        })
            except Exception as e:
                print(f"Error calculating mean grade for term {x.id}: {e}")

        if not term_data:
            return Response(
                {"error": "No performance data found for the given student and calendar year."},
                status=status.HTTP_404_NOT_FOUND
            )
        student_data = term_data
        students_data.append(student_data)  
        if not queryset.exists():
            return Response(
                {"error": f"No Performance data found."},
                status=status.HTTP_404_NOT_FOUND
            )  
        return Response(students_data, status=status.HTTP_200_OK)

class ClassPerformanceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        class_level_id = request.query_params.get('class_level_id')
        exam_type = request.query_params.get('exam_type')
        if not class_level_id:
            first_class_level = ClassLevel.objects.first()
            if not first_class_level:
                return Response({"error": "No class levels available."}, status=status.HTTP_400_BAD_REQUEST)
            class_level = first_class_level
        else:
            try:
                class_level = ClassLevel.objects.get(id=class_level_id)
            except ClassLevel.DoesNotExist:
                return Response({"error": f"Class level with ID {class_level_id} does not exist."}, status=status.HTTP_404_NOT_FOUND)

        if not exam_type:
            return Response({"error": "Exam type is required for querying class performance data."}, 
            status=status.HTTP_400_BAD_REQUEST)
        term_id = request.query_params.get('term_id')
        if not term_id:
            current_term = Term.objects.filter(status='Active').first()
            if not current_term:
                return Response({"error": "No current Active term found."}, status=status.HTTP_400_BAD_REQUEST)
            term_id = current_term.id

        try:
            term = Term.objects.get(id=term_id)
        except Term.DoesNotExist:
            return Response({"error": f"Term with ID {term_id} does not exist."}, status=status.HTTP_404_NOT_FOUND)

        
        students_in_class = Student.objects.filter(class_level=class_level, status="Active")
        student_mean_grades = []
        total_mean_marks = 0

       
        for student in students_in_class:
            marks_data = MarksData.objects.filter(student=student, term=term, exam_type=exam_type).all()
            if not marks_data:
                continue

            first_marks_data = marks_data.first()
            mean_grade_data = MarksData.calculate_mean_grade(student=first_marks_data.student, term=first_marks_data.term.id, exam_type=exam_type)

            
            try:
                mean_marks = float(mean_grade_data['mean_marks'])
                total_mean_marks += mean_marks
                student_mean_grades.append({
                    'student': student.id,
                    'mean_marks': mean_marks,
                    'mean_grade': mean_grade_data['mean_grade']
                })
            except KeyError:
                continue

        
        total_students = len(student_mean_grades)
        if total_students == 0:
            return Response({"error": "No perfomance data found for the selected and  term in the given class."}, status=status.HTTP_400_BAD_REQUEST)

        class_overall_mean = total_mean_marks / total_students if total_students > 0 else 0

        
        grade_counts = {}
        for student_data in student_mean_grades:
            grade = student_data['mean_grade']
            grade_counts[grade] = grade_counts.get(grade, 0) + 1

       
        response_data = [
            {"class_overall_mean_mark": round(class_overall_mean, 2)},
            {"class_level": f"{class_level.name} - {class_level.calendar_year}"},
        ]

       
        mean_grade_configs = MeanGradeConfig.objects.all()
        for grade_config in mean_grade_configs:
            response_data.append({
                "mean_grade": grade_config.grade,
                "no_of_students": grade_counts.get(grade_config.grade, 0)
            })

        return Response(response_data, status=status.HTTP_200_OK)    