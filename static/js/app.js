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

            const csrfTokenElement = document.querySelector('[name=csrfmiddlewaretoken]');
            if (!csrfTokenElement) return;
            const csrfToken = csrfTokenElement.value;
            
            try {
                cell.style.opacity = '0.7';

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
                    cell.className = cell.className.replace(/status-\w+/, `status-${data.status}`);
                    
                    if (data.stats) {
                        const statBoxes = document.querySelectorAll('.stat-box .stat-number');
                        if (statBoxes.length >= 4) {
                            statBoxes[0].textContent = `${data.stats.percentage}%`;
                            statBoxes[1].textContent = data.stats.present;
                            statBoxes[2].textContent = data.stats.absent;
                            statBoxes[3].textContent = data.stats.total;
                        }
                    }
                } else {
                    alert('Failed to update attendance.');
                }
            } catch (error) {
                console.error('Error toggling attendance:', error);
                alert('An error occurred.');
            } finally {
                cell.style.opacity = '1';
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
