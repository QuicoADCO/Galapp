document.getElementById('register-form').addEventListener('submit', async function (e) {
    e.preventDefault();

    const username = document.getElementById('username').value.trim();
    const email    = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;
    const confirm  = document.getElementById('confirm_password').value;
    const msgEl    = document.getElementById('msg');

    msgEl.style.display = 'none';
    msgEl.className = 'msg';

    if (password !== confirm) {
        msgEl.textContent = 'Passwords do not match.';
        msgEl.classList.add('error');
        msgEl.style.display = 'block';
        return;
    }

    try {
        const response = await fetch('/auth/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, email, password })
        });

        const data = await response.json();

        if (response.ok) {
            msgEl.textContent = 'Account created! Redirecting to login...';
            msgEl.classList.add('success');
            msgEl.style.display = 'block';
            setTimeout(() => window.location.href = '/login', 1500);
        } else {
            msgEl.textContent = data.error || 'Registration failed.';
            msgEl.classList.add('error');
            msgEl.style.display = 'block';
        }
    } catch (err) {
        msgEl.textContent = 'Connection error. Try again.';
        msgEl.classList.add('error');
        msgEl.style.display = 'block';
    }
});
