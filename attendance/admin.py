from django.contrib import admin
from .models import Subject, AttendanceRecord

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'target_percentage')
    search_fields = ('name',)

@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ('subject', 'date', 'status')
    list_filter = ('subject', 'status', 'date')
    date_hierarchy = 'date'
