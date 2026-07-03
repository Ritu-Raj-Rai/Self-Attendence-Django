document.addEventListener('DOMContentLoaded', () => {
    document.addEventListener('click', async function(e) {
        // 1. Calendar Nav clicks (AJAX transition)
        const navLink = e.target.closest('.cal-nav');
        if (navLink) {
            e.preventDefault();
            const url = navLink.getAttribute('href');
            if (!url) return;
            
            try {
                const container = document.querySelector('.calendar-container');
                if (container) container.style.opacity = '0.5';
                
                const response = await fetch(url);
                const html = await response.text();
                
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, 'text/html');
                const newContainer = doc.querySelector('.calendar-container');
                
                if (newContainer && container) {
                    container.outerHTML = newContainer.outerHTML;
                    window.history.pushState({}, '', url);
                }
            } catch (err) {
                console.error('Error navigating calendar:', err);
                window.location.href = url;
            }
            return;
        }

        // 2. Calendar Cell clicks
        const cell = e.target.closest('.cal-cell');
        if (cell) {
            const dateStr = cell.dataset.date;
            const subjectId = cell.dataset.subject;
            
            if (!dateStr || !subjectId) return;

            // Prevent multiple rapid clicks on the same day before the previous request finishes
            if (cell.dataset.loading === 'true') return;
            cell.dataset.loading = 'true';

            const csrfTokenElement = document.querySelector('[name=csrfmiddlewaretoken]');
            if (!csrfTokenElement) {
                cell.dataset.loading = 'false';
                return;
            }
            const csrfToken = csrfTokenElement.value;
            
            // Optimistic UI update
            const statuses = ['unmarked', 'present', 'absent', 'holiday'];
            let currentStatus = 'unmarked';
            for (const s of statuses) {
                if (cell.classList.contains(`status-${s}`)) {
                    currentStatus = s;
                    break;
                }
            }
            
            let nextStatus = 'present';
            if (currentStatus === 'present') {
                nextStatus = 'absent';
            } else if (currentStatus === 'absent') {
                nextStatus = 'holiday';
            } else if (currentStatus === 'holiday') {
                nextStatus = 'unmarked';
            }
            
            const revertStatus = () => {
                cell.classList.remove(`status-${nextStatus}`);
                cell.classList.add(`status-${currentStatus}`);
            };
            
            cell.classList.remove(`status-${currentStatus}`);
            cell.classList.add(`status-${nextStatus}`);
            
            try {
                const response = await fetch('/api/toggle-attendance/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    },
                    body: JSON.stringify({
                        subject_id: subjectId,
                        date: dateStr
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    // Update to match server response exactly, just in case
                    cell.classList.remove(`status-${nextStatus}`);
                    cell.classList.add(`status-${data.status}`);
                    
                    if (data.stats) {
                        const elPresent = document.getElementById('stats-present');
                        const elAbsent = document.getElementById('stats-absent');
                        const elHoliday = document.getElementById('stats-holiday');
                        const elPercentage = document.getElementById('stats-percentage');
                        
                        if (elPresent) elPresent.textContent = `Present : ${data.stats.present}`;
                        if (elAbsent) elAbsent.textContent = `Absent : ${data.stats.absent}`;
                        if (elHoliday) elHoliday.textContent = `Holiday : ${data.stats.holiday}`;
                        if (elPercentage) elPercentage.textContent = `Percentage : ${Math.round(data.stats.percentage)}%`;
                    }
                } else {
                    revertStatus();
                    alert('Failed to update attendance.');
                }
            } catch (error) {
                console.error('Error toggling attendance:', error);
                revertStatus();
                alert('An error occurred.');
            } finally {
                cell.dataset.loading = 'false';
            }
        }
    });
});

window.toggleDropdown = function(button) {
    const dropdown = button.closest('.dropdown');
    const menu = dropdown.querySelector('.dropdown-menu');
    
    document.querySelectorAll('.dropdown-menu').forEach(m => {
        if (m !== menu) {
            m.classList.remove('show');
        }
    });
    
    menu.classList.toggle('show');
};

document.addEventListener('click', (e) => {
    if (!e.target.closest('.dropdown')) {
        document.querySelectorAll('.dropdown-menu').forEach(m => {
            m.classList.remove('show');
        });
    }
});

// Force refresh when page is loaded from cache (e.g. back button)
window.addEventListener('pageshow', (event) => {
    if (event.persisted) {
        window.location.reload();
    }
});
