import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mywebsite.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

username = os.environ.get("DJANGO_SUPERUSER_USERNAME")
email = os.environ.get("DJANGO_SUPERUSER_EMAIL")
password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")

if username and password:
    user, created = User.objects.get_or_create(username=username)
    if created:
        print("Creating superuser...")
    else:
        print("Superuser exists — updating password...")
    
    user.email = email or ""
    user.is_staff = True
    user.is_superuser = True
    user.set_password(password)  # Always sync password from env var
    user.save()
    print("Done!")
else:
    print("No credentials found in environment variables")