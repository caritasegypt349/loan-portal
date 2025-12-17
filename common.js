// ملف مشترك لجميع الصفحات
function validateSession() {
    const userId = localStorage.getItem('loggedInUserId');
    if (!userId) {
        alert("الجلسة منتهية. يرجى تسجيل الدخول مرة أخرى.");
        window.location.href = "index.html";
        return false;
    }
    return true;
}

function logout() {
    if (confirm("هل تريد تسجيل الخروج؟")) {
        localStorage.clear();
        sessionStorage.clear();
        window.location.href = "index.html";
    }
}

function addLogoutButton() {
    const header = document.querySelector('h2') || document.querySelector('.container');
    if (header) {
        const logoutBtn = document.createElement('button');
        logoutBtn.textContent = 'تسجيل خروج';
        logoutBtn.id = 'globalLogoutBtn';
        logoutBtn.style.cssText = `
            position: fixed;
            top: 15px;
            left: 15px;
            background: #e74c3c;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            z-index: 1000;
        `;
        logoutBtn.onclick = logout;
        document.body.appendChild(logoutBtn);
    }
}

// استخدام في كل صفحة
window.addEventListener('DOMContentLoaded', function() {
    validateSession();
    addLogoutButton();
});