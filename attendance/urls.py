from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('subject/add/', views.subject_create, name='subject_create'),
    path('subject/<int:pk>/edit/', views.subject_update, name='subject_update'),
    path('subject/<int:pk>/delete/', views.subject_delete, name='subject_delete'),
    path('subject/<int:subject_id>/', views.subject_detail, name='subject_detail'),
    path('subject/<int:subject_id>/<int:year>/<int:month>/', views.subject_detail, name='subject_detail_month'),
    path('api/toggle-attendance/', views.toggle_attendance, name='toggle_attendance'),
]
