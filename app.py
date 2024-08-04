from flask import Flask
from flask import render_template, request, redirect, Response, url_for, session
import mysql.connector

app = Flask(__name__,template_folder='template')

def get_db_connection():
    conn = mysql.connector.connect(
        host='sql10.freemysqlhosting.net',
        user='sql10723991',
        password='BUgAyXLwfQ',
        database='sql10723991'
    )
    return conn

@app.route('/')
def home():
    return render_template('index.html')   

@app.route('/admin')
def admin():
    return render_template('admin.html')   

@app.route('/acceso-login', methods= ["GET", "POST"])
def login():
   
    if request.method == 'POST' and 'txtCorreo' in request.form and 'txtPassword' in request.form:
       
        _correo = request.form['txtCorreo']
        _password = request.form['txtPassword']

        conn = get_db_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute('SELECT * FROM user WHERE email = %s AND password = %s', (_correo, _password,))
        account = cur.fetchone()
        cur.close()
        conn.close()
        
        if account:
            session['logueado'] = True
            session['id'] = account['id']
            return render_template("admin.html")
        else:
            return render_template('index.html', mensaje="Usuario O Contraseña Incorrectas")

    return render_template('index.html')
if __name__ == '__main__':
   app.secret_key = "clavesorda"
   app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
