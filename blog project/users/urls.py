from django.urls import path
from .views import RegisterView, UserListView, UserDetailView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='auth-register'),
    path('users/', UserListView.as_view(), name='user-list'),
    path('users/<int:pk>/', UserDetailView.as_view(), name='user-detail'),
]
