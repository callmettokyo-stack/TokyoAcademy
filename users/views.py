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
        if "update_user" in request.POST:
            user_id = request.POST.get("user_id")
            user = get_object_or_404(User, id=user_id)
            user.first_name = request.POST.get("first_name", "")
            user.last_name = request.POST.get("last_name", "")
            user.email = request.POST.get("email", "")
            user.save()
            messages.success(request, f"อัปเดตข้อมูลของ {user.username} เรียบร้อยแล้ว!")
            return redirect('admin_users')

        else:
            username = request.POST.get("username")
            is_staff = request.POST.get("is_staff") == "on"
            
            if User.objects.filter(username=username).exists():
                messages.error(request, f"ชื่อผู้ใช้ {username} มีอยู่ในระบบแล้ว")
            else:
                password = get_random_string(length=10)
                new_user = User.objects.create_user(username=username, password=password)
                new_user.is_staff = is_staff
                new_user.save()
                messages.success(request, f"สร้างผู้ใช้ {username} สำเร็จ! รหัสผ่านคือ: {password}")
            return redirect('admin_users')

    users = User.objects.all().order_by('-id')
    return render(request, "admin_user.html", {"users": users})

@login_required
def delete_user(request, user_id):
    """ลบผู้ใช้และ Redirect กลับหน้าเดิมเสมอ"""
    if not request.user.is_staff:
        return HttpResponseForbidden("คุณไม่มีสิทธิ์ลบผู้ใช้")
    user = get_object_or_404(User, id=user_id)
    username = user.username
    user.delete()
    messages.success(request, f"ลบผู้ใช้ {username} เรียบร้อยแล้ว")
    return redirect('admin_users')

# ================= COURSE MANAGEMENT (ADMIN ONLY) =================

@login_required
def admin_courses_management(request):
    if not request.user.is_staff:
        return HttpResponseForbidden()
    
    courses = Course.objects.all().order_by('-id')
    course_data = []
    
    all_students = User.objects.filter(is_staff=False)

    for c in courses:
        first_lesson = c.lessons.first()
        video_url = first_lesson.video_url if first_lesson else ""
        enrolled_students = list(c.students.values('id', 'username'))
        enrolled_ids = [s['id'] for s in enrolled_students]

        course_data.append({
            'id': c.id,
            'title': c.title,
            'student_count': c.students.count(),
            'video_url': c.lessons.first().video_url if c.lessons.exists() else "",
            'enrolled_ids': list(c.students.values_list('id', flat=True))
        })
    
    return render(request, "courses_admin.html", {
        "courses": course_data,
        "all_students": all_students 
    })

@login_required
def create_course(request):
    """สร้างคอร์สใหม่ (รูปที่ 2)"""
    if not request.user.is_staff:
        return HttpResponseForbidden()
    
    if request.method == "POST":
        title = request.POST.get("title")
        video_url = request.POST.get("video_url")
        
        if title:
            new_course = Course.objects.create(title=title)
            if video_url:
                Lesson.objects.create(
                    course=new_course, 
                    title=f"Lesson 1", 
                    video_url=video_url
                )
            messages.success(request, f"สร้างคอร์ส {title} เรียบร้อยแล้ว")
    return redirect('admin_courses_management')

@login_required
def edit_course(request, course_id):
    if not request.user.is_staff:
        return HttpResponseForbidden()
    
    course = get_object_or_404(Course, id=course_id) 
    if request.method == "POST":
        course.title = request.POST.get("title")
        course.save()
        new_video_url = request.POST.get("video_url")
        lesson, created = Lesson.objects.get_or_create(course=course, defaults={'title': 'Main Lesson'})
        lesson.video_url = new_video_url
        lesson.save()
        student_ids = request.POST.getlist("students")
        course.students.set(student_ids)
        messages.success(request, f"อัปเดตคอร์ส {course.title} เรียบร้อยแล้ว")
        return redirect("admin_courses_management") 
    return redirect("admin_courses_management")

@login_required
def delete_course(request, course_id):
    """ลบคอร์ส (รูปที่ 4)"""
    if not request.user.is_staff:
        return HttpResponseForbidden()
    course = get_object_or_404(Course, id=course_id)
    title = course.title
    course.delete()
    messages.success(request, f"ลบคอร์ส {title} เรียบร้อยแล้ว")
    return redirect('admin_courses_management')

