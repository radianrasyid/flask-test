from flask import Flask, render_template, request, redirect, url_for, jsonify, current_app, Blueprint
import psycopg2 
from flask_restx import Namespace, Resource, reqparse
# from db import pool
from .db import pool

from psycopg2.extras import DictCursor

dash = Namespace("dashboard", description= "Dashboard's APIS Namespace")

@dash.route("/last-order")
class LastOrder(Resource):
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
    
@dash.route("/top-selling")
class LastOrder(Resource):
    def get(self):
        conn = pool.get_connection()
        cur = conn.cursor(cursor_factory=DictCursor)
        try:
            cur.execute(
                '''
                select
                    m.menu_name,
                    count("order".menu_id) as order_count
                from
                    "order"
                join menu m on
                    m.menu_id = "order".menu_id
                group by
                    "order".menu_id,
                    m.menu_name
                order by
                    order_count desc
                limit 3
                ''') 
            res = cur.fetchall()
            cur.close()
            result = []
            for row in res:
                transformed_row = {"menu_name": row["menu_name"], "order_count": row["order_count"]}
                result.append(transformed_row)
            return jsonify(result)
        except Exception as e:
                return {"error": str(e)}, 500
        finally:
            if cur is not None:
                cur.close()
            if conn is not None:
                pool.return_connection(conn)
    
@dash.route("/sales-summary")
class LastOrder(Resource):
    def get(self):
        conn = pool.get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                '''
               with menu_pricelist as (
                select
                    m.menu_id,
                    menu_name,
                    cast(m.priceist as integer) as priceist
                from
                    menu m
                ),
                order_summary as (
                select
                    mp.menu_name,   
                    count(o.menu_id) as order_menu,
                    mp.priceist,
                    count(o.menu_id) * mp.priceist as total_price,
                    AVG(count(o.menu_id) * mp.priceist) OVER () AS average_total_price
                from
                    "order" o
                join menu_pricelist mp on
                    mp.menu_id = o.menu_id
                group by
                    mp.menu_name,
                    mp.priceist,
                    mp.menu_id 
                )
                select
                    sum(os.total_price) as total,
                    sum(os.order_menu) as order,
                    os.average_total_price
                from
                    order_summary os
                group by
                    average_total_price
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
    
@dash.route("/bar-chart")
class BarChart(Resource):
    def get(self):
        conn = pool.get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                '''
               select
                    array_agg(count_) as count_array,
                    array_agg(menu_name) as menu_name_array
                from
                    (
                        select
                            count(quantity) as count_,
                            o.menu_id,
                            m.menu_name
                        from
                            "order" o
                        join menu m on
                            m.menu_id = o.menu_id
                        group by
                            o.menu_id,
                            m.menu_name
                    ) as sub
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
    
@dash.route("/card-information")
class CardCustomer(Resource):
    def get(self):
        conn = pool.get_connection()
        cur = conn.cursor()
        try:
            result = []
            
            # Execute the first query to get the total number of customers
            cur.execute('''SELECT COUNT(customer_id) AS total_cust FROM customer where customer.is_deleted = '001002' ''')
            total_customer = cur.fetchone()[0]
            result.append({
                'total': total_customer,
                'name': 'Customer',
                'desc': 'Total Customer per Month'
            })

            # Execute the second query to get the total number of orders
            cur.execute('''SELECT COUNT(order_detail_id) AS total_order FROM order_detail where order_detail.is_deleted = '001002' ''')
            total_order = cur.fetchone()[0]
            result.append({
                'total': total_order,
                'name': 'Order',
                'desc': 'Total Order per Month'
            })

            # Execute the third query to get the total number of orders by status
            cur.execute('''
                SELECT order_status, COUNT(order_status) as total_order_status, code_value(order_status, 'eng') as order_status_desc
                FROM order_detail
                where order_detail.is_deleted = '001002'
                GROUP BY order_status
            ''')
            total_order_status = cur.fetchall()
            
            # Append each status result separately
            for row in total_order_status:
                result.append({
                    'total': row[1],
                    'name': row[2],
                    'desc': 'Total Order Status per Month',
                    'icon': "ri-checkbox-circle-line",
                    'color': "success",
                    'width': "70"
                })

            return jsonify(result)
        
        except Exception as e:
            return {"error": str(e)}, 500
        
        finally:
            # Ensure the cursor and connection are properly closed
            if cur is not None:
                cur.close()
            if conn is not None:
                pool.return_connection(conn)

@dash.route("/notification")
class Notification(Resource):
    # @menus.expect(menusArgs)
    def get(self):
        conn = pool.get_connection()
        cur = conn.cursor(cursor_factory=DictCursor)
        try:
            cur.execute(
                '''
                    SELECT lg.message, c.cust_name, lg.created_at::date, log_order_id
                    FROM log_order lg join order_detail od on od.order_detail_id = lg.order_detail_id 
                    join customer c on c.customer_id = od.customer_id order by log_order_id desc limit 4
                ''') 
            res = cur.fetchall()
            cur.close()
            result = []
            for row in res:
                transformed_row = {"log_order_id": row["log_order_id"], "message": row["message"], "created_at": row["created_at"], "cust_name": row["cust_name"]}
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
    