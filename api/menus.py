from flask import Flask, render_template, request, redirect, url_for, jsonify, current_app, Blueprint
import psycopg2 
from flask_restx import Namespace, Resource, reqparse
import argparse
from .db import pool
from psycopg2.extras import DictCursor
from datetime import datetime


menus = Namespace("menus", description= "Menus's APIS Namespace")

menusArgs = reqparse.RequestParser()
# menusArgs.add_argument('rate', type=int, help='Rate cannot be converted')
menusArgs.add_argument('menu_name', type=str,)
menusArgs.add_argument('description', type=str,)
menusArgs.add_argument('priceist', type=str,)

@menus.route("")
class Menus(Resource):
    # @menus.expect(menusArgs)
    def get(self):
        conn = pool.get_connection()
        cur = conn.cursor(cursor_factory=DictCursor)
        try:
            cur.execute(
                '''
                    SELECT * FROM menu where is_deleted = '001002'
                ''') 
            res = cur.fetchall()
            cur.close()
            result = []
            for row in res:
                transformed_row = {"menu_id": row["menu_id"], "menu_name": row["menu_name"], "pricelist": row["pricelist"], "description": row["description"]}
                result.append(transformed_row)

            return jsonify(result) 
            # return jsonify()
        except Exception as e:
                return {"error": str(e)}, 500
        finally:
            if cur is not None:
                cur.close()
            if conn is not None:
                pool.return_connection(conn)
    
    @menus.expect(menusArgs)
    def post(self):
        conn = pool.get_connection()
        cur = conn.cursor()
        args = menusArgs.parse_args()
        try:
            cur.execute(
                """
                    INSERT into menu
                    (
                        menu_name,
                        description, 
                        is_deleted, 
                        created_at, 
                        pricelist
                    )
                    VALUES 
                    (
                        %(menu_name)s, 
                        %(description)s,
                        '001002', 
                        'now()', 
                        %(priceist)s
                    )
                    """, 
                args
                ) 
            conn.commit()
            return jsonify({"status": "success"})
        except Exception as e:
                return {"error": str(e)}, 500
        finally:
            if cur is not None:
                cur.close()
            if conn is not None:
                pool.return_connection(conn)
    
    # @menus.expect(menusArgs)
@menus.route("/<int:menu_id>")
class DeleteMenu(Resource):
    def put(self, menu_id):
        conn = pool.get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                """
                   update
                        public.menu
                    set
                        is_deleted = '001001'
                    where
                        menu_id = %s
                    """, 
                (menu_id,)
                ) 
            conn.commit()
            return jsonify({"status": "success"})
        except Exception as e:
                return {"error": str(e)}, 500
        finally:
            if cur is not None:
                cur.close()
            if conn is not None:
                pool.return_connection(conn)

    def get(self, menu_id):
        conn = pool.get_connection()
        cur = conn.cursor(cursor_factory=DictCursor)
        try:
            cur.execute(
                '''
                    SELECT * FROM menu where is_deleted = '001002' AND menu_id = %s
                ''',(menu_id,)) 
            res = cur.fetchone()
            cur.close()
            # result = []
            if res:  # Check if res is not None
                transformed_row = {
                    "menu_id": res["menu_id"],
                    "menu_name": res["menu_name"],
                    "pricelist": res["priceist"],
                    "description": res["description"]
                }
                return jsonify(transformed_row)
            else:
                return jsonify({})  # Return empty object if no data found
            # return jsonify()
        except Exception as e:
                return {"error": str(e)}, 500
        finally:
            if cur is not None:
                cur.close()
            if conn is not None:
                pool.return_connection(conn)
    
@menus.expect(menusArgs)
@menus.route("/update/<int:menu_id>")
class UpdatedMenu(Resource):
    def put(self, menu_id):
        conn = pool.get_connection()
        cur = conn.cursor()
        args = menusArgs.parse_args()
        print(args['menu_name'])
        try:
            cur.execute(
                """
                   update
                        public.menu
                    set
                        priceist = %s,
                        description = %s,
                        menu_name = %s
                    where
                        menu_id = %s
                    """, 
                (args['priceist'], args['description'], args['menu_name'], menu_id,)
                ) 
            conn.commit()
            return jsonify({"status": "success"})
        except Exception as e:
                return {"error": str(e)}, 500
        finally:
            if cur is not None:
                cur.close()
            if conn is not None:
                pool.return_connection(conn)
    