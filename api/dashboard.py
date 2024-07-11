from flask import Flask, render_template, request, redirect, url_for, jsonify, current_app, Blueprint
import psycopg2 
from flask_restx import Namespace, Resource, reqparse
from .db import pool

menus = Namespace("dashboard", description= "Menus's APIS Namespace")

@menus.route("/sales-trend")
class SalesTrend(Resource):
    def get(self):
        conn = pool.get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                '''
                select
                    c.cust_name,
                    code_value(t.transaction_type, 'eng') as transaction_type,
                    code_value(t.transaction_status, 'eng') as transaction_type,
                    od.req_date_order,
                    od.address_order,
                    array_agg(m.menu_name) as menus  
                from
                    "order" o
                join order_detail od on
                    od.order_id = o.order_id
                join customer c on c.customer_id = od.customer_id 
                join "transaction" t on od.transaction_id = t.transaction_id 
                join menu m on m.menu_id  = o.menu_id 
                group by c.cust_name, t.transaction_type, t.transaction_status, od.order_detail_id  
                order by
                    od.created_at desc
                ''') 
            res = cur.fetchall()
            cur.close()
            return jsonify(res)
        except Exception as e:
                return {"error": str(e)}, 500
        finally:
            if cur is not None:
                cur.close()
            if conn is not None:
                pool.return_connection(conn)
    