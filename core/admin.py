from django.contrib import admin
from .models import *

admin.site.register(CustomUser)
admin.site.register(SecretSignUpCode)
admin.site.register(PostCategory)
admin.site.register(PostEntry)
admin.site.register(FavoritePost)
admin.site.register(MediaUpload)