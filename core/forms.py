from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import SecretSignUpCode, CustomUser, PostEntry
from tinymce.widgets import TinyMCE
from taggit.forms import TagWidget

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
    preset_post_id = forms.IntegerField(required=False, widget=forms.HiddenInput())
    class Meta:
        model = PostEntry
        fields = ['category', 'title', 'post_body', 'tags', 'preset_post_id']
        widgets = {
            'post_body': TinyMCE(attrs={'cols': 80, 'rows': 15}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: September family farm update'}),
            'tags': TagWidget(attrs={'class': 'form-control', 'placeholder': 'Ex: cows, wildflowers, eggs'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        if 'submit' in self.data:
            title = cleaned_data.get('title')
            category = cleaned_data.get('category')
            tags = cleaned_data.get('tags')
            post_body = cleaned_data.get('post_body')
            if not title:
                self.add_error('title', "Please provide a title.")
            if not category:
                self.add_error('category', "Please provide a category.")
            if not tags or len(tags) < 3:
                self.add_error('tags', "Please provide at least 3 tags.")
            if not post_body:
                self.add_error("post_body", "Please provide a body for the post.")
        return cleaned_data