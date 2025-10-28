"""
Authentication and user management views.
"""

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import make_password
from django.db import transaction
from .models import User
from .serializers import UserSerializer, LoginSerializer, RegisterSerializer


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for user management.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    def get_queryset(self):
        """
        Filter users based on role and permissions.
        """
        user = self.request.user
        if user.is_authenticated and user.is_instructor():
            return User.objects.all()
        elif user.is_authenticated and user.is_student():
            return User.objects.filter(id=user.id)
        return User.objects.none()


class LoginView(APIView):
    """
    Handle user login.
    """
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']
            
            user = authenticate(username=username, password=password)
            if user and user.is_active:
                login(request, user)
                return Response({
                    'success': True,
                    'message': 'Login successful',
                    'user': UserSerializer(user).data
                })
            else:
                return Response({
                    'success': False,
                    'message': 'Invalid credentials'
                }, status=status.HTTP_401_UNAUTHORIZED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    """
    Handle user logout.
    """
    
    def post(self, request):
        logout(request)
        return Response({
            'success': True,
            'message': 'Logout successful'
        })


class RegisterView(APIView):
    """
    Handle user registration.
    """
    
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            with transaction.atomic():
                user = serializer.save()
                user.set_password(serializer.validated_data['password'])
                user.save()
                
                return Response({
                    'success': True,
                    'message': 'Registration successful',
                    'user': UserSerializer(user).data
                }, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProfileView(APIView):
    """
    Handle user profile operations.
    """
    
    def get(self, request):
        if request.user.is_authenticated:
            return Response({
                'success': True,
                'user': UserSerializer(request.user).data
            })
        else:
            return Response({
                'success': False,
                'message': 'Not authenticated'
            }, status=status.HTTP_401_UNAUTHORIZED)
    
    def put(self, request):
        if request.user.is_authenticated:
            serializer = UserSerializer(request.user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'success': True,
                    'message': 'Profile updated successfully',
                    'user': serializer.data
                })
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({
                'success': False,
                'message': 'Not authenticated'
            }, status=status.HTTP_401_UNAUTHORIZED)
