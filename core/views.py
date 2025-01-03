from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import PostEntry, ImageUpload
from django.contrib.auth.views import LoginView
from django.views.generic.edit import FormView
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from .forms import *
from django.contrib import messages
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.utils.timezone import get_current_timezone_name, now
from django.http import HttpResponseRedirect
import mimetypes
from django.core.exceptions import ValidationError
from django.core.files.images import get_image_dimensions
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View

class HomeView(LoginRequiredMixin, ListView):
    model = PostEntry  # Replace with your model
    template_name = 'home.html'  # Path to your template
    context_object_name = 'posts'  # Name to access objects in the template
    paginate_by = 10  # Number of items per page
    login_url = reverse_lazy('log-in')  # Redirect to login if not authenticated

    def get_queryset(self):
        return PostEntry.objects.filter(status='Live').order_by('-created_at')

class LoginView(LoginView):
    template_name = 'login.html'  # Path to your login template
    redirect_authenticated_user = True  # Redirect to the homepage if already logged in
    next_page = reverse_lazy('home')

    def form_valid(self, form):
        response = super().form_valid(form)
        user_timezone = self.request.user.local_timezone
        if user_timezone:
            try:
                self.request.session["django_timezone"] = user_timezone
            except Exception as e:
                print(f"Error activating timezone: {e}")
        return response

class SignUpView(FormView):
    template_name = 'signup.html'  # Path to your register template
    form_class = CustomSignUpForm
    success_url = reverse_lazy('home')  # Redirect after successful registration

    def form_valid(self, form):
        user = form.save()  # Save the new user
        login(self.request, user)  # Log the user in

        message = mark_safe(
            f"Welcome,  {user.first_name}! If you'd like, you can start by adding <a href='{reverse('my-account')}'>a profile photo</a>."
        )
        messages.success(self.request, message)

        return super().form_valid(form)

@login_required
def MyAccount(request):
    user = request.user
    form = EditProfilePhotoForm(instance=user)
    if request.method == "POST":
        if 'update_timezone' in request.POST:
            request.session["django_timezone"] = request.POST["timezone"]
            user.local_timezone = request.POST["timezone"]
            user.save()
            messages.success(request, "Your timezone has been updated to " + str(request.POST["timezone"]) + ".")
            return redirect("my-account")
        else:
            form = EditProfilePhotoForm(request.POST, request.FILES, instance=user)
            if form.is_valid():
                form.save()
                messages.success(request, "Your profile photo has been updated!")
                return redirect("my-account")
            else:
                messages.error(request, "There was an error updating your profile photo. Please try again.")

    return render(request, "myaccount.html", {
        "form": form, 
        "post_drafts": PostEntry.objects.filter(author=user, status="Draft").order_by("-last_updated"),
        "active_user_timezone": get_current_timezone_name(),
        "timezones": {
            "US/Pacific (Los Angeles)": "America/Los_Angeles",
            "US/Mountain (Denver)": "America/Denver",
            "US/Central (Chicago)": "America/Chicago",
            "US/Eastern (New York)": "America/New_York",
            "Caribbean (Puerto Rico)": "America/Puerto_Rico",
            "Hawaii-Aleutian Standard Time (Honolulu)": "Pacific/Honolulu",
            "Alaska Standard Time (Anchorage)": "America/Anchorage",
            "Greenwich Mean Time (London)": "Europe/London",
            "Western European Time (Lisbon)": "Europe/Lisbon",
            "Central European Time (Paris)": "Europe/Paris",
            "Eastern European Time (Bucharest)": "Europe/Bucharest",
            "Moscow Standard Time (Moscow)": "Europe/Moscow",
            "Further Eastern European (Kiev)": "Europe/Kiev",
            "China Standard Time (Shanghai)": "Asia/Shanghai",
            "Indian Standard Time (Kolkata)": "Asia/Kolkata",
            "Japan Standard Time (Tokyo)": "Asia/Tokyo",
            "Korea Standard Time (Seoul)": "Asia/Seoul",
            "Singapore Time (Singapore)": "Asia/Singapore",
            "Gulf Standard Time (Dubai)": "Asia/Dubai",
            "Bangladesh Standard Time (Dhaka)": "Asia/Dhaka",
            "Indochina Time (Bangkok)": "Asia/Bangkok",
            "Pakistan Standard Time (Karachi)": "Asia/Karachi",
            "Western Indonesia Time (Jakarta)": "Asia/Jakarta",
            "Central Indonesia Time (Bali)": "Asia/Makassar",
            "Eastern Indonesia Time (Jayapura)": "Asia/Jayapura",
            "Australian Western Standard Time (Perth)": "Australia/Perth",
            "Australian Central Standard Time (Adelaide)": "Australia/Adelaide",
            "Australian Central Standard Time (Darwin)": "Australia/Darwin",
            "Australian Eastern Standard Time (Sydney)": "Australia/Sydney",
            "Australian Eastern Standard Time (Melbourne)": "Australia/Melbourne",
            "Argentina Time (Buenos Aires)": "America/Argentina/Buenos_Aires",
            "Brazil Standard Time (Brasilia)": "America/Sao_Paulo",
            "Chile Standard Time (Santiago)": "America/Santiago",
            "Colombia Time (Bogotá)": "America/Bogota",
            "Peru Time (Lima)": "America/Lima",
            "Paraguay Time (Asunción)": "America/Asuncion",
            "Venezuela Time (Caracas)": "America/Caracas",
            "Ecuador Time (Quito)": "America/Guayaquil"
        }
    })

