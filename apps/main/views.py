from django.shortcuts import render


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer
from apps.utils import DataPagination
from apps.main.models import ClassLevel, FormLevel, GradingConfig, MeanGradeConfig, Stream, Subject, SubjectCategory, Term
from apps.main.serializers import ClassLevelListSerializer, MeanGradeConfigSerializer, ClassLevelSerializer, FormLevelListSerializer, FormLevelSerializer, GradingConfigListSerializer, GradingConfigSerializer, ListSubjectSerializer, StreamListSerializer, StreamSerializer, SubjectCategorySerializer, SubjectSerializer, TermListSerializer, TermSerializer
from apps.teachers.models import Teacher, TeacherSubject
class SubjectAPIView(APIView):
    renderer_classes = [JSONRenderer, BrowsableAPIRenderer]
    serializer_class = SubjectSerializer
    def get(self, request, pk=None):
        user_role = request.user.role 
        if pk:
            try:
                subject = Subject.objects.get(pk=pk)
                if user_role in ['Admin', 'Principal'] or TeacherSubject.objects.filter(teacher__user=request.user, subject=subject).exists():
                    serializer = ListSubjectSerializer(subject)
                    return Response(serializer.data)
                else:
                    return Response({"error": "Subject not assigned to this teacher."}, status=status.HTTP_403_FORBIDDEN)

            except Subject.DoesNotExist:
               return Response({"error": "Subject not found."}, status=status.HTTP_404_NOT_FOUND)
        else:
            if user_role in ['Admin', 'Principal']:
                subjects = Subject.objects.all()
            else:
                teacher = Teacher.objects.get(user=request.user)
                subjects = Subject.objects.filter(teachersubject__teacher=teacher).distinct()
            subjects = subjects.order_by('-created_at')
            page = request.query_params.get('page')
            page_size = request.query_params.get('page_size')
            
            if page or page_size:
                paginator = DataPagination()
                paginated_subjects = paginator.paginate_queryset(subjects, request)
                serializer = ListSubjectSerializer(paginated_subjects, many=True)
                return paginator.get_paginated_response(serializer.data)
            else:
                
                serializer = ListSubjectSerializer(subjects, many=True)
                return Response(serializer.data)

    def post(self, request):
        subject_name = request.data.get('subject_name')
        if Subject.objects.filter(subject_name=subject_name).exists():
            return Response({"error": "A subject with this name already exists."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = SubjectSerializer(data=request.data)
        if serializer.is_valid():
            subject = serializer.save()
            all_class_levels = ClassLevel.objects.all()
            subject.class_levels.set(all_class_levels)
            return Response(SubjectSerializer(subject).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        try:
            subject = Subject.objects.get(pk=pk)
            new_subject_name = request.data.get('subject_name')
            if Subject.objects.filter(subject_name=new_subject_name).exclude(pk=pk).first():
                return Response({"error": "A Subject with that name  already exists."},
                        status=status.HTTP_400_BAD_REQUEST)
            serializer = SubjectSerializer(subject, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response( {
                        "message": "Subject updated successfully",
                        "data": serializer.data  
                    },
                    status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Subject.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
    
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, pk):
        try:
            subject = Subject.objects.get(pk=pk)
        except Subject.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        subject.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class SubjectCategoryAPIView(APIView):
    renderer_classes = [JSONRenderer, BrowsableAPIRenderer]
    serializer_class = SubjectCategorySerializer
    def get(self, request, pk=None):
        if pk:
            try:
                subject_category = SubjectCategory.objects.get(pk=pk)
                serializer = SubjectCategorySerializer(subject_category)
                return Response(serializer.data)
            except SubjectCategory.DoesNotExist:
               return Response({"error": "Subject Category not found."}, status=status.HTTP_404_NOT_FOUND)
        else:
            subject_categories = SubjectCategory.objects.all().order_by('-created_at')
            
            
            page = request.query_params.get('page')
            page_size = request.query_params.get('page_size')
            
            if page or page_size:
                paginator = DataPagination()
                paginated_subject_categories = paginator.paginate_queryset(subject_categories, request)
                serializer = SubjectCategorySerializer(paginated_subject_categories, many=True)
                return paginator.get_paginated_response(serializer.data)
            else:
                
                serializer = SubjectCategorySerializer(subject_categories, many=True)
                return Response(serializer.data)

    def post(self, request):
        serializer = SubjectCategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        try:
            subject_category = SubjectCategory.objects.get(pk=pk)
        except SubjectCategory.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = SubjectCategorySerializer(subject_category, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            subject_category = SubjectCategory.objects.get(pk=pk)
        except SubjectCategory.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        subject_category.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class FormLevelAPIView(APIView):
    renderer_classes = [JSONRenderer, BrowsableAPIRenderer]
    serializer_class = FormLevelSerializer
    def get(self, request, pk=None):
        if pk:
            try:
                form_level = FormLevel.objects.get(pk=pk)
                serializer = FormLevelListSerializer(form_level)
                return Response(serializer.data)
            except FormLevel.DoesNotExist:
               return Response({"error": "Subject Category not found."}, status=status.HTTP_404_NOT_FOUND)
        else:
            form_levels = FormLevel.objects.all().order_by('-created_at')
            
            
            page = request.query_params.get('page')
            page_size = request.query_params.get('page_size')
            
            if page or page_size:
                paginator = DataPagination()
                paginated_form_levels = paginator.paginate_queryset(form_levels, request)
                serializer = FormLevelListSerializer(paginated_form_levels, many=True)
                return paginator.get_paginated_response(serializer.data)
            else:
                
                serializer = FormLevelListSerializer(form_levels, many=True)
                return Response(serializer.data)

    def post(self, request):
        data = request.data
        name = data.get('name')
        level = data.get('level')

       
        if FormLevel.objects.filter(name=name).exists():
            return Response({"error": f"A Form Level with name  {name} already exists."}, status=status.HTTP_400_BAD_REQUEST)

        if FormLevel.objects.filter(level=level).exists():
            return Response({"error": f"A Form Level with the level {level}  already exists."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = FormLevelSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        try:
            form_level = FormLevel.objects.get(pk=pk)
        except FormLevel.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = FormLevelSerializer(form_level, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            form_level = FormLevel.objects.get(pk=pk)
        except FormLevel.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        form_level.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class StreamAPIView(APIView):
    renderer_classes = [JSONRenderer, BrowsableAPIRenderer]
    serializer_class = StreamSerializer
    def get(self, request, pk=None):
        if pk:
            try:
                stream = Stream.objects.get(pk=pk)
                serializer = StreamListSerializer(stream)
                return Response(serializer.data)
            except Stream.DoesNotExist:
               return Response({"error": "Stream not found."}, status=status.HTTP_404_NOT_FOUND)
        else:
            streams = Stream.objects.all().order_by('created_at')
            
            
            page = request.query_params.get('page')
            page_size = request.query_params.get('page_size')
            
            if page or page_size:
                paginator = DataPagination()
                paginated_streams= paginator.paginate_queryset(streams, request)
                serializer = StreamListSerializer(paginated_streams, many=True)
                return paginator.get_paginated_response(serializer.data)
            else:
                
                serializer = StreamListSerializer(streams, many=True)
                return Response(serializer.data)

    def post(self, request):
        name = request.data.get('name')
        if Stream.objects.filter(name=name).exists():
            return Response({"error": f"A stream  with this name {name} already exists."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = StreamSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        try:
            stream = Stream.objects.get(pk=pk)
        except Stream.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        new_name = request.data.get('name')
        existing_stream = Stream.objects.filter(name=new_name).exclude(pk=pk).first()
        if existing_stream:
            return Response({"detail": f"A stream with the name '{new_name}' already exists."}, status=status.HTTP_400_BAD_REQUEST)
        serializer = StreamSerializer(stream, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            stream = Stream.objects.get(pk=pk)
        except Stream.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        stream.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class ClassLevelAPIView(APIView):
    renderer_classes = [JSONRenderer, BrowsableAPIRenderer]
    serializer_class = ClassLevelSerializer
    def get(self, request, pk=None):
        user_role = request.user.role 
        if pk:
            try:
                class_level = ClassLevel.objects.get(pk=pk)
                if user_role in ['Admin', 'Principal'] or TeacherSubject.objects.filter(teacher__user=request.user, class_level=class_level).exists():
                    serializer = ClassLevelListSerializer(class_level)
                    return Response(serializer.data)
                else:
                    return Response({"error": "Class level not assigned to this teacher."}, status=status.HTTP_403_FORBIDDEN)

            except ClassLevel.DoesNotExist:
                return Response({"error": "Class Level  does not exist."}, status=status.HTTP_404_NOT_FOUND)
        else:
            if user_role in ['Admin', 'Principal']:
                # Admins and Principals see all class levels
                class_levels = ClassLevel.objects.all()
            else:
                teacher = Teacher.objects.get(user=request.user)
                class_levels = ClassLevel.objects.filter(teachersubject__teacher=teacher).distinct()
            class_levels=class_levels.order_by('-created_at')
            page = request.query_params.get('page')
            page_size = request.query_params.get('page_size')
            
            if page or page_size:
                paginator = DataPagination()
                paginated_class_levels = paginator.paginate_queryset(class_levels, request)
                serializer = ClassLevelListSerializer(paginated_class_levels, many=True)
                return paginator.get_paginated_response(serializer.data)
            else:
                serializer = ClassLevelListSerializer(class_levels, many=True)
                return Response(serializer.data)

    def post(self, request):
        form_level_id = request.data.get('form_level')
        stream_id = request.data.get('stream')
        existing_class_level_no_stream = ClassLevel.objects.filter(form_level_id=form_level_id, stream__isnull=True).first()
        
        if existing_class_level_no_stream and stream_id:
            return Response(
                {
                    "error": (
                        "A class level with this form level and no stream already exists. "
                        "Please update or delete the existing class level before adding a new one with a stream."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if stream_id:
            if ClassLevel.objects.filter(form_level_id=form_level_id, stream_id=stream_id).exists():
                return Response(
                    {"error": "A class level with this form level and stream already exists."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            
            # if ClassLevel.objects.filter(form_level_id=form_level_id, stream__isnull=True).exists()
            if existing_class_level_no_stream:
                return Response(
                    {"error": "A class level with this form level and no stream already exists."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        serializer = ClassLevelSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        try:
            class_level = ClassLevel.objects.get(pk=pk)
        except ClassLevel.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = ClassLevelSerializer(class_level, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            class_level = ClassLevel.objects.get(pk=pk)
        except ClassLevel.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        class_level.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
class GraduatingClassAPIView(APIView):
    renderer_classes = [JSONRenderer, BrowsableAPIRenderer]
    serializer_class = ClassLevelListSerializer

    def get(self, request):
        user_role = request.user.role
        
        graduating_class_levels = ClassLevel.objects.filter(form_level__level=4)
        print("graduating_class_levels", graduating_class_levels)
       
        if user_role in ['Admin', 'Principal']:
            pass
        else:
           
            teacher = Teacher.objects.get(user=request.user)
            graduating_class_levels = graduating_class_levels.filter(teachersubject__teacher=teacher).distinct()

        page = request.query_params.get('page')
        page_size = request.query_params.get('page_size')
        
        if page or page_size:
            paginator = DataPagination()
            paginated_class_levels = paginator.paginate_queryset(graduating_class_levels, request)
            serializer = ClassLevelListSerializer(paginated_class_levels, many=True)
            return paginator.get_paginated_response(serializer.data)
        else:
            serializer = ClassLevelListSerializer(graduating_class_levels, many=True)
            return Response(serializer.data)

class GradingConfigAPIView(APIView):
    renderer_classes = [JSONRenderer, BrowsableAPIRenderer]
    serializer_class = GradingConfigSerializer
    def get(self, request, pk=None):
        if pk:
            try:
                grading_config = GradingConfig.objects.get(pk=pk)
                serializer = GradingConfigListSerializer(grading_config)
                return Response(serializer.data)
            except GradingConfig.DoesNotExist:
                return Response({"error": "Grading config  does not exist."}, status=status.HTTP_404_NOT_FOUND)
        else:
            grading_configs = GradingConfig.objects.all().order_by('-created_at')
            page = request.query_params.get('page')
            page_size = request.query_params.get('page_size')
            
            if page or page_size:
                paginator = DataPagination()
                paginated_grading_configs = paginator.paginate_queryset(grading_configs, request)
                serializer = GradingConfigListSerializer(paginated_grading_configs, many=True)
                return paginator.get_paginated_response(serializer.data)
            else:
                serializer = GradingConfigListSerializer(grading_configs, many=True)
                return Response(serializer.data)

    def post(self, request):
        grade = request.data.get('grade')
        subject_category = request.data.get('subject_category')

        
        if GradingConfig.objects.filter(grade=grade, subject_category=subject_category).exists():
            return Response({"error": "A grading config for the given subject category and grade already exists."},
                            status=status.HTTP_400_BAD_REQUEST)
        serializer = GradingConfigSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        try:
            grading_config = GradingConfig.objects.get(pk=pk)
        except GradingConfig.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        grade = request.data.get('grade')
        subject_category = request.data.get('subject_category')
        
        if GradingConfig.objects.filter(grade=grade, subject_category=subject_category).exclude(pk=pk).first():
            return Response({"error": "A grading config for the given subject category and grade already exists."},
                    status=status.HTTP_400_BAD_REQUEST)
        serializer = GradingConfigSerializer(grading_config, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            grading_config = GradingConfig.objects.get(pk=pk)
        except GradingConfig.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        grading_config.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class MeanGradeConfigAPIView(APIView):
    renderer_classes = [JSONRenderer, BrowsableAPIRenderer]
    serializer_class = GradingConfigSerializer
    def get(self, request, pk=None):
        if pk:
            try:
                mean_grade_config = MeanGradeConfig.objects.get(pk=pk)
                serializer = MeanGradeConfigSerializer(mean_grade_config)
                return Response(serializer.data)
            except GradingConfig.DoesNotExist:
                return Response({"error": "Grading config  does not exist."}, status=status.HTTP_404_NOT_FOUND)
        else:
            mean_grade_configs = MeanGradeConfig.objects.all().order_by('-created_at')
            page = request.query_params.get('page')
            page_size = request.query_params.get('page_size')
            
            if page or page_size:
                paginator = DataPagination()
                paginated_mean_grade_configs = paginator.paginate_queryset(mean_grade_configs, request)
                serializer = MeanGradeConfigSerializer(paginated_mean_grade_configs, many=True)
                return paginator.get_paginated_response(serializer.data)
            else:
                serializer = MeanGradeConfigSerializer(grading_configs, many=True)
                return Response(serializer.data)

    def post(self, request):
        grade = request.data.get('grade')
       

        
        if MeanGradeConfig.objects.filter(grade=grade).exists():
            return Response({"error": "A mean grade config for the given  grade already exists."},
                            status=status.HTTP_400_BAD_REQUEST)
        serializer = MeanGradeConfigSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        try:
            mean_grade_config = MeanGradeConfig.objects.get(pk=pk)
        except MeanGradConfig.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        grade = request.data.get('grade')
        if MeanGradeConfig.objects.filter(grade=grade).exclude(pk=pk).first():
            return Response({"error": "A  mean grade config for the given  grade already exists."},
                    status=status.HTTP_400_BAD_REQUEST)
        serializer = MeanGradeConfigSerializer(mean_grade_config, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            mean_grade_config = MeanGradeConfig.objects.get(pk=pk)
        except MeanGradeConfig.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        mean_grade_config.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
class TermsAPIView(APIView):
    renderer_classes = [JSONRenderer, BrowsableAPIRenderer]
    serializer_class = TermSerializer
    def get(self, request, pk=None):
        user_role = request.user.role 
        if pk:
            try:
                term = Term.objects.get(pk=pk)
                serializer = TermListSerializer(term)
                return Response(serializer.data)
            except Subject.DoesNotExist:
               return Response({"error": "Term not found."}, status=status.HTTP_404_NOT_FOUND)
        else:
           
            terms = Term.objects.all().order_by('-created_at')
            page = request.query_params.get('page')
            page_size = request.query_params.get('page_size')
            
            if page or page_size:
                paginator = DataPagination()
                paginated_subjects = paginator.paginate_queryset(terms, request)
                serializer = TermListSerializer(paginated_subjects, many=True)
                return paginator.get_paginated_response(serializer.data)
            else:
                
                serializer = TermListSerializer(terms, many=True)
                return Response(serializer.data)
    def post(self, request):
        data = request.data
        if 'status' not in data:
            data['status'] = 'Active' 
        
        
        if Term.objects.filter(term=data['term'], calendar_year=data['calendar_year']).exists():
            return Response({"error": "Term already exists."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = TermSerializer(data=data)
        if serializer.is_valid():
            term = serializer.save()  
            return Response(TermSerializer(term).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk=None):
        
        try:
            term = Term.objects.get(pk=pk)
        except Term.DoesNotExist:
            return Response({"error": "Term not found."}, status=status.HTTP_404_NOT_FOUND)

        
        data = request.data
        if Term.objects.filter(term=data['term'], calendar_year=data['calendar_year']).exclude(pk=term.pk).exists():
            return Response({"error": "Term already exists."}, status=status.HTTP_400_BAD_REQUEST)

        
        serializer = TermSerializer(term, data=data, partial=True)  
        if serializer.is_valid():
            term = serializer.save()  
            return Response(TermSerializer(term).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    def patch(self, request, pk=None):
        try:
            term = Term.objects.get(pk=pk)
        except Term.DoesNotExist:
            return Response({"error": "Term not found."}, status=status.HTTP_404_NOT_FOUND)

        data = request.data
        serializer = TermSerializer(term, data=data, partial=True)  
        if serializer.is_valid():
            term = serializer.save()
            return Response(TermSerializer(term).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    def delete(self, request, pk=None):
        try:
            term = Term.objects.get(pk=pk)
            term.delete()  
            return Response({"message": "Term deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except Term.DoesNotExist:
            return Response({"error": "Term not found."}, status=status.HTTP_404_NOT_FOUND)

class ActiveTermsAPIView(APIView):
    renderer_classes = [JSONRenderer, BrowsableAPIRenderer]
    serializer_class = TermListSerializer
    def get(self, request):
        user_role = request.user.role 
        
           
        terms = Term.objects.filter(status="Active")
        page = request.query_params.get('page')
        page_size = request.query_params.get('page_size')
            
        if page or page_size:
            paginator = DataPagination()
            paginated_subjects = paginator.paginate_queryset(terms, request)
            serializer = TermListSerializer(paginated_subjects, many=True)
            return paginator.get_paginated_response(serializer.data)
        else:
                
            serializer = TermListSerializer(terms, many=True)
            return Response(serializer.data)