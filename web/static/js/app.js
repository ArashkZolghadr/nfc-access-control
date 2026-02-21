const API_BASE = '/api';

const persianRoles = {
    'super_admin': 'مدیر ارشد',
    'admin': 'مدیر سیستم',
    'manager': 'مدیر',
    'employee': 'کارمند',
    'visitor': 'بازدیدکننده',
    'contractor': 'پیمانکار',
    'security': 'نگهبان',
    'guest': 'مهمان'
};

const persianStatus = {
    'granted': 'دسترسی مجاز',
    'denied': 'دسترسی رد شده',
    'expired': 'کارت منقضی',
    'blacklisted': 'لیست سیاه',
    'inactive': 'غیرفعال',
    'invalid_time': 'زمان نامعتبر',
    'invalid_zone': 'زون نامعتبر',
    'invalid_card': 'کارت نامعتبر'
};

function updateTime() {
    const now = new Date();
    const options = {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    };
    document.getElementById('currentTime').textContent = now.toLocaleDateString('fa-IR', options);
}

function navigateToSection(sectionId) {
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    document.querySelectorAll('.content-section').forEach(section => {
        section.classList.remove('active');
    });
    
    const activeNav = document.querySelector(`[data-section="${sectionId}"]`);
    const activeSection = document.getElementById(sectionId);
    
    if (activeNav) activeNav.classList.add('active');
    if (activeSection) activeSection.classList.add('active');
    
    const titles = {
        'dashboard': 'داشبورد',
        'logs': 'لاگ‌های دسترسی',
        'users': 'کاربران',
        'zones': 'زون‌ها',
        'simulator': 'شبیه‌ساز NFC'
    };
    document.querySelector('.header-title h1').textContent = titles[sectionId] || 'داشبورد';
}

