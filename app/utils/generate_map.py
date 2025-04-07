import pandas as pd
import geopandas as gpd
from google.cloud import bigquery
import folium
import os
from folium.plugins import HeatMap
from deep_translator import GoogleTranslator

DATA_PATH = 'data/shapefiles/ne_110m_admin_0_countries.shp'

# Function to generate the map
def generate_map(map_type='imports'):
    # Load the shapefile
    world = gpd.read_file(DATA_PATH)

    # Generate the map centered on Mexico
    m = folium.Map(location=[23.6345, -102.5528], zoom_start=5)

    # Load the data from BigQuery
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "data/credentials.json"
    project_id = "certain-cursor-454922-p9"
    client = bigquery.Client(project=project_id)
    query = "SELECT * FROM `certain-cursor-454922-p9.mexico_costume_economics.costumes_data`"
    query_job = client.query(query)
    df = query_job.to_dataframe()
    df.fillna(0, inplace=True)
    # Ajustar el nombre de la columna según el archivo CSV
    if 'Regiones' in df.columns:
        df['Regions'] = df['Regiones']
    else:
        print("Error: La columna 'Regiones' no se encuentra en el CSV")

    # Reemplazar la traducción automática por un mapeo manual
    country_mapping = {
        "Estados Unidos": "United States of America",
        "EE. UU.": "United States of America",
        "Rusia": "Russia",
        "Chile": "Chile",
        "Reino Unido": "United Kingdom",
        "Alemania": "Germany",
        "Francia": "France",
        "China": "China",
        "Japón": "Japan",
        "Canadá": "Canada",
        "Brasil": "Brazil",
        "España": "Spain",
        "Italia": "Italy",
        "México": "Mexico",
        # Añadir más mapeos según sea necesario
    }

    # Usar el mapeo (con fallback a traducción automática)
    def map_country(name):
        if name in country_mapping:
            return country_mapping[name]
        else:
            # Intenta traducir si no está en el mapeo
            try:
                return GoogleTranslator(source='es', target='en').translate(name)
            except:
                return name

    df["Regions"] = df["Regiones"].apply(map_country)
    # Unir datos con el shapefile por el nombre del país
    world = world.merge(df, how="left", left_on="NAME", right_on="Regions")
    # Llenar valores NaN con 0 después de la unión
    world.fillna(0, inplace=True)


    # Prepare heatmap data
    heat_data = []
    for _, row in world.iterrows():
        value = row['Imports'] if map_type == 'imports' else row['Exports']
        if value > 0:
            coords = row['geometry'].centroid.coords[:]
            lon, lat = coords[0]
            heat_data.append([lat, lon, value])

            # Add country polygons with tooltips
            folium.GeoJson(
                row['geometry'],
                tooltip=f"{map_type.capitalize()}: {value:,.2f} USD",
                popup=f"Region: {row['NAME']}<br>{map_type.capitalize()}: {value:,.2f} USD"
            ).add_to(m)

    # Add the heatmap layer
    HeatMap(heat_data).add_to(m)

    # Guardar el mapa en la carpeta estática con la ruta absoluta
    map_path = os.path.join(os.getcwd(), 'app', 'static', f'map_{map_type}.html')
    try:
        m.save(map_path)
        print(f"Mapa generado correctamente: {map_path}")
    except Exception as e:
        print(f"Error al guardar el mapa: {str(e)}")

    return f'static/map_{map_type}.html'
