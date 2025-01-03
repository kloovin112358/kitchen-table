from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import SecretSignUpCode, CustomUser, PostEntry
from tinymce.widgets import TinyMCE

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

class EditProfilePhotoForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['profile_photo']
        widgets = {
            'profile_photo': forms.FileInput(attrs={'class': 'form-control'}),
        }

class PostEntryForm(forms.ModelForm):
    class Meta:
        model = PostEntry
        fields = ['category', 'title', 'post_body', 'tags']
        widgets = {
            'post_body': TinyMCE(attrs={'cols': 80, 'rows': 15}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: September family farm update'}),
            'tags': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Add tags, separated by commas'}),
        }