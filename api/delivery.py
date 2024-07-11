from flask import Flask, render_template, request, redirect, url_for, jsonify, current_app, Blueprint
import psycopg2 
from flask_restx import Namespace, Resource, reqparse
import argparse
from .db import pool
from psycopg2.extras import DictCursor


delivery = Namespace("delivery", description= "Menus's APIS Namespace")

deliveryArgs = reqparse.RequestParser()
# transactionArgs.add_argument('rate', type=int, help='Rate cannot be converted')
deliveryArgs.add_argument('delivery_type', type=str,)
deliveryArgs.add_argument('delivery_status', type=str,)

@delivery.route("")
class Transaction(Resource):
    def get(self):
        if pool:
            print('succes')
        else:
            print('nope')
        conn = pool.get_connection()
        cur = conn.cursor(cursor_factory=DictCursor)
        try:
            cur.execute(
                '''
                    SELECT 
                        d.delivery_status,
                        d.delivery_type,
                        code_value(d.delivery_status, 'eng') as delivery_status_name,
                        code_value(d.delivery_type, 'eng') as delivery_type_name,
                        c.cust_name,
                        d.updated_time,
                        d.order_detail_id
                    FROM delivery d
                    JOIN order_detail od on od.order_detail_id = d.order_detail_id
                    JOIN customer c on c.customer_id = od.customer_id
                    order by delivery_id desc
                ''') 
            res = cur.fetchall()

            result = []
            for row in res:
                transformed_row = {
                                   "delivery_status": row['delivery_status'],
                                   "delivery_type": row['delivery_type'],
                                   "delivery_status_name": row['delivery_status_name'],
                                   "delivery_type_name": row['delivery_type_name'],
                                   "cust_name": row["cust_name"],
                                   "updated_time": row["updated_time"],                               
                                   "order_detail_id": row["order_detail_id"]                                   
                                   }
                result.append(transformed_row)
                
            return jsonify(result)
        except Exception as e:
            return {"error": str(e)}, 500
        finally:
            if cur is not None:
                cur.close()
            if conn is not None:
                pool.return_connection(conn)

# @delivery.expect(transactionArgs)       
@delivery.route('/edit-delivery/<int:order_detail_id>')
class TransactionStatus(Resource):
    def put(self, order_detail_id):
        if pool:
            print('succes')
        else:
            print('nope')
        conn = pool.get_connection()
        cur = conn.cursor(cursor_factory=DictCursor)
        args = deliveryArgs.parse_args()
        try:
            cur.execute(
                """
                update 
                    delivery 
                set 
                    delivery_type = %s,
                    delivery_status = %s,
                    updated_time = 'now()'
                where 
                    order_detail_id = %s            
                """,
                (args['delivery_type'], args['delivery_status'], order_detail_id,)
            )
            conn.commit()

            cur.execute(
                """
                select 
                    c.cust_name
                from order_detail od join customer c on c.customer_id = od.customer_id
                where 
                    order_detail_id = %s     
                """,
                (order_detail_id,)
            )

            cust_name = cur.fetchone()[0]
            message = 'Update Delivery from {}'.format(cust_name)
            cur.execute(
                """
                INSERT
                    into public.log_order (
                    message, order_detail_id
                )
                VALUES (%s, %s);

                """,
                (message, order_detail_id,)
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