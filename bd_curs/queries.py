# queries.py
import pandas as pd
from db import database_connection

def view_table(role, table_name):
    with database_connection(role) as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM candy_factory.{table_name}")
        rows = cursor.fetchall()
        df = pd.DataFrame(rows, columns=[i[0] for i in cursor.description])
    return df

def execute_query(role, query):
    with database_connection(role) as conn:
        cursor = conn.cursor()
        cursor.execute(query)
        result = cursor.fetchone()
    return result

def execute_best_price_weight_ratio_query(role, query):
    import matplotlib.pyplot as plt
    import io
    with database_connection(role) as conn:
        cursor = conn.cursor()
        cursor.execute(query)
        result = cursor.fetchone()
        result_row = result[0]
        orders = result_row.split(', ')
        order_ids = []
        ratios = []
        for order in orders:
            order_id, ratio = order.split(': ')
            order_ids.append(order_id)
            ratios.append(float(ratio))
        plt.figure(figsize=(10, 5))
        plt.bar(order_ids, ratios, color='skyblue')
        plt.xlabel('ID заказа')
        plt.ylabel('Соотношение цена/вес')
        plt.title('Лучшее соотношение цена/вес для заказов')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        plt.close()
    return buf