from django.urls import path
from .views import UserRegistrationView, UserLoginView, UserLogoutView, UserUpdateView, UserPasswordUpdateView


urlpatterns = [
      path('register/', UserRegistrationView.as_view(), name = 'register'),
      path('login/', UserLoginView.as_view(), name = 'login'),
      path('logout/', UserLogoutView.as_view(), name = 'logout'),
      path('profile/', UserUpdateView.as_view(), name = 'profile'),
      path('password_update/', UserPasswordUpdateView.as_view(), name = 'password_update'),
]