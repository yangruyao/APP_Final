from flask import Blueprint, jsonify, request
import requests
import csv
from io import StringIO
from urllib.parse import urlencode

api_blueprint = Blueprint('api', __name__)

BASE_URLS = {
    "atracciones": "https://dataestur.azure-api.net/API-SEGITTUR-v1/ATRACCIONES_RECURSOS_TURISTICOS_DL",
    "turismo": "https://dataestur.azure-api.net/API-SEGITTUR-v1/TURISMO_RECEPTOR_PROV_PAIS_DL?desde%20%28a%C3%B1o%29=2023&desde%20%28mes%29=1&hasta%20%28a%C3%B1o%29=2023&hasta%20%28mes%29=12",
    "satisfaccion": "https://dataestur.azure-api.net/API-SEGITTUR-v1/IND_SATISFACCION_PERCEPCION_DL?desde%20%28a%C3%B1o%29=2023&desde%20%28mes%29=1&hasta%20%28a%C3%B1o%29=2023&hasta%20%28mes%29=12"
                    "",
}

@api_blueprint.route('/api/tourism/attractions', methods=['GET'])
def get_tourism_attractions():
    province_name = request.args.get('province')
    if not province_name:
        return jsonify({'error': 'No se especificó una provincia'}), 400

    def normalize(text):
        return text.lower()

    normalized_name = normalize(province_name)
    print(f"Provincia solicitada normalizada: {normalized_name}")

    results = {'atracciones': [], 'turismo': [], 'satisfaccion': []}

    headers = {'accept': 'application/octet-stream'}

    try:
        for category, url in BASE_URLS.items():
            # Construir los parámetros
            params = {"CCAA": "Todos", "Provincia": province_name}
            encoded_params = urlencode(params)
            full_url = f"{url}&{encoded_params}" if '?' in url else f"{url}?{encoded_params}"
            print(f"Consultando URL completa: {full_url}")

            response = requests.get(full_url, headers=headers)

            if response.status_code != 200:
                print(f"Error en la respuesta de {category}: {response.status_code}")
                continue

            # Procesar CSV
            decoded_content = response.content.decode('latin1', errors='replace')
            print(
                f"Datos crudos recibidos para {category}: {decoded_content[:500]}")  # Solo los primeros 500 caracteres

            csv_reader = csv.reader(StringIO(decoded_content), delimiter=';')

            if category == "atracciones":
                for row in csv_reader:
                    if len(row) >= 6 and normalize(row[2]) == normalized_name:
                        results['atracciones'].append({
                            "Nombre": row[0],
                            "Descripcion": f"Valoración: {row[3]}, Opiniones: {row[4]}"
                        })

            elif category == "turismo":
                for row in csv_reader:
                    if len(row) >= 4 and normalize(row[2]) == normalized_name:
                        results['turismo'].append({
                            "Año": row[0],
                            "Mes": row[1],
                            "Pais Origen": row[4],
                            "Turistas": row[5]
                        })
            elif category == "satisfaccion":
                        for row in csv_reader:
                            if len(row) >= 6 and normalize(
                                    row[4]) == normalized_name:  # Usar la columna de provincia destino
                                results['satisfaccion'].append({
                                    "Año": row[0],
                                    "Mes": row[1],
                                    "Pais Origen": row[2],
                                    "Satisfaccion General": row[5] if row[5] else "N/A",
                                    "Satisfaccion Productos": row[6] if row[6] else "N/A",
                                })

        if not results['atracciones'] and not results['turismo'] and not results['satisfaccion']:
            return jsonify({'error': f'No se encontraron datos para la provincia "{province_name}"'}), 404

        return jsonify(results)

    except requests.RequestException as e:
        return jsonify({'error': 'Error al conectar con las rutas de SEGITTUR', 'details': str(e)}), 500