"""
API URL patterns for the code review system.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'assignments', views.AssignmentViewSet)
router.register(r'submissions', views.SubmissionViewSet)
router.register(r'feedback', views.FeedbackViewSet)
router.register(r'plagiarism', views.PlagiarismReportViewSet)
router.register(r'exports', views.ExportJobViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('upload/', views.FileUploadView.as_view(), name='file-upload'),
    path('analyze/', views.CodeAnalysisView.as_view(), name='code-analysis'),
    path('health/', views.HealthCheckView.as_view(), name='health-check'),
    
    # Authentication endpoints
    path('auth/login/', views.LoginView.as_view(), name='login'),
    path('auth/logout/', views.LogoutView.as_view(), name='logout'),
    path('auth/register/', views.RegisterView.as_view(), name='register'),
    path('auth/profile/', views.ProfileView.as_view(), name='profile'),
]
