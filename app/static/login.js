document.getElementById('login-form').addEventListener('submit', async function (e) {
    e.preventDefault();

    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;
    const errorEl  = document.getElementById('error-msg');

    errorEl.style.display = 'none';

    try {
        const response = await fetch('/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });

        const data = await response.json();

        if (response.ok) {
            localStorage.setItem('token', data.token);
            // Open-redirect prevention: only allow relative paths starting with '/'
            // and explicitly reject protocol-relative URLs like '//evil.com'
            const params    = new URLSearchParams(window.location.search);
            const siguiente = params.get('siguiente') || '';
            const destino   = (siguiente.startsWith('/') && !siguiente.startsWith('//'))
                ? siguiente
                : '/dashboard';
            window.location.href = destino;
        } else {
            errorEl.textContent = data.error || 'Error al iniciar sesión.';
            errorEl.style.display = 'block';
        }
    } catch {
        errorEl.textContent = 'Error de conexión. Inténtalo de nuevo.';
        errorEl.style.display = 'block';
    }
});
