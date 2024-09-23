import os
os.environ['MPLCONFIGDIR'] = '/tmp/matplotlib'
import sqlite3
from flask import Flask, render_template, request, session, g, redirect, url_for
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import csv
import random
from collections import defaultdict
from scipy import stats
import geopandas as gpd  # Importar GeoPandas

# Crear instancia de la aplicación Flask
app = Flask(__name__, template_folder='template')
app.secret_key = "clave_secreta"  # Cambiar a una clave segura para producción
DATABASE = 'signsense.db'


def get_db():
    """
    Establece una conexión a la base de datos SQLite si no existe.
    Retorna la conexión de la base de datos.
    """
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db


@app.teardown_appcontext
def close_connection(exception):
    """
    Cierra la conexión de la base de datos al final del contexto de la aplicación.
    """
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def usuario_logueado():
    """
    Verifica si el usuario está logueado en la sesión.
    Retorna True si el usuario está logueado, de lo contrario False.
    """
    return session.get('logueado', False)


@app.route('/')
def inicio():
    """
    Renderiza la página de inicio, mostrando si el usuario está logueado.
    """
    logueado = usuario_logueado()
    return render_template('inicio.html', logueado=logueado)


@app.route('/index')
def home():
    """
    Renderiza la página principal de la aplicación.
    """
    logueado = usuario_logueado()
    return render_template('index.html', logueado=logueado)


@app.route('/admin')
def admin():
    """
    Renderiza la página de administración si el usuario está logueado.
    """
    logueado = usuario_logueado()
    return render_template('admin.html', logueado=logueado)


@app.route('/acceso-login', methods=["GET", "POST"])
def login():
    """
    Maneja el proceso de login del usuario. Redirige a 'start' si el login es exitoso.
    """
    if usuario_logueado():
        return redirect(url_for('start'))

    if request.method == 'POST':
        correo = request.form.get('txtCorreo')
        password = request.form.get('txtPassword')

        if correo and password:
            conn = get_db()
            cur = conn.cursor()
            cur.execute('SELECT * FROM user WHERE email = ? AND password = ?', (correo, password,))
            account = cur.fetchone()
            cur.close()

            if account:
                session['logueado'] = True
                session['id'] = account['id']
                session['usuario_nombre'] = account['name']
                return redirect(url_for('start'))

            return render_template('index.html',
                                   mensaje="Usuario o Contraseña Incorrectas", logueado=False)

    return render_template('index.html', logueado=False)


