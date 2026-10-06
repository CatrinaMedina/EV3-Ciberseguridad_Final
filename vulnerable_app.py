from flask import Flask, request, render_template_string, session, redirect, url_for, Response
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
import sqlite3
import os
import hashlib

try:
    from werkzeug.serving import WSGIRequestHandler
    WSGIRequestHandler.server_version = "WebServer"
    WSGIRequestHandler.sys_version = ""
except Exception:
    pass


app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", os.urandom(24))


# MÉTRICA PROMETHEUS:
# Cuenta la cantidad total de peticiones HTTP recibidas por la aplicación Flask.
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Cantidad total de peticiones HTTP recibidas por la aplicación Flask',
    ['method', 'endpoint', 'status']
)


def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


@app.after_request
def set_security_headers(response):
    # CORRECCIÓN OWASP ZAP: Content Security Policy Header Not Set
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self'; "
        "img-src 'self' data:; "
        "font-src 'self'; "
        "object-src 'none'; "
        "base-uri 'self'; "
        "form-action 'self'; "
        "frame-ancestors 'none'"
    )

    # CORRECCIÓN OWASP ZAP: Missing Anti-clickjacking Header
    response.headers["X-Frame-Options"] = "DENY"

    # CORRECCIÓN OWASP ZAP: X-Content-Type-Options Header Missing
    response.headers["X-Content-Type-Options"] = "nosniff"

    # CORRECCIÓN OWASP ZAP: Permissions Policy Header Not Set
    response.headers["Permissions-Policy"] = (
        "camera=(), microphone=(), geolocation=(), payment=(), fullscreen=(self)"
    )

    # CORRECCIÓN OWASP ZAP: Cross-Origin headers missing
    response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
    response.headers["Cross-Origin-Resource-Policy"] = "same-origin"

    # CORRECCIÓN OWASP ZAP: Storable and Cacheable Content
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    # CORRECCIÓN OWASP ZAP: Server Leaks Version Information
    response.headers.pop("Server", None)

    # MÉTRICA PROMETHEUS:
    # Registra método HTTP, endpoint y código de estado de cada respuesta.
    endpoint_name = request.endpoint or request.path

    REQUEST_COUNT.labels(
        request.method,
        endpoint_name,
        str(response.status_code)
    ).inc()

    return response


@app.route('/')
def index():
    return 'Welcome to the Task Manager Application!'


@app.route('/robots.txt')
def robots_txt():
    return Response(
        "User-agent: *\nDisallow:\n",
        mimetype="text/plain"
    )


@app.route('/sitemap.xml')
def sitemap_xml():
    return Response(
        '''<?xml version="1.0" encoding="UTF-8"?>
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
            <url>
                <loc>http://ev3-app:5000/</loc>
            </url>
        </urlset>
        ''',
        mimetype="application/xml"
    )


@app.route('/metrics')
def metrics():
    """
    Endpoint para proporcionar métricas.

    Retorna:
        Métricas en formato compatible con Prometheus.
    """
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')

        conn = get_db_connection()

        # CORRECCIÓN CWE-89: SQL Injection
        # Se elimina la consulta SQL construida con f-string.
        # Se utiliza una consulta parametrizada para evitar que los datos del usuario
        # sean interpretados como parte de la sentencia SQL.
        hashed_password = hash_password(password)
        query = "SELECT * FROM users WHERE username = ? AND password = ?"
        user = conn.execute(query, (username, hashed_password)).fetchone()

        conn.close()

        if user:
            session['user_id'] = user['id']
            session['role'] = user['role']
            return redirect(url_for('dashboard'))
        else:
            return 'Invalid credentials!'

    return '''
        <form method="post">
            Username: <input type="text" name="username"><br>
            Password: <input type="password" name="password"><br>
            <input type="submit" value="Login">
        </form>
    '''


@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']

    conn = get_db_connection()
    tasks = conn.execute(
        "SELECT * FROM tasks WHERE user_id = ?",
        (user_id,)
    ).fetchall()
    conn.close()

    return render_template_string('''
        <h1>Welcome, user {{ user_id }}!</h1>

        <form action="/add_task" method="post">
            <input type="text" name="task" placeholder="New task"><br>
            <input type="submit" value="Add Task">
        </form>

        <h2>Your Tasks</h2>
        <ul>
        {% for task in tasks %}
            <li>
                {{ task['task'] }}

                <!-- CORRECCIÓN ADICIONAL: la eliminación se realiza mediante método POST -->
                <form action="/delete_task/{{ task['id'] }}" method="post">
                    <button type="submit">Delete</button>
                </form>
            </li>
        {% endfor %}
        </ul>
    ''', user_id=user_id, tasks=tasks)


@app.route('/add_task', methods=['POST'])
def add_task():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    task = request.form.get('task', '')
    user_id = session['user_id']

    conn = get_db_connection()
    conn.execute(
        "INSERT INTO tasks (user_id, task) VALUES (?, ?)",
        (user_id, task)
    )
    conn.commit()
    conn.close()

    return redirect(url_for('dashboard'))


@app.route('/delete_task/<int:task_id>', methods=['POST'])
def delete_task(task_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()

    # CORRECCIÓN ADICIONAL:
    # Solo se elimina la tarea si pertenece al usuario autenticado.
    conn.execute(
        "DELETE FROM tasks WHERE id = ? AND user_id = ?",
        (task_id, session['user_id'])
    )

    conn.commit()
    conn.close()

    return redirect(url_for('dashboard'))


@app.route('/admin')
def admin():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))

    return 'Welcome to the admin panel!'


if __name__ == '__main__':
    # CORRECCIÓN CWE-94: debug=True en Flask
    # Se desactiva el modo debug para evitar exposición del debugger.
    app.run(port=5000, debug=False)
