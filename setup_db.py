import sqlite3

connection = sqlite3.connect('database.db')

with open('schema.sql') as f:
    connection.executescript(f.read())

cur = connection.cursor()

# Create dummy data for products table
products = [
    ('Product 1', 'Description 1', 'thumbnail1.png', 10, 15, 20, 500, 1),
    ('Product 2', 'Description 2', 'thumbnail2.png', 5, 10, 15, 1000, 2),
    ('Product 3', 'Description 3', 'thumbnail3.png', 8, 12, 18, 750, 3),
]

for product in products:
    cur.execute('INSERT INTO products (title, desc, thumbnail_url, size_s_quant, size_m_quant, size_l_quant, price, delivery_time) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', product)

connection.commit()
connection.close()