@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    Permite registrar a nuevos usuarios en la aplicación.
    """
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        name = request.form.get('name')  # Nombre opcional

        if email and password:
            conn = get_db()
            try:
                cur = conn.cursor()
                cur.execute('INSERT INTO user (email, password, name) VALUES (?, ?, ?)',
                            (email, password, name))
                conn.commit()
                cur.close()
                mensaje = "Registro exitoso. Ahora puedes iniciar sesión."
                return render_template('index.html', mensaje=mensaje)
            except sqlite3.Error as e:
                print(f"Error en la base de datos: {e}")
                mensaje = "No se pudo registrar el usuario. Intenta de nuevo."
                return render_template('register.html', mensaje=mensaje)

    return render_template('register.html')


@app.route('/send-contact', methods=['POST'])
def send_contact():
    """
    Procesa el envío del formulario de contacto.
    """
    nombre = request.form.get('nombre')
    email = request.form.get('email')
    mensaje = request.form.get('mensaje')

    # Aquí se podría agregar lógica para enviar el mensaje por correo
    return render_template('inicio.html', mensaje="¡Gracias por contactarnos! Te responderemos pronto.")


@app.route('/mapa')
def mapa():
    """
    Renderiza la página del mapa utilizando GeoPandas y muestra datos geoespaciales.
    """
    if not usuario_logueado():
        return redirect('/acceso-login')

    nombre_usuario = session.get('usuario_nombre', 'Usuario')

    # Cargar datos geoespaciales usando GeoPandas
    try:
        # Ruta al archivo CSV con los datos del mapa
        csv_file_path = os.path.join('static', 'mapasordosaprendizaje.csv')

        # Leer el archivo CSV usando Pandas
        df = pd.read_csv(csv_file_path)

        # Asegurarse de que las columnas estén correctamente nombradas
        df.columns = df.columns.str.strip().str.lower()
        df.rename(columns={'lat': 'latitude', 'lon': 'longitude'}, inplace=True)

        # Convertir el DataFrame en un GeoDataFrame
        gdf = gpd.GeoDataFrame(
            df,
            geometry=gpd.points_from_xy(df['longitude'], df['latitude'])
        )

        # Convertir el GeoDataFrame a GeoJSON para pasarlo al template
        geojson_data = gdf.to_json()

        return render_template('map.html', nombre_usuario=nombre_usuario, geojson_data=geojson_data)

    except Exception as e:
        print(f"Error al cargar los datos geoespaciales: {e}")
        return render_template('map.html', mensaje="No se pudo cargar el mapa.")
@app.route('/start')
def start():
    """
    Renderiza la página de inicio para usuarios logueados.
    """
    if not usuario_logueado():
        return redirect(url_for('login'))

    nombre_usuario = session.get('usuario_nombre', 'Usuario')
    return render_template('start.html', nombre_usuario=nombre_usuario)


@app.route('/logout')
def logout():
    """
    Cierra la sesión del usuario y lo redirige a la página de inicio.
    """
    session.pop('logueado', None)
    session.pop('id', None)
    session.pop('usuario_nombre', None)
    return redirect('/')


@app.route('/diccionario')
def diccionario():
    """
    Renderiza la página del diccionario de señas con imágenes y descripciones cargadas desde un archivo CSV,
    agrupadas por categorías.
    """
    categorias_senas = defaultdict(list)

    # Ruta del archivo CSV
    csv_file_path = os.path.join('static', 'diccionario_senas.csv')

    # Leer el archivo CSV y agrupar por categorías
    try:
        with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                img_url = row['img'] if row['img'] else 'static/default_image.png'  # Imagen predeterminada
                categorias_senas[row['categoria']].append({
                    "img": img_url,
                    "descripcion": row['descripcion'],
                    "nombre": row['signo']  # Columna 'signo' desde el CSV
                })
    except FileNotFoundError:
        print("Error: El archivo CSV no fue encontrado.")

    return render_template('diccionario.html', categorias_senas=categorias_senas)


def cargar_datos():
    """
    Cargar los datos del CSV usando Pandas.
    """
    return pd.read_csv('static/diccionario_senas.csv')


def cargar_senas_por_categoria(categoria_seleccionada):
    """
    Carga las señas de una categoría específica desde el archivo CSV.
    """
    df = cargar_datos()
    preguntas_test = df[df['categoria'] == categoria_seleccionada].to_dict('records')
    return preguntas_test


@app.route('/seleccionar-categoria')
def seleccionar_categoria():
    """
    Renderiza la página para seleccionar una categoría antes de realizar el test de señas.
    """
    categorias = cargar_datos()['categoria'].unique()  # Obtener categorías únicas desde el CSV
    return render_template('seleccionar_categoria.html', categorias=categorias)


@app.route('/test', methods=['GET', 'POST'])
def test():
    """
    Renderiza el test de señas de una categoría específica con selección múltiple y guarda las respuestas.
    """
    categoria = request.args.get('categoria')  # Obtener categoría desde el query string
    if not categoria:
        return "No se especificó una categoría.", 400

    if request.method == 'POST':
        # Guardar respuestas del usuario en sesión
        respuestas_usuario = []
        preguntas = cargar_senas_por_categoria(categoria)
        for idx, pregunta in enumerate(preguntas):
            respuesta = request.form.get(f"respuesta_{idx}")
            if respuesta:
                respuestas_usuario.append(respuesta)
            else:
                respuestas_usuario.append("Sin respuesta")
        session['respuestas'] = respuestas_usuario
        return redirect(url_for('resultados', categoria=categoria))

    # Cargar las preguntas de la categoría seleccionada
    preguntas = cargar_senas_por_categoria(categoria)

    # Preparar opciones de respuesta (correcta e incorrectas)
    opciones_respuestas = []
    for pregunta in preguntas:
        # Selecciona dos respuestas incorrectas aleatoriamente dentro de la misma categoría
        incorrectas = random.sample([p['nombre'] for p in preguntas if p['nombre'] != pregunta['nombre']], 2)
        # Agregar la respuesta correcta
        opciones = incorrectas + [pregunta['nombre']]
        random.shuffle(opciones)  # Barajar las opciones para que no siempre esté en la misma posición
        opciones_respuestas.append({
            'pregunta': pregunta,
            'opciones': opciones
        })

    return render_template('test.html', preguntas=opciones_respuestas, categoria=categoria, enumerate=enumerate)

@app.route('/resultados/<categoria>')
def resultados(categoria):
    """
    Muestra los resultados del test después de completarlo y genera estadísticas con NumPy y SciPy.
    """
    respuestas_usuario = session.get('respuestas', [])
    preguntas = cargar_senas_por_categoria(categoria)

    # Comparar respuestas del usuario con las correctas
    resultados = []

    if len(respuestas_usuario) != len(preguntas):
        return render_template('error.html', mensaje="No respondiste a todas las preguntas.")

    correctas = 0
    for i, pregunta in enumerate(preguntas):
        # Evitar el IndexError validando que el índice sea válido
        if i < len(respuestas_usuario):
            correcto = (respuestas_usuario[i] == pregunta['nombre'])
        else:
            correcto = False  # Si no hay respuesta, la respuesta es incorrecta por defecto
        if correcto:
            correctas += 1
        resultados.append({
            'pregunta': pregunta['nombre'],
            'respuesta_usuario': respuestas_usuario[i] if i < len(respuestas_usuario) else "Sin respuesta",
            'correcto': correcto
        })

    total_preguntas = len(preguntas)
    porcentaje_correctas = (correctas / total_preguntas) * 100

    # Calcular estadísticas usando NumPy y SciPy
    puntuaciones = np.array([1 if r['correcto'] else 0 for r in resultados])
    media = np.mean(puntuaciones)
    desviacion_estandar = np.std(puntuaciones)
    intervalo_confianza = stats.t.interval(
        0.95, len(puntuaciones)-1, loc=media, scale=stats.sem(puntuaciones))

    # Generar gráfico con Matplotlib
    labels = ['Correctas', 'Incorrectas']
    sizes = [correctas, total_preguntas - correctas]
    colors = ['green', 'red']

    plt.figure(figsize=(6, 6))
    plt.pie(sizes, labels=labels, colors=colors,
            autopct='%1.1f%%', startangle=90)
    plt.title('Resultados del Test')
    plt.axis('equal')  # Para que el gráfico sea un círculo

    # Guardar el gráfico en el directorio estático
    grafico_filename = 'grafico_resultados.png'
    grafico_path = os.path.join('static', grafico_filename)
    plt.savefig(grafico_path)
    plt.close()

    # Generar la URL para el archivo estático
    grafico_url = url_for('static', filename=grafico_filename)

    return render_template('resultados.html', resultados=resultados, categoria=categoria,
                           porcentaje_correctas=porcentaje_correctas,
                           media=media,
                           desviacion_estandar=desviacion_estandar,
                           intervalo_confianza=intervalo_confianza,
                           grafico_url=grafico_url)


if __name__ == '__main__':
    # Iniciar la aplicación con el contexto de la base de datos
    with app.app_context():
        db = get_db()

    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
