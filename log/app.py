from flask import Flask
from flask import render_template, request, redirect, Response, url_for, session
import mysql.connector

app = Flask(__name__,template_folder='template')

def get_db_connection():
    conn = mysql.connector.connect(
        host='localhost',
        user='yourusername',
        password='Straeker_2002',
        database='yourdatabase'
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

        cur = mysql.connection.cursor()
        cur.execute('SELECT * FROM usuarios WHERE correo = %s AND password = %s', (_correo, _password,))
        account = cur.fetchone()
      
        if account:
            session['logueado'] = True
            session['id'] = account['id']

            return render_template("admin.html")
        else:
            return render_template('index.html',mensaje="Usuario O Contraseña Incorrectas")

    
if __name__ == '__main__':
   app.run(debug=True)
