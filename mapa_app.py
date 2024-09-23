from flask import Blueprint, render_template, session, redirect
import pandas as pd
import geopandas as gpd
import os

# Crear un Blueprint para el módulo del mapa
mapa_bp = Blueprint('mapa', __name__)

@mapa_bp.route('/mapa')
def mapa():
    if not session.get('logueado'):
        return redirect('/acceso-login')

    nombre_usuario = session.get('usuario_nombre', 'Usuario')

    # Cargar datos geoespaciales usando GeoPandas
    try:
        csv_file_path = os.path.join('static', 'mapasordosaprendizaje.csv')
        df = pd.read_csv(csv_file_path)
        df.rename(columns={'lat': 'latitude', 'lon': 'longitude'}, inplace=True)
        gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df['longitude'], df['latitude']))
        geojson_data = gdf.to_json()

        return render_template('map.html', nombre_usuario=nombre_usuario, geojson_data=geojson_data)
    except Exception as e:
        print(f"Error al cargar los datos geoespaciales: {e}")
        return render_template('map.html', mensaje="No se pudo cargar el mapa.")
