from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from django.utils.crypto import get_random_string

from .models import Course, Lesson, Progress


from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from django import forms
from django.utils.crypto import get_random_string


# ================= CUSTOM FORM =================
class CustomUserCreationForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("username", "is_staff")

    def save(self, commit=True):
        user = super().save(commit=False)

        # 👉 generate password อัตโนมัติ
        password = get_random_string(8)
        user.set_password(password)
        user._generated_password = password

        if commit:
            user.save()
        return user


# ================= USER ADMIN =================
class CustomUserAdmin(UserAdmin):

    add_form = CustomUserCreationForm  # 🔥 ใช้ form ใหม่

    list_display = ("username", "is_staff", "role")
    list_filter = ("is_staff",)

    def role(self, obj):
        return "ADMIN" if obj.is_staff else "USER"
    role.short_description = "Role"

    # ใช้ default ของ Django
    fieldsets = UserAdmin.fieldsets

    # 👉 ตอนสร้าง เหลือแค่นี้
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "is_staff"),
        }),
    )

    # 👉 แสดง password หลังสร้าง
    def response_add(self, request, obj, post_url_continue=None):
        if hasattr(obj, "_generated_password"):
            role = "ADMIN" if obj.is_staff else "USER"
            self.message_user(
                request,
                f"สร้าง {role} | Username: {obj.username} | Password: {obj._generated_password}"
            )
        return super().response_add(request, obj, post_url_continue)


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

# ================= LESSON INLINE =================
class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 1
    ordering = ("order",)


# ================= COURSE ADMIN =================
@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("title", "student_count")
    search_fields = ("title",)
    filter_horizontal = ("students",)
    inlines = [LessonInline]

    def student_count(self, obj):
        return obj.students.count()
    student_count.short_description = "Students"


# ================= LESSON ADMIN =================
@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "order")
    list_filter = ("course",)
    ordering = ("course", "order")
    search_fields = ("title",)


# ================= PROGRESS ADMIN =================
@admin.register(Progress)
class ProgressAdmin(admin.ModelAdmin):
    list_display = ("user", "lesson", "completed", "video_time")
    list_filter = ("completed",)
    search_fields = ("user__username", "lesson__title")