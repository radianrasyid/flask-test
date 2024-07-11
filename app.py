# app.py
import sys
import os
from flask_cors import CORS
from pathlib import Path
from flask import Flask, send_from_directory, jsonify
from flask_restx import Api, Resource
sys.path.append(str(Path(__file__).parent))
# Tambahkan direktori 'apis' ke dalam sys.path
# current_dir = os.path.dirname(os.path.realpath(__file__))
# apis_dir = os.path.join(current_dir, 'apis')
# sys.path.append(apis_dir)

    
app = Flask(__name__) 
api = Api(app)
CORS(app, resources={r"/*": {"origins": "*"}})

# Inisialisasi pool koneksi
from api.db import ConnectionPool, initializeConnectionPool, pool, psycopg2, atexit
initializeConnectionPool()

# from api.users import users
from api.users import users
from api.dash import dash
from api.menus import menus
from api.transaction import transaction
from api.order import order
from api.delivery import delivery
# from apis.dashboard import dashboard
import pkgutil

# Mendaftarkan namespace users
api.add_namespace(users, path='/users')
api.add_namespace(menus, path='/menus')
api.add_namespace(transaction, path='/transaction')
api.add_namespace(dash, path='/dash')
api.add_namespace(order, path='/order') 
api.add_namespace(delivery, path='/delivery') 

    # Route untuk favicon.ico
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                                'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/')
def hello_world():
    return jsonify({"message": "Hello World"})


if __name__ == "__main__":
    app.run(debug=True)