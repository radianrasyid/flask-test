from flask import Flask, render_template, request, redirect, url_for, jsonify, current_app, Blueprint
import psycopg2 
from flask_restx import Namespace, Resource, reqparse
import argparse
from .db import pool
from psycopg2.extras import DictCursor


transaction = Namespace("transaction", description= "Menus's APIS Namespace")

transactionArgs = reqparse.RequestParser()
# transactionArgs.add_argument('rate', type=int, help='Rate cannot be converted')
transactionArgs.add_argument('transaction_type', type=str,)
transactionArgs.add_argument('transaction_status', type=str,)
transactionArgs.add_argument('transaction_to', type=str,)
transactionArgs.add_argument('description', type=str,)

@transaction.route("")
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
                        t.transaction_id,
                        t.transaction_type,
                        t.transaction_status,
                        t.transaction_to,
                        t.updated_time,
                        code_value(t.transaction_type, 'eng') as transaction_type_name,
                        code_value(t.transaction_status, 'eng') as transaction_status_name,
                        code_value(t.transaction_to, 'eng') as transaction_to_name,
                        t.decscription as description,
                        c.cust_name,
                        od.order_detail_id
                    FROM transaction t
                    JOIN order_detail od on od.order_detail_id = t.order_detail_id
                    JOIN customer c on c.customer_id = od.customer_id
                    WHERE t.is_deleted = '001002'
                    order by transaction_id desc
                ''') 
            res = cur.fetchall()

            result = []
            for row in res:
                transformed_row = {
                                   "transaction_id": row["transaction_id"], 
                                   "transaction_status": row["transaction_status"], 
                                   "transaction_type": row["transaction_type"], 
                                   "transaction_to": row["transaction_to"], 
                                   "description": row["description"], 
                                   "cust_name": row["cust_name"],
                                   "transaction_type_name": row["transaction_type_name"],
                                   "transaction_status_name": row["transaction_status_name"],
                                   "transaction_to_name": row["transaction_to_name"],                               
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
    
    @transaction.expect(transactionArgs)
    def post(self):
        conn = pool.get_connection()
        cur = conn.cursor()
        args = transactionArgs.parse_args()
        try:
            cur.execute(
                    """
                    INSERT INTO public."transaction"
                    (
                        transaction_type, 
                        transaction_status, 
                        transaction_to, 
                        decscription
                    )
                    VALUES
                    (
                        %(transaction_type)s, 
                        %(transaction_status)s, 
                        %(transaction_to)s, 
                        %(description)s
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

@transaction.expect(transactionArgs)       
@transaction.route('/edit-transaction/<int:order_detail_id>')
class TransactionStatus(Resource):
    def put(self, order_detail_id):
        if pool:
            print('succes')
        else:
            print('nope')
        conn = pool.get_connection()
        cur = conn.cursor(cursor_factory=DictCursor)
        args = transactionArgs.parse_args()
        try:
            cur.execute(
                """
                update 
                    transaction 
                set 
                    transaction_type = %s,
                    transaction_status = %s,
                    transaction_to = %s
                where 
                    order_detail_id = %s            
                """,
                (args['transaction_type'], args['transaction_status'], args['transaction_to'], order_detail_id,)
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
            message = 'Update transaction from {}'.format(cust_name)
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