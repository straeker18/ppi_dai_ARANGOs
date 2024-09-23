from flask import Blueprint, render_template
import csv
from collections import defaultdict
import os

# Crear un Blueprint para el módulo del diccionario
diccionario_bp = Blueprint('diccionario', __name__)

@diccionario_bp.route('/diccionario')
def diccionario():
    categorias_senas = defaultdict(list)
    csv_file_path = os.path.join('static', 'diccionario_senas.csv')
    try:
        with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                img_url = row['img'] if row['img'] else 'static/default_image.png'
                categorias_senas[row['categoria']].append({
                    "img": img_url,
                    "descripcion": row['descripcion'],
                    "nombre": row['signo']
                })
    except FileNotFoundError:
        print("Error: El archivo CSV no fue encontrado.")
    return render_template('diccionario.html', categorias_senas=categorias_senas)
