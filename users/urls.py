from django.urls import path
from .views import student_login, dashboard, course_list, course_detail
from .views import mark_complete, save_progress
from . import views

urlpatterns = [
    path("", student_login),
    path("dashboard/", dashboard),
    path("courses/", course_list),
    path("course/<int:id>/", course_detail),
    path("complete/<int:lesson_id>/", mark_complete),
    path("save-progress/", save_progress),
    path("admin-dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path('admin-users/', views.admin_users_view, name="admin_users"),
    path('delete-user/<int:user_id>/', views.delete_user, name='delete_user'),
]

