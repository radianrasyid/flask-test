from flask import Flask, render_template, request, redirect, url_for, jsonify, current_app, Blueprint
import psycopg2 
from flask_restx import Namespace, Resource
from .db import pool

# Inisialisasi pool koneksi
# pool = ConnectionPool()

# Mendapatkan koneksi dari pool
# conn = pool.get_connection()
# print(conn)

users = Namespace('users', description='User Namespace')

@users.route('')
class Users(Resource):
    def get(self):
        
        conn = pool.get_connection()
        cur = conn.cursor()
        cur.execute(
        ''' 
            SELECT *
            from users
        '''
        )
        res = cur.fetchall()
        pool.close_all_connections()
        # cur.close()
        # conn.close()
        pool.return_connection(conn)
        return jsonify(res)
    
    def say_hello():
        print("hello world")

