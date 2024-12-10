from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_db_connection
from utils import generate_dummy_products
from datetime import datetime
import random
import stripe

app = Flask(__name__)
app.secret_key = 'your_secret_key'

stripe.api_key = "sk_test_51QRhfsLEpW261ZraxSLaY2quZOypkfcO9cSgWkRAqtulbCsJ1ebWoQMMHmGnWN21IJcohXJBpMxpr9lzBDyGGJxf00mgEVmxVF"  # Replace with your Stripe secret key

products = generate_dummy_products()

@app.route('/')
def home():
    cart_count = sum(item['quantity'] for item in session.get('cart', []))
    return render_template('home.html', cart_count=cart_count)

@app.route('/products')
def products_page():
    conn = get_db_connection()
    products = conn.execute('SELECT * FROM products').fetchall()
    conn.close()
    cart_count = sum(item['quantity'] for item in session.get('cart', []))
    return render_template('products.html', products=products, cart_count=cart_count)

@app.route('/account', methods=['GET', 'POST'])
def account():
    if request.method == 'POST':
        email = request.form['custemail']
        password = request.form['custpassword']
        username = request.form['username']
        if len(password) < 8:
            flash('Password must be at least 8 characters.')
            return redirect(url_for('account'))
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        conn = get_db_connection()
        conn.execute('INSERT INTO users (username, email, password) VALUES (?, ?, ?)',
                     (username, email, hashed_password))
        conn.commit()
        conn.close()

        flash('Account created successfully!')
        return redirect(url_for('account'))

    if 'user_id' in session:
        conn = get_db_connection()
        orders = conn.execute('SELECT * FROM orders WHERE username = ?', (session['username'],)).fetchall()
        order_items = {}
        for order in orders:
            items = conn.execute('SELECT * FROM order_items WHERE order_id = ?', (order['id'],)).fetchall()
            order_items[order['id']] = items
        cart = session.get('cart', [])
        conn.close()
        # Aggregate cart items
        aggregated_cart = {}
        for item in cart:
            key = (item['product_id'], item['size'])
            if key in aggregated_cart:
                aggregated_cart[key]['quantity'] += item['quantity']
            else:
                aggregated_cart[key] = item
        cart = list(aggregated_cart.values())
        cart_count = sum(item['quantity'] for item in cart)
        total_price_cents = sum(item['quantity'] * item['price'] for item in cart)
        total_price = total_price_cents / 100.0  # Convert to dollars
        print('Total price:', total_price)  # Debugging print statement
        return render_template('account.html', orders=orders, order_items=order_items, cart=cart, cart_count=cart_count, total_price=total_price)

    return render_template('account.html', cart_count=0)

@app.route('/login', methods=['POST'])
def login():
    email = request.form['custemail']
    password = request.form['custpassword']
    current_cart = session.get('cart', [])
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    conn.close()

    if user and check_password_hash(user['password'], password):
        session['user_id'] = user['id']
        session['username'] = user['username']
        # Merge current session cart with user's saved cart
        session['cart'] = user['cart_content'] if user['cart_content'] else []
        session['cart'].extend(current_cart)
        flash('Login successful!')
        print('User logged in:', session['username'])
        print('Cart contents:', session['cart'])
        return redirect(url_for('account'))
    else:
        flash('Invalid login credentials.')
        print('Invalid login attempt for email:', email)
        return redirect(url_for('account'))

@app.route('/logout')
def logout():
    print('User logged out:', session.get('username'))
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('cart', None)
    flash('You have been logged out.')
    return redirect(url_for('home'))

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    product_id = request.form['product_id']
    size = request.form['size']
    quantity = int(request.form['quantity'])

    conn = get_db_connection()
    product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    conn.close()

    if size == 'S' and product['size_s_quant'] < quantity:
        flash(f'Not enough stock for {product["title"]} (Size S)')
    elif size == 'M' and product['size_m_quant'] < quantity:
        flash(f'Not enough stock for {product["title"]} (Size M)')
    elif size == 'L' and product['size_l_quant'] < quantity:
        flash(f'Not enough stock for {product["title"]} (Size L)')
    else:
        cart = session.get('cart', [])
        item_found = False
        for item in cart:
            if item['product_id'] == product_id and item['size'] == size:
                item['quantity'] += quantity
                item_found = True
                break
        if not item_found:
            cart.append({
                'product_id': product_id,
                'size': size,
                'quantity': quantity,
                'price': product['price']  # Include the price here
            })
        session['cart'] = cart
        flash('Product added to cart!')
        print('Product added to cart:', product['title'], 'Size:', size, 'Quantity:', quantity, 'Price:', product['price'])
        print('Current cart:', session['cart'])

    return redirect(url_for('products_page'))

