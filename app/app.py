from flask import Flask, render_template, request, jsonify
import os
from utils.generate_map import generate_map
from google.cloud import bigquery
import pandas as pd

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/update_map', methods=['POST'])
def update_map():
    data = request.json
    map_type = data.get('type', 'imports')
    try:
        map_path = generate_map(map_type)
        response = {'status': 'success', 'map_path': map_path}
    except Exception as e:
        response = {'status': 'error', 'message': str(e)}
    return jsonify(response)

@app.route('/get_chart_data', methods=['POST'])
def get_chart_data():
    data = request.json
    map_type = data.get('type', 'imports')
    try:
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "data/credentials.json"
        project_id = "certain-cursor-454922-p9"
        client = bigquery.Client(project=project_id)
        query = "SELECT * FROM `certain-cursor-454922-p9.mexico_costume_economics.costumes_data`"
        query_job = client.query(query)
        df = query_job.to_dataframe()
        df.fillna(0, inplace=True)

        top_countries = df[['Regiones', map_type.capitalize()]].sort_values(by=map_type.capitalize(), ascending=False).head(5)
        labels = top_countries['Regiones'].tolist()
        values = top_countries[map_type.capitalize()].tolist()
        response = {'status': 'success', 'data': {'labels': labels, 'values': values}}
    except Exception as e:
        response = {'status': 'error', 'message': str(e)}
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
