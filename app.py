import os
import datetime
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import json
import sqlite3

import logging



app = Flask(__name__)
CORS(app)


handler = logging.FileHandler('logs/flask_app.log')  # Log to a file
app.logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
handler.setFormatter(formatter)
app.logger.addHandler(handler)


# Crie uma métrica de exemplo (contador de requisições)
REQUEST_COUNT = Counter('http_requests_total', 'Total de requisições HTTP', ['method', 'endpoint'])
REQUEST_LATENCY = Histogram('http_request_latency_seconds', 'Latência das requisições HTTP em segundos', ['method', 'endpoint'])
HTTP_ERRORS = Counter('http_errors_total', 'Total de respostas HTTP com erro', ['method', 'endpoint', 'status_code'])


def log_message(level, message):
    """Loga uma mensagem com o nível especificado."""

    log_methods = {
        'debug': app.logger.debug,
        'info': app.logger.info,
        'warning': app.logger.warning,
        'error': app.logger.error,
        'critical': app.logger.critical
    }
    if level in log_methods:
        log_methods[level](f"{message}")
    else:
        app.logger.error(f"Unrecognized logging level: {level}")


# Middleware para contar requisições
@app.before_request
def before_request():
    REQUEST_COUNT.labels(method=request.method, endpoint=request.path).inc()

# Rota para o Prometheus coletar as métricas
@app.route('/metrics')
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

# Endpoint para devolver todos as pessoas cadastradas
@app.route('/')
def home():
    log_message('info', 'This is an INFO message')
    log_message('debug', 'This is a DEBUG message')
    log_message('warning', 'This is a WARNING message')
    log_message('error', 'This is an ERROR message')
    log_message('critical', 'This is a CRITICAL message')
    return "API de veículos"

@app.route('/veiculos', methods=['GET'])
def veiculos():
    try:
        with sqlite3.connect('veiculos.db') as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''SELECT renavam, placa, marca, modelo FROM veiculos''')
            result = cursor.fetchall()
            log_message('info', '/veiculos GET')
            return json.dumps([dict(ix) for ix in result]), 200
    except Exception as e:
        log_message('error', '/veiculos GET')
        return jsonify(error=str(e)), 500

@app.route('/veiculo/<placa>', methods=['GET', 'DELETE'])
def veiculo_por_placa(placa):
    try:
        with sqlite3.connect('veiculos.db') as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            if request.method == 'GET':
                cursor.execute('''SELECT renavam, placa, marca, modelo FROM veiculos WHERE placa=?''', [placa])
                result = cursor.fetchall()
                if result:
                    log_message('info', '/veiculo/<placa> GET - Veículo encontrado')
                    return json.dumps([dict(ix) for ix in result]), 200
                log_message('info', '/veiculo/<placa> GET - Veículo não encontrado')
                return jsonify(error="Veículo não encontrado"), 404
            elif request.method == 'DELETE':
                cursor.execute('DELETE FROM veiculos WHERE placa = ?', (placa,))
                if cursor.rowcount == 0:
                    log_message('info', '/veiculo/<placa> DELETE - Veículo não encontrado')
                    return jsonify(error="Veículo não encontrado"), 404
                conn.commit()
                log_message('info', '/veiculo/<placa> DELETE - Veículo encontrado e deletado')
                return jsonify(success="Veículo deletado com sucesso"), 200
    except Exception as e:
        log_message('error', '/veiculo/<placa>')
        return jsonify(error=str(e)), 500

@app.route('/veiculo', methods=['POST'])
def insere_atualiza_veiculo():
    data = request.get_json(force=True)
    renavam = data.get('renavam')
    placa = data.get('placa')
    marca = data.get('marca')
    modelo = data.get('modelo')
    try:
        with sqlite3.connect('veiculos.db') as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT 1 FROM veiculos WHERE placa = ?', (placa,))
            exists = cursor.fetchone()
            if exists:
                log_message('info', '/veiculo POST - Veículo encontrado e atualizado')
                cursor.execute('UPDATE veiculos SET renavam=?, marca=?, modelo=? WHERE placa=?', (renavam, marca, modelo, placa))
                conn.commit()
                return jsonify(success="Veículo atualizado com sucesso"), 200
            log_message('info', '/veículo POST - Veículo não encontrado e inserido')
            cursor.execute('INSERT INTO veiculos (renavam, placa, marca, modelo) VALUES (?, ?, ?, ?)', (renavam, placa, marca, modelo))
            conn.commit()
            return jsonify(success="Veículo inserido com sucesso"), 201
    except Exception as e:
        log_message('error', '/veiculo POST')
        return jsonify(error=str(e)), 500
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
