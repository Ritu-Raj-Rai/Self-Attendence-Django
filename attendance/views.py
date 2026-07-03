from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.cache import never_cache
from django.db.models import Count, Q
from django.urls import reverse
import json
import calendar
from datetime import datetime, date
import math

from .models import Subject, AttendanceRecord
from .forms import SubjectForm

def get_session_key(request):
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key

def calculate_stats(subject):
    records = subject.attendance_records.all()
    present_count = records.filter(status='present').count()
    absent_count = records.filter(status='absent').count()
    holiday_count = records.filter(status='holiday').count()
    total_held = present_count + absent_count
    
    attendance_percentage = 0
    if total_held > 0:
        attendance_percentage = (present_count / total_held) * 100
        
    percentage = round(attendance_percentage, 1)
    offset = 213.6 - (213.6 * percentage) / 100
    
    return {
        'present': present_count,
        'absent': absent_count,
        'holiday': holiday_count,
        'total': total_held,
        'percentage': percentage,
        'offset': round(offset, 2),
    }

@never_cache
def dashboard(request):
    session_key = get_session_key(request)
    subjects = Subject.objects.filter(session_key=session_key)
    subject_data = []
    
    total_present = 0
    total_held = 0
    
    for subject in subjects:
        stats = calculate_stats(subject)
        total_present += stats['present']
        total_held += stats['total']
        
        percentage = stats['percentage']
        target = subject.target_percentage
        
        status_msg = ""
        status_color = ""
        
        if total_held == 0:
            status_color = "amber"
            status_msg = "No classes yet."
        elif percentage >= target:
            status_color = "green"
            if target > 0:
                can_miss = math.floor((stats['present'] * 100 / target) - stats['total'])
                status_msg = f"On track! Can safely miss {max(0, can_miss)} classes."
            else:
                status_msg = "Target is 0%."
        else:
            status_color = "red"
            if target < 100:
                needed = math.ceil( (target * stats['total'] - 100 * stats['present']) / (100 - target) )
                if needed <= 0: needed = 1
                status_msg = f"Need to attend {needed} consecutive classes."
            else:
                status_msg = "Target is 100%, impossible to reach if missed."

        subject_data.append({
            'obj': subject,
            'stats': stats,
            'status_msg': status_msg,
            'status_color': status_color,
        })
        
    overall_percentage = (total_present / total_held * 100) if total_held > 0 else 0
    
    context = {
        'subjects': subject_data,
        'overall_percentage': round(overall_percentage, 1)
    }
    return render(request, 'attendance/dashboard.html', context)

@never_cache
def subject_detail(request, subject_id, year=None, month=None):
    session_key = get_session_key(request)
    subject = get_object_or_404(Subject, id=subject_id, session_key=session_key)
    stats = calculate_stats(subject)
    
    today = date.today()
    if not year or not month:
        year = today.year
        month = today.month
    else:
        year = int(year)
        month = int(month)
        
    cal = calendar.Calendar(firstweekday=6) # Sunday=6
    month_days = cal.monthdatescalendar(year, month)
    
    start_date = month_days[0][0]
    end_date = month_days[-1][-1]
    
    records = AttendanceRecord.objects.filter(
        subject=subject, 
        date__range=[start_date, end_date]
    ).values('date', 'status')
    
    record_dict = {r['date']: r['status'] for r in records}
    
    calendar_data = []
    for week in month_days:
        week_data = []
        for d in week:
            status = record_dict.get(d, 'unmarked')
            is_current_month = (d.month == month)
            week_data.append({
                'date': d.strftime('%Y-%m-%d'),
                'day': d.day,
                'status': status,
                'is_current_month': is_current_month,
                'is_today': (d == today)
            })
        calendar_data.append(week_data)
        
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1
    
    month_name = calendar.month_name[month]
        
    context = {
        'subject': subject,
        'stats': stats,
        'calendar': calendar_data,
        'year': year,
        'month': month,
        'month_name': month_name,
        'prev_year': prev_year,
        'prev_month': prev_month,
        'next_year': next_year,
        'next_month': next_month,
        'days_of_week': ['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT'],
    }
    return render(request, 'attendance/subject_detail.html', context)

def subject_create(request):
    if request.method == 'POST':
        form = SubjectForm(request.POST)
        if form.is_valid():
            subject = form.save(commit=False)
            subject.session_key = get_session_key(request)
            subject.save()
            return redirect('dashboard')
    else:
        form = SubjectForm()
    return render(request, 'attendance/subject_form.html', {'form': form, 'title': 'Add Subject'})

def subject_update(request, pk):
    session_key = get_session_key(request)
    subject = get_object_or_404(Subject, pk=pk, session_key=session_key)
    if request.method == 'POST':
        form = SubjectForm(request.POST, instance=subject)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = SubjectForm(instance=subject)
    return render(request, 'attendance/subject_form.html', {'form': form, 'title': 'Edit Subject'})

def subject_delete(request, pk):
    session_key = get_session_key(request)
    subject = get_object_or_404(Subject, pk=pk, session_key=session_key)
    if request.method == 'POST':
        subject.delete()
        return redirect('dashboard')
    return render(request, 'attendance/subject_confirm_delete.html', {'subject': subject})

@require_POST
def toggle_attendance(request):
    try:
        data = json.loads(request.body)
        subject_id = data.get('subject_id')
        date_str = data.get('date')
        
        session_key = get_session_key(request)
        subject = get_object_or_404(Subject, id=subject_id, session_key=session_key)
        record_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        record, created = AttendanceRecord.objects.get_or_create(
            subject=subject, 
            date=record_date,
            defaults={'status': 'present'}
        )
        
        status_to_return = 'present'
        if not created:
            if record.status == 'present':
                record.status = 'absent'
                record.save()
                status_to_return = 'absent'
            elif record.status == 'absent':
                record.status = 'holiday'
                record.save()
                status_to_return = 'holiday'
            elif record.status == 'holiday':
                record.delete()
                status_to_return = 'unmarked'
                
        stats = calculate_stats(subject)
        
        return JsonResponse({
            'success': True,
            'status': status_to_return,
            'stats': stats
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
