from django.contrib import admin
from .models import *

admin.site.register(CustomUser)
admin.site.register(SecretSignUpCode)
admin.site.register(PostCategory)
admin.site.register(PostEntry)
admin.site.register(Favorite)
admin.site.register(ImageUpload)