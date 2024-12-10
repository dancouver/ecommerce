import sqlite3

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    conn = get_db_connection()
    conn.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        cart_content TEXT,
        current_orders TEXT
    )
    ''')
    conn.execute('''
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_number INTEGER,
        username TEXT,
        date_ordered TEXT,
        product_1 TEXT,
        quantity_1 INTEGER,
        size_1 TEXT,
        product_2 TEXT,
        quantity_2 INTEGER,
        size_2 TEXT,
        product_3 TEXT,
        quantity_3 INTEGER,
        size_3 TEXT
    )
    ''')
    conn.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY,
        thumbnail_url TEXT,
        title TEXT,
        desc TEXT,
        size_s_quant INTEGER,
        size_m_quant INTEGER,
        size_l_quant INTEGER,
        delivery_time INTEGER,
        price REAL
    )
    ''')
    conn.commit()
    conn.close()

def populate_products(products):
    conn = get_db_connection()
    for product in products:
        conn.execute('INSERT INTO products (id, thumbnail_url, title, desc, size_s_quant, size_m_quant, size_l_quant, delivery_time, price) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                     (product['id'], product['thumbnail_url'], product['title'], product['desc'], product['size_s_quant'], product['size_m_quant'], product['size_l_quant'], product['delivery_time'], product['price']))
    conn.commit()
    conn.close()
