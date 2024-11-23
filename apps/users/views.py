from django.db import IntegrityError
from django.shortcuts import render
from django.utils import timezone

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils.crypto import get_random_string 
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer
from apps.users.models import User
from apps.users.serializers import UserListSerializer, UserProfileSerializer, UserSerializer
from apps.main.serializers import SubjectCategorySerializer
from apps.utils import DataPagination
from django.contrib.auth.models import Permission
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth import authenticate
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from rest_framework import viewsets


class LoginAPIView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response({'error': 'Username and password are required.'}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(username=username, password=password)

        if user is not None:

            tokens = user.get_jwt_tokens()
            response = Response({
                'accessToken': tokens['access'],
                'refreshToken': tokens['refresh'],
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'phone_number': user.phone_number,
                    'role': user.role,
                }
            })
            # response.set_cookie(
            #     key='accessToken',
            #     value=tokens['access'],
            #     httponly=True,
            #     secure=False,  
            #     samesite='Strict'
            # )
            # response.set_cookie(
            #     key='refreshToken',
            #     value=tokens['access'],
            #     httponly=True,
            #     secure=False,
            #     samesite='Strict'
            # )

            return response

        else:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)


class UserAPIView(APIView):
    renderer_classes = [JSONRenderer, BrowsableAPIRenderer]
    serializer_class = UserListSerializer

    def get(self, request, pk=None):
        if pk:
            try:
                user = User.objects.get(pk=pk)
                serializer = UserListSerializer(user)
                return Response(serializer.data)
            except User.DoesNotExist:
                return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        else:
            users = User.objects.filter(role__in=["Admin", "Principal"])

            page = request.query_params.get('page')
            page_size = request.query_params.get('page_size')
            users = users.order_by('-created_at')
            if page or page_size:
                paginator = DataPagination()
                paginated_users = paginator.paginate_queryset(users, request)
                serializer = UserListSerializer(paginated_users, many=True)
                return paginator.get_paginated_response(serializer.data)
            else:
                serializer = UserListSerializer(users, many=True)
                return Response(serializer.data)

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data.get('username')
            email = serializer.validated_data.get('email')

            if User.objects.filter(username=username).exists():
                return Response({"error": "A user with this username already exists."}, status=status.HTTP_400_BAD_REQUEST)

            if User.objects.filter(email=email).exists():
                return Response({"error": "A user with this email already exists."}, status=status.HTTP_400_BAD_REQUEST)

            try:
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except IntegrityError:
                return Response({"error": "An error occured while creating user"}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

       
        username = request.data.get('username')
        email = request.data.get('email')

       
        if User.objects.filter(username=username).exclude(pk=pk).exists():
            return Response({"error": "A user with this username already exists."}, status=status.HTTP_400_BAD_REQUEST)

        
        if User.objects.filter(email=email).exclude(pk=pk).exists():
            return Response({"error": "A user with this email already exists."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = UserSerializer(user, data=request.data)

      
        if serializer.is_valid():
            try:
                serializer.save()
                return Response({
                "message": "Account updated successfully",  
                "user": serializer.data  
            }, status=status.HTTP_200_OK)
            except IntegrityError:
                return Response({"error": "An error occurred while updating the user."}, status=status.HTTP_400_BAD_REQUEST)

        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def delete(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        user.delete()
        return Response({"message: Account successfully deleted!"}, status=status.HTTP_204_NO_CONTENT)

class UserProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user 
        print("user->", user)
        serializer = UserProfileSerializer(user)  
        return Response(serializer.data)  

class AvailableTeacherUsersAPIView(APIView):
    def get(self, request):
        users = User.objects.filter(role='Teacher') 
        serializer = UserListSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class PasswordResetRequestAPIView(APIView):
    def post(self, request):
        email = request.data.get('email')
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "Account with this email does not exist."}, status=status.HTTP_404_NOT_FOUND)

       
        token = get_random_string(length=32)
        user.password_reset_token = token
        user.token_created_at = timezone.now()
        user.save()
        return Response({"token": token, "message": "Use this token to reset your password."}, status=status.HTTP_200_OK)

class PasswordResetAPIView(APIView):
    def post(self, request):
        token = request.data.get('token')
        new_password = request.data.get('new_password')
        
        try:
            user = User.objects.get(password_reset_token=token)
            if timezone.now() > user.token_created_at + timezone.timedelta(hours=1):
                return Response({"error": "Password reset Token has expired."}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({"error": "Invalid token."}, status=status.HTTP_400_BAD_REQUEST)

       
        user.set_password(new_password)
        user.password_reset_token = None  
        user.token_created_at = None  
        user.save()

        return Response({"message": "Password has been reset successfully."}, status=status.HTTP_200_OK)


class ChangePasswordAPIView(APIView):
    permission_classes = [IsAuthenticated] 

    def post(self, request):
        user = request.user
        current_password = request.data.get("current_password")
        new_password = request.data.get("new_password")
        confirm_password = request.data.get("confirm_password")
        
       
        if not current_password or not new_password or not confirm_password:
            return Response({"error": "All fields are required."}, status=status.HTTP_400_BAD_REQUEST)
        
        if not user.check_password(current_password):
            return Response(
                {"error": "The current password you entered is incorrect."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if new_password != confirm_password:
            return Response({"error": "New password and confirm password do not match."}, status=status.HTTP_400_BAD_REQUEST)
        
       
        user.set_password(new_password)
        user.save()

        return Response({"message": "Password changed successfully."}, status=status.HTTP_200_OK)


class PermissionViewSet(viewsets.ViewSet):
    def list(self, request):
        permissions = Permission.objects.all()
        permission_list = [
            {'id': p.id, 'name': f"{p.content_type.app_label} | {p.name}"}
            for p in permissions
        ]
        return Response(permission_list)


