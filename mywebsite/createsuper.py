import os
import django

# บรรทัดนี้สำคัญมาก ต้องตรงกับชื่อโฟลเดอร์ที่มี settings.py
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mywebsite.settings')
django.setup()

from django.contrib.auth.models import User

# กำหนด Username และ Password ที่คุณต้องการที่นี่
username = 'admin'
email = 'admin@example.com'
password = '1234' # <-- แก้รหัสผ่านที่อยากได้ตรงนี้

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, email, password)
    print(f"Superuser '{username}' created successfully!")
else:
    user = User.objects.get(username=username)
    user.set_password(password)
    user.save()
    print(f"Password for '{username}' updated successfully!")
