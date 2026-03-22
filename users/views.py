from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from .models import Course, Progress, Lesson
from django.contrib.auth.models import User
from django import forms 
from django.utils.crypto import get_random_string 
from django.contrib import messages 

# ================= HELPER =================
def user_has_access(user, course):
    return course.students.filter(id=user.id).exists()

# 🔒 Decorator: ให้เฉพาะ USER เข้า (กัน admin)
def user_only(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.is_staff:
            return HttpResponseForbidden("Admin ไม่สามารถเข้าใช้งานหน้านี้ได้")
        return view_func(request, *args, **kwargs)
    return wrapper

# ================= LOGIN =================
def student_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if user.is_staff:
                return redirect("/admin-dashboard/")
            else:
                return redirect("/dashboard/")
    return render(request, "login.html")

# ================= DASHBOARD & COURSE LIST =================
@login_required
@user_only
def dashboard(request):
    courses = Course.objects.filter(students=request.user)
    in_progress = Progress.objects.filter(
        user=request.user,
        completed=False
    ).values_list('lesson__course', flat=True)
    return render(request, "dashboard.html", {
        "courses": courses,
        "in_progress": in_progress
    })

@login_required
@user_only
def course_list(request):
    """ฟังก์ชันที่เคยหายไป: แสดงรายการคอร์สทั้งหมดของผู้เรียน"""
    courses = Course.objects.filter(students=request.user)
    return render(request, 'courses/list.html', {'courses': courses})

# ================= COURSE DETAIL & PROGRESS =================
@login_required
@user_only
def course_detail(request, id):
    course = get_object_or_404(Course, id=id)
    if not user_has_access(request.user, course):
        return HttpResponseForbidden("คุณไม่มีสิทธิ์เข้าถึงคอร์สนี้")
    
    lessons = course.lessons.all()
    total_lessons = lessons.count()
    completed_lessons_count = Progress.objects.filter(
        user=request.user, completed=True, lesson__in=lessons
    ).count()
    
    percent = int((completed_lessons_count / total_lessons) * 100) if total_lessons > 0 else 0
    
    return render(request, "course_detail.html", {
        "course": course,
        "lessons": lessons,
        "completed_lessons": Progress.objects.filter(user=request.user, completed=True).values_list('lesson_id', flat=True),
        "percent": percent
    })

@login_required
@user_only
def mark_complete(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    if not user_has_access(request.user, lesson.course):
        return HttpResponseForbidden("ไม่มีสิทธิ์")
    progress, created = Progress.objects.get_or_create(user=request.user, lesson=lesson)
    progress.completed = True
    progress.save()
    return redirect(f"/course/{lesson.course.id}/")

@login_required
@user_only
def save_progress(request):
    if request.method == "POST":
        lesson_id = request.POST.get("lesson_id")
        time = request.POST.get("time")
        lesson = get_object_or_404(Lesson, id=lesson_id)
        if not user_has_access(request.user, lesson.course):
            return JsonResponse({"status": "forbidden"}, status=403)
        progress, created = Progress.objects.get_or_create(user=request.user, lesson=lesson)
        progress.video_time = time
        progress.save()
        return JsonResponse({"status": "ok"})
    return JsonResponse({"status": "invalid"}, status=400)

# ================= ADMIN DASHBOARD =================
@login_required
def admin_dashboard(request):
    if not request.user.is_staff:
        return HttpResponseForbidden("คุณไม่มีสิทธิ์")
    return render(request, "admin.html", {
        "users": User.objects.all(),
        "courses": Course.objects.all(),
        "lessons": Lesson.objects.all(),
        "progresses": Progress.objects.all()
    })

# ================= USER MANAGEMENT (FIXED) =================

@login_required
def admin_users_view(request):
    """ฟังก์ชันเดียวจัดการ User: แสดงรายการ, เพิ่มผู้ใช้, แก้ไขผู้ใช้"""
    if not request.user.is_staff:
        return HttpResponseForbidden("คุณไม่มีสิทธิ์")

    if request.method == "POST":
        # กรณี A: อัปเดตข้อมูล (Edit User)
        if "update_user" in request.POST:
            user_id = request.POST.get("user_id")
            user = get_object_or_404(User, id=user_id)
            user.first_name = request.POST.get("first_name", "")
            user.last_name = request.POST.get("last_name", "")
            user.email = request.POST.get("email", "")
            user.save()
            messages.success(request, f"อัปเดตข้อมูลของ {user.username} เรียบร้อยแล้ว!")
            return redirect('admin_users')

        # กรณี B: สร้างผู้ใช้ใหม่ (Add User)
        else:
            username = request.POST.get("username")
            is_staff = request.POST.get("is_staff") == "on"
            
            if User.objects.filter(username=username).exists():
                messages.error(request, f"ชื่อผู้ใช้ {username} มีอยู่ในระบบแล้ว")
            else:
                # ✅ แก้ไข: เรียกผ่าน User.objects (UserManager)
                password = get_random_string(length=10)
                new_user = User.objects.create_user(username=username, password=password)
                new_user.is_staff = is_staff
                new_user.save()
                messages.success(request, f"สร้างผู้ใช้ {username} สำเร็จ! รหัสผ่านคือ: {password}")
            return redirect('admin_users')

    # แสดงผลหน้ารายการ
    users = User.objects.all().order_by('-id')
    return render(request, "admin_user.html", {"users": users})

@login_required
def delete_user(request, user_id):
    """ลบผู้ใช้และ Redirect กลับหน้าเดิมเสมอ"""
    # 1. เช็คสิทธิ์ (ต้องเป็น Staff เท่านั้น)
    if not request.user.is_staff:
        return HttpResponseForbidden("คุณไม่มีสิทธิ์ลบผู้ใช้")

    # 2. ดึงข้อมูล User
    user = get_object_or_404(User, id=user_id)
    username = user.username

    # 3. ทำการลบ
    user.delete()
    
    # 4. แจ้งเตือน
    messages.success(request, f"ลบผู้ใช้ {username} เรียบร้อยแล้ว")
    
    # 5. สำคัญมาก: ต้องมี Return Redirect ตรงนี้!
    return redirect('admin_users')

