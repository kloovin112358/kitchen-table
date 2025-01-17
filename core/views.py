from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView
from django.urls import reverse_lazy
from .models import PostEntry, ImageUpload, Favorite, PostCategory
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
from django.db.models import Prefetch, Q, OuterRef, Exists, Min, Max
from urllib.parse import urlparse
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime
from django.db.models.functions import TruncDate

class HomeView(LoginRequiredMixin, ListView):
    model = PostEntry  # Replace with your model
    template_name = 'home.html'  # Path to your template
    context_object_name = 'posts'  # Name to access objects in the template
    paginate_by = 12  # Number of items per page
    login_url = reverse_lazy('log-in')  # Redirect to login if not authenticated

    def get_queryset(self):
        # Base queryset
        queryset = PostEntry.objects.filter(status='Live')

        favorite_status = Favorite.objects.filter(
            user=self.request.user, 
            post_entry=OuterRef('pk')
        )

        # Handle query parameters with snake_case
        favorites_only = self.request.GET.get('favorites_only', 'false').lower() == 'on'
        sort_by = self.request.GET.get('sort_by', 'latest')  # Default to 'new'
        search = self.request.GET.get('search', '').strip()  # Get the search query
        category = self.request.GET.get('category', '')
        
        # Filter for favorites only if specified
        if favorites_only:
            queryset = queryset.filter(Exists(favorite_status))
        
        # Filter by search string (title or tags)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(post_body__icontains=search) | Q(tags__name__icontains=search)
            ).distinct()

        # Apply sorting
        if sort_by == 'latest':
            queryset = queryset.order_by('-created_at')  # Newest first
        elif sort_by == 'oldest':
            queryset = queryset.order_by('created_at')  # Oldest first

        # Prefetch related images
        # image_prefetch = Prefetch(
        #     'imageupload_set',  # Reverse relation from PostEntry to ImageUpload
        #     queryset=ImageUpload.objects.order_by('uploaded_at'),  # Oldest image first
        #     to_attr='prefetched_images'  # Attribute to store prefetched images
        # )
        queryset = queryset.annotate(is_favorite=Exists(favorite_status))

        if category:
            queryset = queryset.filter(category=category)

        return queryset
        return queryset.prefetch_related(image_prefetch)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add query parameters to the context for template usage
        context['favorites_only'] = self.request.GET.get('favorites_only', 'false')
        context['sort_by'] = self.request.GET.get('sort_by', 'latest')
        context['search'] = self.request.GET.get('search', '')
        context['selected_category'] = self.request.GET.get('category', '')
        context['categories'] = PostCategory.objects.all()
        return context

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
def MediaUpload(request):
    if request.method == 'POST':
        uploaded_files = request.FILES.getlist('images')
        captions = request.POST.getlist('captions')
        image_tags = request.POST.getlist('image_tags')
        dates_taken = request.POST.getlist('dates_taken')
        common_tags = request.POST.get('common_tags', '')
        
        try:
            count = 0
            common_tag_list = [tag.strip() for tag in common_tags.split(',') if tag.strip()]
            
            for i, image in enumerate(uploaded_files):
                # Parse date taken
                date_taken = None
                if i < len(dates_taken) and dates_taken[i]:
                    try:
                        date_taken = timezone.datetime.strptime(dates_taken[i], '%Y-%m-%d').date()
                    except (ValueError, TypeError):
                        date_taken = timezone.now().date()
                else:
                    date_taken = timezone.now().date()
                
                # Create image
                upload = ImageUpload.objects.create(
                    uploaded_by=request.user,
                    uploaded_image=image,
                    caption=captions[i] if i < len(captions) else '',
                    date_taken=date_taken
                )
                
                # Add common tags
                for tag in common_tag_list:
                    upload.tags.add(tag)
                
                # Add image-specific tags
                if i < len(image_tags):
                    image_specific_tags = [tag.strip() for tag in image_tags[i].split(',') if tag.strip()]
                    for tag in image_specific_tags:
                        upload.tags.add(tag)
                
                count += 1
            
            messages.success(request, f"Successfully uploaded {count} image{'s' if count != 1 else ''}!")
            return JsonResponse({'status': 'success', 'redirect': reverse('gallery')})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
            
    return render(request, "mediaupload.html")

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
    
    # Get favorite posts
    total_favorite_posts = Favorite.objects.filter(
        user=user,
        post_entry__isnull=False
    ).count()
    
    favorite_posts = Favorite.objects.filter(
        user=user,
        post_entry__isnull=False
    ).select_related('post_entry')[:3]
    
    remaining_favorite_posts = max(0, total_favorite_posts - 3)

    # Get favorite images
    total_favorite_images = Favorite.objects.filter(
        user=user,
        image_upload__isnull=False
    ).count()
    
    favorite_images = Favorite.objects.filter(
        user=user,
        image_upload__isnull=False
    ).order_by('-id').select_related('image_upload')[:3]
    
    remaining_favorite_images = max(0, total_favorite_images - 3)

    # Get gallery uploads (existing code)
    total_images = ImageUpload.objects.filter(
        uploaded_by=user,
    ).count()
    
    recent_images = ImageUpload.objects.filter(
        uploaded_by=user,
    ).order_by('-uploaded_at')[:3]

    remaining_images = max(0, total_images - 3)

    return render(request, "myaccount.html", {
        "form": form, 
        "post_drafts": PostEntry.objects.filter(author=user, status="Draft").order_by("-last_updated"),
        "posts": PostEntry.objects.filter(author=user, status="Live"),
        "favorite_posts": favorite_posts,
        "remaining_favorite_posts": remaining_favorite_posts,
        "favorite_images": favorite_images,
        "remaining_favorite_images": remaining_favorite_images,
        "active_user_timezone": get_current_timezone_name(),
        "recent_images": recent_images,
        "remaining_image_count": remaining_images,
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

class GalleryTemplateView(LoginRequiredMixin, TemplateView):
    template_name = 'gallery.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['users'] = CustomUser.objects.all()
        
        # Get min and max dates from date_taken instead of uploaded_at
        date_range = ImageUpload.objects.aggregate(
            min_date=Min('date_taken'),
            max_date=Max('date_taken')
        )
        
        context['min_date'] = date_range['min_date']
        context['max_date'] = date_range['max_date']
        return context

class GalleryAjaxView(LoginRequiredMixin, View):
    def get(self, request):
        # Base queryset
        queryset = ImageUpload.objects.filter(
            Q(related_post_entry__isnull=True) | 
            Q(related_post_entry__status="Live")
        )

        favorite_status = Favorite.objects.filter(
            user=request.user, 
            image_upload=OuterRef('pk')
        )

        # Get query parameters
        page = int(request.GET.get('page', 1))
        search = request.GET.get('search', '').strip()
        favorites_only = request.GET.get('favorites_only', 'false').lower() == 'on'
        sort_by = request.GET.get('sort_by', 'latest')
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')

        # Apply favorites filter
        if favorites_only:
            queryset = queryset.filter(Exists(favorite_status))

        # Apply date range filter if provided
        if start_date and end_date:
            try:
                start_date = timezone.datetime.strptime(start_date, '%Y-%m-%d').date()
                end_date = timezone.datetime.strptime(end_date, '%Y-%m-%d').date()
                queryset = queryset.filter(date_taken__range=[start_date, end_date])
            except ValueError:
                pass

        # Apply search filter
        if search:
            queryset = queryset.filter(
                Q(caption__icontains=search) |
                Q(tags__name__icontains=search)
            ).distinct()

        # Apply sorting
        if sort_by == 'oldest':
            queryset = queryset.order_by('date_taken')
        else:  # latest
            queryset = queryset.order_by('-date_taken')

        # Add users filter
        users = request.GET.get('users')
        if users:
            user_ids = [int(uid) for uid in users.split(',')]
            queryset = queryset.filter(uploaded_by_id__in=user_ids)

        queryset = queryset.annotate(is_favorite=Exists(favorite_status))

        # Paginate the results
        paginator = Paginator(queryset, 10)
        page_obj = paginator.get_page(page)

        # Prepare the data for JSON response
        photos_data = []
        for photo in page_obj:
            photos_data.append({
                'id': photo.id,
                'image_url': photo.uploaded_image.url,
                'caption': photo.caption,
                'uploaded_by': photo.uploaded_by.get_full_name(),
                'uploaded_by_id': photo.uploaded_by.id,
                'date': photo.date_taken.strftime('%b %d, %Y'),
                'is_favorite': photo.is_favorite,
                'tags': [{'name': tag.name} for tag in photo.tags.all()],
                'related_post_entry': {
                    'id': photo.related_post_entry.id,
                    'url': reverse('post-view', kwargs={'pk': photo.related_post_entry.id})
                } if photo.related_post_entry else None
            })

        return JsonResponse({
            'photos': photos_data,
            'has_next': page_obj.has_next(),
            'next_page': page + 1 if page_obj.has_next() else None,
        })

def PasswordReset(request):
    return render(request, "passwordreset.html")

class PostEntryBaseView:
    def form_valid(self, form):
        form.instance.author = self.request.user  # Set the logged-in user as the author
        form.instance.last_updated = now()
        if "save_as_draft" in self.request.POST:
            # Set status to "Draft" when Save as Draft button is clicked
            form.instance.status = "Draft"
            messages.success(self.request, "Your changes have been saved. Feel free to continue editing.")
        elif "submit" in self.request.POST:
            # Set status to "Live" when Submit button is clicked
            if form.instance.id and form.instance.status == "Live":
                messages.success(self.request, "Sweet! Your post has been updated.")
            else:
                form.instance.status = "Live"
                form.instance.created_at = now()
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
    
    def get(self, request, *args, **kwargs):
        # Call parent get() first to set self.object
        response = super().get(request, *args, **kwargs)
        # Print post body of the instance being updated
        print(f"Post body for post {self.object.id}:")
        print(self.object.post_body)
        return response

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

@login_required
def ViewPost(request, pk):
    post = get_object_or_404(PostEntry, pk=pk)
    if request.method == "POST":
        existingFavoriteEntry = Favorite.objects.filter(post_entry=post, user=request.user).first()
        if not existingFavoriteEntry:
            newFavorite = Favorite(post_entry=post, user=request.user)
            newFavorite.save()
            messages.success(request, "Nice! You've added this post to your favorites.")
        else:
            existingFavoriteEntry.delete()
            messages.info(request, "This post has been removed from your favorites.")
        return redirect("post-view", pk=pk)
    else:
        referrer = request.META.get('HTTP_REFERER', '')
        home_url = reverse('home')  # Replace 'home' with the actual name of your URL pattern
        referrer_path = urlparse(referrer).path
        if referrer_path == home_url:
            referrer_link = referrer
        else:
            referrer_link = None
        return render(request, "postview.html", {
            "post": post, 
            "referrer_link": referrer_link,
            "is_favorite": Favorite.objects.filter(post_entry=post, user=request.user).exists()
        })

class ImageDeleteView(LoginRequiredMixin, View):
    def post(self, request, image_id):
        try:
            image = ImageUpload.objects.get(id=image_id, uploaded_by=request.user)
            image.delete()
            return JsonResponse({'status': 'success'})
        except ImageUpload.DoesNotExist:
            return JsonResponse({'error': 'Image not found or permission denied'}, status=404)

class ImageFavoriteView(LoginRequiredMixin, View):
    def post(self, request, image_id):
        try:
            image = ImageUpload.objects.get(id=image_id)
            favorite = Favorite.objects.filter(
                user=request.user,
                image_upload=image
            ).first()

            if favorite:
                favorite.delete()
                is_favorite = False
            else:
                Favorite.objects.create(
                    user=request.user,
                    image_upload=image
                )
                is_favorite = True

            return JsonResponse({
                'status': 'success',
                'is_favorite': is_favorite
            })
        except ImageUpload.DoesNotExist:
            return JsonResponse({
                'error': 'Image not found'
            }, status=404)