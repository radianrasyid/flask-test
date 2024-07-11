from flask import Flask, render_template, request, redirect, url_for, jsonify, current_app, Blueprint
import psycopg2 
from flask_restx import Namespace, Resource, reqparse
import argparse
from .db import pool
from psycopg2.extras import DictCursor
from datetime import datetime


order = Namespace("order", description= "Menus's APIS Namespace")

orderArgs = reqparse.RequestParser()

@order.route("")
class Order(Resource):
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
                    with total_price as 
                        (
                            select
                                o.order_detail_id,
                                SUM(m.pricelist * o.quantity) as order_total
                            from
                                menu m
                            join "order" o on
                                o.menu_id = m.menu_id
                            where m.is_deleted = '001002'
                            group by o.order_detail_id
                        ) 
                            select distinct on (od.order_detail_id)
                                c.*,
                                od.*,
                                code_value(od.order_status,
                                'eng') as order_status_name,
                                array_agg(m.menu_name) as menu,
                                array_agg(o.quantity) as quantity,
                                tp.order_total as total
                            from
                                "order" o
                            join "order_detail" od on
                                o.order_detail_id = od.order_detail_id
                            join total_price tp on
                                tp.order_detail_id = od.order_detail_id
                            join transaction t on
                                t.order_detail_id = od.order_detail_id
                            join customer c on
                                c.customer_id = od.customer_id
                            join menu m on
                                m.menu_id = o.menu_id
                            where
                                od.is_deleted = '001002'
                            group by
                                od.order_detail_id,
                                c.customer_id,
                                tp.order_total
                            order by
                                od.order_detail_id desc
                ''') 
            rows = cur.fetchall()
            res = [dict(row) for row in rows]
            return jsonify(res)
        except Exception as e:
            return {"error": str(e)}, 500
        finally:
            if cur is not None:
                cur.close()
            if conn is not None:
                pool.return_connection(conn)

    # orderArgs.add_argument('rate', type=int, help='Rate cannot be converted')
    orderArgs.add_argument('cust_name', type=str)
    orderArgs.add_argument('address', type=str)
    orderArgs.add_argument('no_tlp', type=str)
    orderArgs.add_argument('order_to', type=str)
    orderArgs.add_argument('description', type=str) 
    orderArgs.add_argument('orderItems', type=list) 
    orderArgs.add_argument('deliveryType', type=str) 
    orderArgs.add_argument('deliveryStatus', type=str) 
    orderArgs.add_argument('transactionType', type=str) 
    orderArgs.add_argument('transactionStatus', type=str) 
    orderArgs.add_argument('req_date_order', type=str, location='json') 
    
    @order.expect(orderArgs)
    def post(self):
        conn = pool.get_connection()
        cur = conn.cursor()
        data = request.json
        args = orderArgs.parse_args()
        order_items = data.get('orderItems', [])
        order_data = {
            'cust_name': args['cust_name'],
            'address': args['address'],
            'address_order': args['address'],  # Set address_order sama dengan address
            'no_tlp': args['no_tlp'],
            'order_to': args['order_to'],
            'description': args['description'],
            'req_date_order': args['req_date_order'],
            'delivery_type': args['deliveryType'],
            'delivery_status': args['deliveryStatus'],
            'transaction_type': args['transactionType'],
            'transaction_status': args['transactionStatus'],
            'orderItems': order_items
        }
        print(order_data)
        
        try:
            # Insert customer and return customer_id
            cur.execute(
                """
                INSERT INTO public."customer" (cust_name, address, no_tlp)
                VALUES (%s, %s, %s)
                RETURNING customer_id
                """,
                (
                    order_data['cust_name'],
                    order_data['address'],
                    order_data['no_tlp']
                )
            )
            customer_id = cur.fetchone()[0]
            
            # Insert order detail and return order_detail_id
            cur.execute(
                """
                INSERT INTO public.order_detail (customer_id, upd_date_order, req_date_order, address_order, created_at)
                VALUES (%s, NOW(), %s, %s, NOW())
                RETURNING order_detail_id
                """,
                (
                    customer_id,
                    order_data['req_date_order'],
                    order_data['address_order']
                )
            )
            order_detail_id = cur.fetchone()[0]
            
            # Loop through orderItems and insert each one into the order table
            for item in order_items:
                cur.execute(
                    """
                    INSERT INTO public."order" (order_detail_id, menu_id, quantity, order_status)
                    VALUES (%s, %s, %s, '002001')
                    """,
                    (
                        order_detail_id,
                        item['menu_id'],
                        item['quantity']
                    )
                )
            
            # Insert into the transaction table
            cur.execute(
                """
                INSERT INTO public."transaction" (
                    transaction_id, transaction_type, transaction_status, transaction_to, order_detail_id
                )
                VALUES (
                    NEXTVAL('transaction_id_seq'), %s, %s, '004001', %s
                )
                """,
                (order_data['transaction_type'], order_data['transaction_status'], order_detail_id,)
            )
            # Insert into the delivery table
            cur.execute(
                """
                INSERT INTO public."delivery" (
                   delivery_status, delivery_type, order_detail_id
                )
                VALUES (
                   %s,  %s , %s
                )
                """,
                (order_data['delivery_status'], order_data['delivery_type'], order_detail_id,)
            )


            message = 'New order from {}, lets Check for details!'.format(order_data['cust_name'])
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
            conn.rollback()
            return jsonify({"status": "error", "message": str(e)}), 500
        
        finally:
            pool.return_connection(conn)


@order.route('/latest-order')
class LatestOrder(Resource):
    def get(self):
        if pool:
            print('succes')
            print('yaa')
        else:
            print('nope')
        conn = pool.get_connection()
        cur = conn.cursor(cursor_factory=DictCursor)
        try: 
            cur.execute(
                '''
                with total_price as 
                (
                    select
                        o.order_detail_id,
                        SUM(m.pricelist * o.quantity) as order_total
                    from
                        menu m
                    join "order" o on
                        o.menu_id = m.menu_id
                    where
                        m.is_deleted = '001002'
                    group by
                        o.order_detail_id
                ) 
                    select
                        c.cust_name,
                        od.req_date_order,
                        tp.order_total as total,
                        od.order_detail_id,
                        code_value(od.order_status, 'eng') as order_status,
                        code_value(t.transaction_status , 'eng') as transaction_status
                    from
                        order_detail od
                    join total_price tp on
                        tp.order_detail_id = od.order_detail_id
                    join customer c on c.customer_id = od.customer_id 
                    join "transaction" t on t.order_detail_id  = od.order_detail_id  
                    where  od.is_deleted = '001002'
                    order by od.upd_date_order  desc
                    limit 5
                '''
            )
            res = cur.fetchall()

            result = []
            for row in res:
                transformed_row = {"order_detail_id": row["order_detail_id"], "cust_name": row["cust_name"], "req_date_order": row["req_date_order"], "total": row["total"], "order_status": row["order_status"], "transaction_status": row["transaction_status"]}
                result.append(transformed_row)
            return jsonify(result)
        except Exception as e:
            return {"error": str(e)}, 500
        finally:
            if cur is not None:
                cur.close()
            if conn is not None:
                pool.return_connection(conn)


editStatusArgs = reqparse.RequestParser()
editStatusArgs.add_argument('address_order', type=str)
editStatusArgs.add_argument('order_status', type=str)
@order.expect(editStatusArgs)
@order.route('/edit-status/<int:order_detail_id>')
class orderStatus(Resource):
    def put(self, order_detail_id):
        if pool:
            print('succes')
            print('yaa')
        else:
            print('nope')
        conn = pool.get_connection()
        cur = conn.cursor(cursor_factory=DictCursor)
        args = editStatusArgs.parse_args()
        try:
            cur.execute(
                """
                update 
                    order_detail 
                set 
                    order_status = %s,
                    address_order = %s
                where order_detail_id = %s            
                """,
                (args['order_status'], args['address_order'], order_detail_id,)
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

@order.route("/delete-order/<int:order_detail_id>")
class DeleteOrder(Resource):
    def put(self, order_detail_id):
        conn = pool.get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                """
                   update
                        public.order_detail
                    set
                        is_deleted = '001001'
                    where
                        order_detail_id = %s
                    """, 
                (order_detail_id,)
                ) 
            
            cur.execute(
                """
                   update
                        public.transaction
                    set
                        is_deleted = '001001'
                    where
                        order_detail_id = %s
                    """, 
                (order_detail_id,)
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
