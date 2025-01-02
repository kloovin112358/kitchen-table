from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.base_user import BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.conf import settings
from tinymce.models import HTMLField
from taggit.managers import TaggableManager

class CustomUserManager(BaseUserManager):
    """
    Custom user model manager where email is the unique identifier
    for authentication instead of usernames.
    """
    def create_user(self, email, password, **extra_fields):
        """
        Create and save a User with the given email and password.
        """
        if not email:
            raise ValueError(_('The email must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        """
        Create and save a SuperUser with the given email and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractUser):
    username = None
    email = models.EmailField(_('email address'), unique=True)
    join_date = models.DateField(default=timezone.now)
    profile_photo = models.ImageField(blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = CustomUserManager()

    def get_full_name(self):
        return self.first_name + " " + self.last_name

    def __str__(self):
        return self.get_full_name() + " (" + self.email + ")"

class SecretSignUpCode(models.Model):
    #TODO change this to a password passphrase
    code = models.CharField(max_length=6)

    def __str__(self):
        return self.code
    
class PostCategory(models.Model):
    category = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.category
    
class PostEntry(models.Model):
    category = models.ForeignKey(PostCategory, on_delete=models.RESTRICT)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    title = models.CharField(max_length=150)
    post_body = HTMLField()
    tags = TaggableManager()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title + " by " + str(self.author) + ", submitted: " + str(self.created_at)

class FavoritePost(models.Model):
    post_entry = models.ForeignKey(PostEntry, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

class MediaUpload(models.Model):
    media_type = models.CharField(
        max_length=5, 
        choices=[
            ("Image", _("Image")), 
            ("Video", _("Video")), 
        ]
    )
    related_post_entry = models.ForeignKey(PostEntry, on_delete=models.CASCADE, blank=True, null=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    media_link = models.URLField()
    uploaded_at = models.DateTimeField(auto_now_add=True)
    caption = models.CharField(blank=True, null=True, max_length=200)

