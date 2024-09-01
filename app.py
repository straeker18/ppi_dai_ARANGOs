import os
import sqlite3
from flask import Flask, render_template, request, session, g, redirect, url_for

app = Flask(__name__, template_folder='template')
app.secret_key = "clave"
DATABASE = 'signsense.db'


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


# Función para verificar si un usuario está logueado
def usuario_logueado():
    return 'logueado' in session and session['logueado']


@app.route('/')
def inicio():
    logueado = usuario_logueado()
    return render_template('inicio.html', logueado=logueado)


@app.route('/index')
def home():
    logueado = usuario_logueado()
    return render_template('index.html', logueado=logueado)


@app.route('/admin')
def admin():
    logueado = usuario_logueado()
    return render_template('admin.html', logueado=logueado)


@app.route('/acceso-login', methods=["GET", "POST"])
def login():
    if usuario_logueado():  # Si el usuario ya está logueado, redirigir a start.html
        return redirect(url_for('start'))

    if request.method == 'POST' and 'txtCorreo' in request.form and 'txtPassword' in request.form:
        _correo = request.form['txtCorreo']
        _password = request.form['txtPassword']

        conn = get_db()
        cur = conn.cursor()
        cur.execute('SELECT * FROM user WHERE email = ? AND password = ?', (_correo, _password,))
        account = cur.fetchone()
        cur.close()

        if account:
            session['logueado'] = True
            session['id'] = account['id']
            session['usuario_nombre'] = account['name']  # Guardar nombre del usuario en la sesión (opcional)
            return redirect(url_for('start'))  # Redirigir a start.html después de un login exitoso
        else:
            return render_template('index.html', mensaje="Usuario o Contraseña Incorrectas", logueado=False)

    return render_template('index.html', logueado=False)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        _email = request.form['email']
        _password = request.form['password']
        _name = request.form.get('name')  # Opcional: nombre del usuario

        conn = get_db()
        try:
            cur = conn.cursor()
            cur.execute('INSERT INTO user (email, password, name) VALUES (?, ?, ?)', (_email, _password, _name))
            conn.commit()
            cur.close()
            mensaje = "Registro exitoso. Ahora puedes iniciar sesión."
            return render_template('index.html', mensaje=mensaje)
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            mensaje = "No se pudo registrar el usuario. Intenta de nuevo."
            return render_template('register.html', mensaje=mensaje)

    return render_template('register.html')


@app.route('/send-contact', methods=['POST'])
def send_contact():
    nombre = request.form['nombre']
    email = request.form['email']
    mensaje = request.form['mensaje']

    # Aquí puedes agregar lógica para enviar el mensaje por correo electrónico
    return render_template('inicio.html', mensaje="¡Gracias por contactarnos! Te responderemos pronto.")


@app.route('/mapa')
def mapa():
    if not usuario_logueado():  # Verificar si el usuario está logueado
        return redirect('/acceso-login')  # Redirigir al login si no está logueado
    nombre_usuario = session.get('usuario_nombre', 'Usuario')  # Obtener el nombre del usuario
    return render_template('map.html', nombre_usuario=nombre_usuario)


@app.route('/start')
def start():
    if not usuario_logueado():
        return redirect(url_for('login'))
    nombre_usuario = session.get('usuario_nombre', 'Usuario')
    return render_template('start.html', nombre_usuario=nombre_usuario)


@app.route('/logout')
def logout():
    session.pop('logueado', None)
    session.pop('id', None)
    session.pop('usuario_nombre', None)
    return redirect('/')


if __name__ == '__main__':
    with app.app_context():
        db = get_db()

    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
