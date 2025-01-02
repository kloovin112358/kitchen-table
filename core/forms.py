from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import SecretSignUpCode, CustomUser

class CustomSignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)
    password1 = forms.CharField(widget=forms.PasswordInput, label="Password")
    password2 = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")
    secret_code = forms.CharField(max_length=6, required=True, label="Secret Code")

    class Meta:
        model = CustomUser
        fields = ['email', 'password1', 'password2', 'secret_code']

    def clean_secret_code(self):
        secret_code = self.cleaned_data.get("secret_code")
        try:
            code_obj = SecretSignUpCode.objects.get(code=secret_code)
        except SecretSignUpCode.DoesNotExist:
            raise forms.ValidationError("Invalid secret code.")
        return secret_code