@app.route('/update_cart', methods=['POST'])
def update_cart():
    product_id = request.form['product_id']
    size = request.form['size']
    quantity = int(request.form['quantity'])

    cart = session.get('cart', [])
    conn = get_db_connection()
    product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    conn.close()

    if size == 'S' and product['size_s_quant'] < quantity:
        flash(f'Not enough stock for {product["title"]} (Size S)')
    elif size == 'M' and product['size_m_quant'] < quantity:
        flash(f'Not enough stock for {product["title"]} (Size M)')
    elif size == 'L' and product['size_l_quant'] < quantity:
        flash(f'Not enough stock for {product["title"]} (Size L)')
    else:
        for item in cart:
            if item['product_id'] == product_id and item['size'] == size:
                item['quantity'] = quantity
                item['price'] = product['price']  # Ensure price is maintained
                print('Cart item updated:', item)
                break

        # Remove items with zero quantity
        cart = [item for item in cart if item['quantity'] > 0]
        session['cart'] = cart
        flash('Cart updated!')
        print('Cart updated:', session['cart'])

    return redirect(url_for('account'))

@app.route('/place_order', methods=['POST'])
def place_order():
    if 'user_id' not in session:
        flash('Please log in to place an order.')
        return redirect(url_for('account'))

    cart = session.get('cart', [])
    if not cart:
        flash('Your cart is empty.')
        return redirect(url_for('products_page'))

    try:
        total_amount_cents = sum(item['quantity'] * item['price'] for item in cart)
        total_amount = total_amount_cents / 100.0  # Convert to dollars

        conn = get_db_connection()
        order_number = str(datetime.now().timestamp()).replace('.', '') + str(random.randint(1000, 9999))
        conn.execute('INSERT INTO orders (order_number, username, date_ordered) VALUES (?, ?, ?)',
                     (order_number, session['username'], datetime.now()))
        order_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]

        for item in cart:
            conn.execute('INSERT INTO order_items (order_id, product_id, quantity, size, price) VALUES (?, ?, ?, ?, ?)',
                         (order_id, item['product_id'], item['quantity'], item['size'], item['price']))

        conn.commit()
        conn.close()

        # Redirect to the payment page with the total amount
        return redirect(url_for('payment', total_amount=total_amount))
    except Exception as e:
        flash('An error occurred with the cart items. Please try again.')
        print('Error in place_order:', e)
        return redirect(url_for('account'))

@app.route('/order/<int:order_id>')
def order_details(order_id):
    conn = get_db_connection()
    order = conn.execute('SELECT * FROM orders WHERE id = ?', (order_id,)).fetchone()
    conn.close()

    cart_count = sum(item['quantity'] for item in session.get('cart', []))

    if order:
        return render_template('order_details.html', order=order, cart_count=cart_count)
    else:
        flash('Order not found.')
        return redirect(url_for('account'))

# Payment routes
@app.route('/payment')
def payment():
    total_amount = request.args.get('total_amount', type=float)
    if total_amount is None:
        flash('Invalid payment amount.')
        return redirect(url_for('products_page'))

    cart = session.get('cart', [])
    if not cart:
        flash('Your cart is empty.')
        return redirect(url_for('products_page'))

    total_amount_cents = int(total_amount * 100)  # Convert to cents
    cart_count = sum(item['quantity'] for item in cart)
    print('Total amount (payment):', total_amount)  # Debugging print statement
    return render_template('payment.html', total_amount=total_amount, cart_count=cart_count)


@app.route('/create-payment-intent', methods=['POST'])
def create_payment():
    data = request.get_json()
    amount = data.get('amount')

    # Create a payment intent using Stripe
    try:
        intent = stripe.PaymentIntent.create(
            amount=int(amount * 100),  # Convert to cents
            currency='usd',
            payment_method_types=['card'],
        )
        print('Payment intent created:', intent)
        return jsonify(client_secret=intent.client_secret)
    except Exception as e:
        print('Error creating payment intent:', str(e))
        return jsonify(error=str(e))


@app.route('/payment-success', methods=['POST'])
def payment_success():
    cart = session.get('cart', [])
    conn = get_db_connection()

    # Update stock levels
    for item in cart:
        if item['size'] == 'S':
            conn.execute('UPDATE products SET size_s_quant = size_s_quant - ? WHERE id = ?',
                         (item['quantity'], item['product_id']))
        elif item['size'] == 'M':
            conn.execute('UPDATE products SET size_m_quant = size_m_quant - ? WHERE id = ?',
                         (item['quantity'], item['product_id']))
        elif item['size'] == 'L':
            conn.execute('UPDATE products SET size_l_quant = size_l_quant - ? WHERE id = ?',
                         (item['quantity'], item['product_id']))

    conn.commit()
    conn.close()

    # Clear the cart
    session['cart'] = []

    # Redirect to home page
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
