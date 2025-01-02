from django.core.management.base import BaseCommand
from core.models import PostCategory, SecretSignUpCode
from django.contrib.auth import get_user_model
import random
from wonderwords import RandomWord

User = get_user_model()

class Command(BaseCommand):
    help = 'On database/server startup, creates required database entries.'

    def handle(self, *args, **kwargs):
        # Create categories if they don't exist
        category1, created1 = PostCategory.objects.get_or_create(category="Wiki")
        category2, created2 = PostCategory.objects.get_or_create(category="Blog Post")
        
        # Provide feedback on category creation
        if created1:
            self.stdout.write("Category 'Wiki' created.")
        else:
            self.stdout.write("Category 'Wiki' already exists.")

        if created2:
            self.stdout.write("Category 'Blog Post' created.")
        else:
            self.stdout.write("Category 'Blog Post' already exists.")

        # Create SecretSignUpCode if none exists
        if not SecretSignUpCode.objects.exists():
            signUpCode = SecretSignUpCode()
            
            # Initialize RandomWord
            rw = RandomWord()
            
            # Generate a passphrase with 5 random words
            passphrase = ' '.join(rw.word() for _ in range(5))
            signUpCode.code = passphrase
            
            signUpCode.save()
            self.stdout.write("Secret Passphrase created.")
        else:
            self.stdout.write("Secret Code exists in the database. Skipping.")