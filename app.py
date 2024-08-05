from flask import Flask, render_template, request, session
import mysql.connector
from mysql.connector import Error

app = Flask(__name__, template_folder='template')
app.secret_key = "clave"


def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host='sql10.freemysqlhosting.net',
            user='sql10723991',
            password='BUgAyXLwfQ',
            database='sql10723991'
        )
        if conn.is_connected():
            return conn
    except Error as e:
        print(f"Error: {e}")
    return None


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/admin')
def admin():
    return render_template('admin.html')


@app.route('/acceso-login', methods=["GET", "POST"])
def login():
    if request.method == 'POST' and 'txtCorreo' in request.form and 'txtPassword' in request.form:
        _correo = request.form['txtCorreo']
        _password = request.form['txtPassword']

        conn = get_db_connection()
        if conn:
            try:
                cur = conn.cursor(dictionary=True)
                cur.execute('SELECT * FROM user WHERE email = %s AND password = %s', (_correo, _password,))
                account = cur.fetchone()
                cur.close()
            except Error as e:
                print(f"Database error: {e}")
                account = None
            finally:
                conn.close()

            if account:
                session['logueado'] = True
                session['id'] = account['id']
                return render_template("admin.html")
            else:
                return render_template('index.html', mensaje="Usuario o Contraseña Incorrectas")
        else:
            return render_template('index.html', mensaje="No se pudo conectar a la base de datos")

    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
