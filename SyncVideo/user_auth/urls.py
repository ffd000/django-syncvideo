from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.UserRegisterView.as_view(), name='register'),
    path('login/', views.UserLoginView.as_view(), name='login'),
    path('logout/', views.UserLogoutView.as_view(), name='logout'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    path('profile/', views.details_profile, name='profile'),
    path('delete-profile/', views.delete_profile, name='delete_profile'),
    path('password/', views.UserChangePasswordView.as_view(), name='change_password'),
]
