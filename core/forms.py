from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import SecretSignUpCode, CustomUser

class CustomSignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)
    password1 = forms.CharField(widget=forms.PasswordInput, label="Password")
    password2 = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")
    secret_code = forms.CharField(max_length=300, required=True, label="Secret Passphrase")
    first_name = forms.CharField()
    last_name = forms.CharField()

    class Meta:
        model = CustomUser
        fields = ['email', 'password1', 'password2', 'secret_code', "first_name", "last_name"]

    def clean_secret_code(self):
        secret_code = self.cleaned_data.get("secret_code")
        try:
            code_obj = SecretSignUpCode.objects.get(code=secret_code)
        except SecretSignUpCode.DoesNotExist:
            raise forms.ValidationError("Passphrase is not correct.")
        return secret_code