async function fetchAPI(endpoint) {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`);
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        return null;
    }
}

async function loadDashboard() {
    const statusData = await fetchAPI('/status');
    const usersData = await fetchAPI('/users');
    const logsData = await fetchAPI('/logs?limit=100');
    
    const totalUsers = usersData?.success ? usersData.count : 0;
    document.getElementById('totalUsers').textContent = totalUsers.toLocaleString('fa-IR');
    
    if (logsData?.success) {
        const today = new Date().toDateString();
        const todayLogs = logsData.data.filter(log => {
            const logDate = new Date(log.timestamp).toDateString();
            return logDate === today;
        });
        document.getElementById('todayLogs').textContent = todayLogs.length.toLocaleString('fa-IR');
        
        const successCount = logsData.data.filter(log => log.status === 'granted').length;
        const successRate = logsData.data.length > 0 ? Math.round((successCount / logsData.data.length) * 100) : 0;
        document.getElementById('successRate').textContent = successRate + '%';
        
        renderRecentLogs(logsData.data.slice(0, 5));
    }
    
    const zonesData = await fetchAPI('/zones');
    const totalZones = zonesData?.success ? zonesData.count : 1;
    document.getElementById('totalZones').textContent = totalZones.toLocaleString('fa-IR');
}

async function loadLogs() {
    const limit = document.getElementById('logsLimit')?.value || 10;
    const logsData = await fetchAPI(`/logs?limit=${limit}`);
    
    const tbody = document.getElementById('allLogsBody');
    if (!tbody) return;
    
    if (!logsData?.success || logsData.data.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="loading-cell">
                    <i class="fas fa-inbox"></i>
                    هیچ لاگی یافت نشد
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = logsData.data.map((log, index) => `
        <tr>
            <td>${(index + 1).toLocaleString('fa-IR')}</td>
            <td>${formatDate(log.timestamp)}</td>
            <td>${log.user_id ? `کاربر #${log.user_id}` : 'ناشناس'}</td>
            <td>زون #${log.zone_id || '-'}</td>
            <td>
                <span class="status-badge ${log.status === 'granted' ? 'success' : 'danger'}">
                    <i class="fas fa-${log.status === 'granted' ? 'check' : 'times'}-circle"></i>
                    ${persianStatus[log.status] || log.status}
                </span>
            </td>
            <td>${log.reason || '-'}</td>
            <td>${log.device_id || '-'}</td>
        </tr>
    `).join('');
}

function renderRecentLogs(logs) {
    const tbody = document.getElementById('recentLogsBody');
    if (!tbody) return;
    
    if (!logs || logs.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="loading-cell">
                    <i class="fas fa-inbox"></i>
                    هیچ لاگی یافت نشد
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = logs.map(log => `
        <tr>
            <td>${formatDate(log.timestamp)}</td>
            <td>${log.user_id ? `کاربر #${log.user_id}` : 'ناشناس'}</td>
            <td>زون #${log.zone_id || '-'}</td>
            <td>
                <span class="status-badge ${log.status === 'granted' ? 'success' : 'danger'}">
                    <i class="fas fa-${log.status === 'granted' ? 'check' : 'times'}-circle"></i>
                    ${persianStatus[log.status] || log.status}
                </span>
            </td>
            <td>${log.device_id || '-'}</td>
        </tr>
    `).join('');
}

async function loadUsers() {
    const usersData = await fetchAPI('/users');
    const grid = document.getElementById('usersGrid');
    if (!grid) return;
    
    if (!usersData?.success || usersData.data.length === 0) {
        grid.innerHTML = `
            <div class="loading-state">
                <i class="fas fa-users"></i>
                <span>هیچ کاربری یافت نشد</span>
            </div>
        `;
        return;
    }
    
    grid.innerHTML = usersData.data.map(user => `
        <div class="user-card">
            <div class="user-avatar">
                ${user.first_name?.charAt(0) || 'U'}
            </div>
            <div class="user-name">${user.full_name || 'نامشخص'}</div>
            <div class="user-email">${user.email || '-'}</div>
            <div class="user-meta">
                <span class="user-role">${persianRoles[user.role] || user.role}</span>
                <span class="status-badge ${user.is_active ? 'success' : 'danger'}">
                    ${user.is_active ? 'فعال' : 'غیرفعال'}
                </span>
            </div>
        </div>
    `).join('');
}

async function loadZones() {
    const zonesData = await fetchAPI('/zones');
    const grid = document.getElementById('zonesGrid');
    if (!grid) return;
    
    if (!zonesData?.success || zonesData.data.length === 0) {
        grid.innerHTML = `
            <div class="loading-state">
                <i class="fas fa-building"></i>
                <span>هیچ زونی یافت نشد</span>
            </div>
        `;
        return;
    }
    
    grid.innerHTML = zonesData.data.map(zone => `
        <div class="zone-card">
            <div class="zone-header">
                <div class="zone-name">${zone.name}</div>
                <span class="zone-badge ${zone.is_active ? 'active' : 'inactive'}">
                    ${zone.is_active ? 'فعال' : 'غیرفعال'}
                </span>
            </div>
            <div class="zone-info">
                ${zone.code ? `<div class="zone-detail"><i class="fas fa-code"></i> ${zone.code}</div>` : ''}
                ${zone.description ? `<div class="zone-detail"><i class="fas fa-info-circle"></i> ${zone.description}</div>` : ''}
                <div class="zone-detail">
                    <i class="fas fa-shield-alt"></i>
                    سطح امنیت: ${zone.security_level}
                </div>
                <div class="security-level">
                    ${[1,2,3,4,5,6,7,8,9,10].map(i => 
                        `<div class="security-dot ${i <= zone.security_level ? 'filled' : ''}"></div>`
                    ).join('')}
                </div>
            </div>
        </div>
    `).join('');
    
    const zoneSelect = document.getElementById('simZoneSelect');
    if (zoneSelect) {
        zoneSelect.innerHTML = zonesData.data.map(zone => 
            `<option value="${zone.id}">${zone.name}</option>`
        ).join('');
    }
}

async function simulateTap() {
    const uid = document.getElementById('cardUid').value.trim();
    const zoneId = document.getElementById('simZoneSelect')?.value || 1;
    
    if (!uid) {
        showSimResult(false, 'لطفا UID کارت را وارد کنید');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/simulate-tap`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ uid, zone_id: parseInt(zoneId) })
        });
        
        const result = await response.json();
        showSimResult(result.success, result.message || result.user || 'نتیجه نامشخص');
    } catch (error) {
        showSimResult(false, 'خطا در ارتباط با سرور');
    }
}

function quickSimulate(uid) {
    document.getElementById('cardUid').value = uid;
    simulateTap();
}

function showSimResult(success, message) {
    const resultDiv = document.getElementById('simResult');
    const resultIcon = document.getElementById('resultIcon');
    const resultTitle = document.getElementById('resultTitle');
    const resultMessage = document.getElementById('resultMessage');
    
    resultDiv.classList.remove('hidden', 'success', 'error');
    resultDiv.classList.add(success ? 'success' : 'error');
    
    resultIcon.innerHTML = `<i class="fas fa-${success ? 'check' : 'times'}"></i>`;
    resultTitle.textContent = success ? 'دسترسی مجاز' : 'دسترسی رد شده';
    resultMessage.textContent = message;
    
    resultDiv.style.display = 'flex';
}

function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('fa-IR', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

async function refreshData() {
    const activeSection = document.querySelector('.content-section.active');
    if (!activeSection) return;
    
    const sectionId = activeSection.id;
    
    switch (sectionId) {
        case 'dashboard':
            await loadDashboard();
            break;
        case 'logs':
            await loadLogs();
            break;
        case 'users':
            await loadUsers();
            break;
        case 'zones':
            await loadZones();
            break;
    }
}

document.addEventListener('DOMContentLoaded', function() {
    updateTime();
    setInterval(updateTime, 1000);
    
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            const section = this.getAttribute('data-section');
            navigateToSection(section);
        });
    });
    
    const initialSection = 'dashboard';
    navigateToSection(initialSection);
    loadDashboard();
    loadUsers();
    loadZones();
    
    document.getElementById('cardUid').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            simulateTap();
        }
    });
});
