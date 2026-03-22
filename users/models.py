from django.db import models
from django.contrib.auth.models import User
import re


# ================= COURSE =================
class Course(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(default="No description")

    students = models.ManyToManyField(
        User,
        blank=True,
        related_name="courses"
    )

    def __str__(self):
        return self.title


# ================= LESSON =================
class Lesson(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="lessons"
    )

    title = models.CharField(max_length=200)

    # 👉 ใส่ลิงก์ Google Drive ปกติได้เลย
    video_url = models.URLField(help_text="ใส่ลิงก์ Google Drive")

    order = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.course.title} - {self.title}"

    class Meta:
        ordering = ["order"]

    # ✅ แปลงลิงก์ Google Drive → embed อัตโนมัติ
    def get_embed_url(self):
        """
        รองรับลิงก์แบบ:
        https://drive.google.com/file/d/FILE_ID/view
        """
        match = re.search(r"/d/(.*?)/", self.video_url)
        if match:
            file_id = match.group(1)
            return f"https://drive.google.com/file/d/{file_id}/preview"
        return self.video_url


# ================= PROGRESS =================
class Progress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)

    completed = models.BooleanField(default=False)
    video_time = models.FloatField(default=0)

    class Meta:
        unique_together = ("user", "lesson")

    def __str__(self):
        return f"{self.user.username} - {self.lesson.title}"
    
