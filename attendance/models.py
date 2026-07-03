from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class Subject(models.Model):
    name = models.CharField(max_length=200)
    color = models.CharField(max_length=7, default='#0D9488', help_text="Hex color code")
    target_percentage = models.FloatField(
        default=75.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)]
    )
    session_key = models.CharField(max_length=40, db_index=True, null=True, blank=True)
    
    def __str__(self):
        return self.name

class AttendanceRecord(models.Model):
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('holiday', 'Holiday / No Class'),
    ]
    
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)

    class Meta:
        unique_together = ('subject', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"{self.subject.name} - {self.date} - {self.status}"
