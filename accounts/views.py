from django.shortcuts import render, redirect
from django.views.generic import FormView
from .forms import UserRegistrationForm, UserUpdateForm
from django.contrib.auth import login, logout
from django.urls import reverse_lazy
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.views import View
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.contrib import messages
# Create your views here.

def user_info_email(user, field, subject, template):
      message = render_to_string(template, {
            'user': user,
            'field': field,
      })
      send_email = EmailMultiAlternatives(subject, '', to = [user.email])
      send_email.attach_alternative(message, 'text/html')
      send_email.send()


class UserRegistrationView(FormView):
      template_name = 'accounts/user_registration.html'
      form_class = UserRegistrationForm
      success_url = reverse_lazy('login')
      
      def form_valid(self, form):
            print(form.cleaned_data)
            user = form.save()
            login(self.request, user)
            print(user)
            return super().form_valid(form)     # If everything is okay, the form_valid function will be called
      
      
class UserLoginView(LoginView):
      template_name = 'accounts/user_login.html'
      
      
      def get_success_url(self):
            return reverse_lazy('home')
      

class UserLogoutView(LogoutView):
      def get_success_url(self):
            if self.request.user.is_authenticated:
                  logout(self.request)
            return reverse_lazy('home')
      

class UserUpdateView(View):
      template_name = 'accounts/profile.html'
      
      def get(self, request):
            form = UserUpdateForm(instance = request.user)
            return render(request, self.template_name, {'form': form})

      def post(self, request):
            form = UserUpdateForm(request.POST, instance = request.user)
            if form.is_valid():
                  form.save()
                  return redirect('profile')
            return render(request, self.template_name, {'form', form})
      
      
      
class UserPasswordUpdateView(PasswordChangeView):
      template_name = 'accounts/password.html'
      success_url = reverse_lazy('profile')
      
      def form_valid(self, form):
            messages.success(self.request, 'Password changed successfully.')
            user_info_email(
                  self.request.user, 
                  'Password', 
                  'Password change',
                  'accounts/emails/password_email.html'
                  )
            return super().form_valid(form)
      
      def form_invalid(self, form):
            messages.error(self.request, 'Invalid Password')
            return super().form_invalid(form)