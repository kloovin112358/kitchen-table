from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from django.urls import reverse_lazy
from .models import PostEntry
from django.contrib.auth.views import LoginView
from django.views.generic.edit import FormView
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from .forms import *

class HomeView(LoginRequiredMixin, ListView):
    model = PostEntry  # Replace with your model
    template_name = 'home.html'  # Path to your template
    context_object_name = 'posts'  # Name to access objects in the template
    paginate_by = 10  # Number of items per page
    login_url = reverse_lazy('log-in')  # Redirect to login if not authenticated

    # Optionally override the get_queryset method to customize the query
    def get_queryset(self):
        return super().get_queryset().order_by('-created_at')  # Example ordering

class LoginView(LoginView):
    template_name = 'login.html'  # Path to your login template
    redirect_authenticated_user = True  # Redirect to the homepage if already logged in
    next_page = reverse_lazy('home')

class SignUpView(FormView):
    template_name = 'signup.html'  # Path to your register template
    form_class = CustomSignUpForm
    success_url = reverse_lazy('home')  # Redirect after successful registration

    def form_valid(self, form):
        user = form.save()  # Save the new user
        login(self.request, user)  # Log the user in
        return super().form_valid(form)

@login_required
def MyAccount(request):
    return render(request, "myaccount.html")

def PasswordReset(request):
    return render(request, "passwordreset.html")