@login_required
def CreateDummyPostInstance(request):
    newPostEntry = PostEntry(author=request.user)
    newPostEntry.save()
    return JsonResponse({"entry_id": newPostEntry.id}, status=201)

def PasswordReset(request):
    return render(request, "passwordreset.html")

class PostEntryBaseView:
    def form_valid(self, form):
        form.instance.author = self.request.user  # Set the logged-in user as the author
        if "save_as_draft" in self.request.POST:
            # Set status to "Draft" when Save as Draft button is clicked
            form.instance.status = "Draft"
            form.instance.last_updated = now()
            messages.success(self.request, "Your changes have been saved. Feel free to continue editing.")
        elif "submit" in self.request.POST:
            # Set status to "Live" when Submit button is clicked
            form.instance.status = "Live"
            messages.success(self.request, "Nice! Your post is now live.")
        return super().form_valid(form)

    def form_invalid(self, form):
        if "submit" in self.request.POST:
            messages.error(self.request, "Please correct the errors, marked in red.")
        return super().form_invalid(form)

    def get_success_url(self):
        if self.object.status == "Draft":
            return reverse_lazy('post-edit', kwargs={'pk': self.object.pk})
        else:
            return reverse_lazy('home')

class PostEntryCreateView(LoginRequiredMixin, PostEntryBaseView, CreateView):
    model = PostEntry
    form_class = PostEntryForm
    template_name = 'postcreate.html'  # Replace with your actual template path
    success_url = reverse_lazy('home')  # Redirect after success (e.g., to a list of posts)

class PostEntryUpdateView(LoginRequiredMixin, PostEntryBaseView, UpdateView):
    model = PostEntry
    form_class = PostEntryForm
    template_name = 'postcreate.html'  # Replace with your actual template path
    success_url = reverse_lazy('home')  # Redirect after success (e.g., to a list of posts)

    def get_queryset(self):
        # Ensure the user can only edit their own posts (optional, but a good practice)
        return PostEntry.objects.filter(author=self.request.user)

class PostEntryDeleteView(LoginRequiredMixin, DeleteView):
    model = PostEntry
    success_url = reverse_lazy('home')

    def dispatch(self, request, *args, **kwargs):
        # Check if the pk is 0 before proceeding with any actions
        pk = self.kwargs.get('pk')
        
        if pk == 0:  # Handle case where pk is 0 (invalid)
            messages.info(self.request, "Changes discarded.")
            return redirect('home')  # Redirect to home and skip all further actions
        
        # Proceed with the default dispatch behavior if pk is valid
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return PostEntry.objects.filter(author=self.request.user)

    def post(self, request, *args, **kwargs):
        # Delete the object
        if 'pk' in self.kwargs:
            self.object = self.get_object()
            self.object.delete()

            # Show success message
            messages.success(self.request, "Draft successfully deleted.")
        
        # Redirect to the success URL after deletion
        return HttpResponseRedirect(self.success_url)

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)

class ImageUploadView(LoginRequiredMixin, View):
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        uploaded_file = request.FILES.get('file')
        post_entry_id = request.POST.get('post_entry_id')

        # Validate file type
        if not uploaded_file:
            return JsonResponse({'error': 'No file provided.'}, status=400)
        
        mime_type, _ = mimetypes.guess_type(uploaded_file.name)
        if not mime_type or not mime_type.startswith('image/'):
            return JsonResponse({'error': 'Only image files are allowed.'}, status=400)

        # Validate dimensions or size if necessary
        try:
            get_image_dimensions(uploaded_file)
        except ValidationError:
            return JsonResponse({'error': 'Invalid image file.'}, status=400)
        
        related_post_entry = None
        if post_entry_id:
            try:
                related_post_entry = PostEntry.objects.get(pk=post_entry_id)
            except PostEntry.DoesNotExist:
                return JsonResponse({'error': 'Invalid PostEntry ID.'}, status=400)
        else:
            return JsonResponse({'error': 'Please save the post before adding images.'}, status=400)

        # Save to the model
        image_upload = ImageUpload(
            uploaded_by=request.user,
            uploaded_image=uploaded_file,
            related_post_entry=related_post_entry
        )
        image_upload.save()

        # Return the image URL to TinyMCE
        return JsonResponse({'location': image_upload.uploaded_image.url})