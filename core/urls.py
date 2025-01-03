from django.urls import path
from .views import *
from django.contrib.auth.views import LogoutView
from django.urls import reverse_lazy

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('login/', LoginView.as_view(), name="log-in"),
    path('sign-up/', SignUpView.as_view(), name='sign-up'),
    path('account/', MyAccount, name="my-account"),
    path('password-reset/', PasswordReset, name="password-reset"),
    path('sign-out/', LogoutView.as_view(next_page=reverse_lazy('log-in')), name='sign-out'),
    path('post/new/', PostEntryCreateView.as_view(), name='post-create'),
    path('post/<int:pk>/edit/', PostEntryUpdateView.as_view(), name='post-edit'),
    # path('ajax/image-upload/', ImageUpload, name="image-upload")
]