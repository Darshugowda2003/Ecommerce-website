from flask import Flask, jsonify, request, render_template, redirect, session, url_for, flash
import sqlite3 as sql
from werkzeug.security import generate_password_hash, check_password_hash

UPLOADS_PATH = 'static/images'

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super secret key'

def get_db_connection():
    conn = sql.connect('app_data.db')
    conn.row_factory = sql.Row
    return conn

# Helper function to authenticate admin
def authenticate_admin(email, password):
    valid_admins = {
        'darsugowda2003@gmail.com': 'darshu@2003',
        'darshugowda2905@gmail.com': 'darshan@2003'
    }
    if email in valid_admins and valid_admins[email] == password:
        return True
    return False

# Function to get user details by user_id
def get_user_by_id(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    user = cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchall()
    cursor.close()
    conn.close()
    return user

# Function to update user details
def update_user_details(user_id, aadhar_card_number, address, card_details, phone_number):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE users
        SET aadhar_card_number = ?,
            address = ?,
            card_details = ?,
            phone_number = ?
        WHERE id = ?
    ''', (aadhar_card_number, address, card_details, phone_number, user_id))
    conn.commit()
    cursor.close()
    conn.close()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/renting")
def renting():
    return render_template("renting.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contact", methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        message = request.form['message']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO contacts (first_name, last_name, email, message)
            VALUES (?, ?, ?, ?)
        ''', (first_name, last_name, email, message))
        conn.commit()
        cursor.close()
        conn.close()

        return redirect('/thank_you')
    return render_template("contact.html")

@app.route("/login_signup", methods=['GET', 'POST'])
def login_signup():
    if request.method == 'POST':
        action = request.form['action']
        email = request.form['email']
        password = request.form['password']
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if action == 'login':
            user = cursor.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
            if user and check_password_hash(user['password'], password):
                session['user_id'] = user['id']
                flash('Login successful!', 'success')
                return redirect(url_for('index'))
            else:
                flash('Login failed. Check your email and password.', 'danger')
        
        elif action == 'signup':
            full_name = request.form['full_name']
            aadhar_card_number = request.form.get('aadhar_card_number')
            address = request.form.get('address')
            card_details = request.form.get('card_details')
            phone_number = request.form.get('phone_number')
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
            try:
                cursor.execute('''
                    INSERT INTO users (full_name, email, password, aadhar_card_number, address, card_details, phone_number)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (full_name, email, hashed_password, aadhar_card_number, address, card_details, phone_number))
                conn.commit()
                flash('Account created successfully!', 'success')
                return redirect(url_for('index'))
            except sql.IntegrityError:
                flash('Account with this email already exists.', 'danger')
        
        cursor.close()
        conn.close()

    return render_template("login_signup.html")

@app.route('/admin_auth', methods=['GET', 'POST'])
def admin_auth():
    if request.method == 'POST':
        admin_email = request.form['admin_email']
        admin_password = request.form['admin_password']

        if authenticate_admin(admin_email, admin_password):
            session['admin_logged_in'] = True
            flash('Admin login successful!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Admin login failed. Check your credentials.', 'danger')

    return render_template("admin_auth.html")

@app.route('/admin_dashboard')
def admin_dashboard():
    if 'admin_logged_in' not in session:
        flash('Please log in as admin to view this page.', 'warning')
        return redirect(url_for('admin_auth'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    users = cursor.execute('SELECT * FROM users').fetchall()
    orders = cursor.execute('SELECT * FROM orders').fetchall()
    contacts = cursor.execute('SELECT * FROM contacts').fetchall()
    cursor.close()
    conn.close()

    return render_template("admin_dashboard.html", users=users, orders=orders, contacts=contacts)



@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('admin_logged_in', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/cart')
def cart():
    cart_items = session.get('cart', [])
    cart_total = sum(int(item['price']) for item in cart_items)
    return render_template('cart.html', cart_items=cart_items, cart_total=cart_total)

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    item_name = request.form.get('item_name')
    item_price = request.form.get('item_price')
    item_image = request.form.get('item_image')
    
    cart = session.get('cart', [])
    cart.append({'name': item_name, 'price': item_price, 'image': item_image})
    session['cart'] = cart
    
    return redirect(url_for('cart'))

@app.route('/remove_from_cart', methods=['POST'])
def remove_from_cart():
    item_name = request.form.get('item_name')
    item_price = request.form.get('item_price')
    item_image = request.form.get('item_image')
    
    cart = session.get('cart', [])
    cart = [item for item in cart if item['name'] != item_name]
    session['cart'] = cart
    
    return redirect(url_for('cart'))

@app.route('/confirm_order', methods=['POST'])
def confirm_order():
    payment_method = request.form.get('payment_method')
    if not payment_method:
        return jsonify(message="Please select a payment method."), 400
    
    user_id = session.get('user_id')
    if user_id:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO orders (user_id, payment_method)
            VALUES (?, ?)
        ''', (user_id, payment_method))
        conn.commit()
        cursor.close()
        conn.close()
    
    session.pop('cart', None)
    return jsonify(message='Your order has been placed successfully with payment method: ' + payment_method)

@app.route("/main")
def main():
    return render_template("main.html")

@app.route('/account', methods=['GET', 'POST'])
def account():
    user_id = session.get('user_id')
    if not user_id:
        flash('You need to log in to access your account.', 'danger')
        return redirect(url_for('login_signup'))

    user = get_user_by_id(user_id)

    if request.method == 'POST':
        aadhar_card_number = request.form.get('aadhar_card_number')
        address = request.form.get('address')
        card_details = request.form.get('card_details')
        phone_number = request.form.get('phone_number')

        update_user_details(user_id, aadhar_card_number, address, card_details, phone_number)
        flash('Your account details have been updated.', 'success')
        user = get_user_by_id(user_id)  # Refresh user data after update

    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('login_signup'))
    
    return render_template("account.html", user=user)

@app.route("/thank_you")
def thank_you():
    return "Thank you for your message!"

if __name__ == "__main__":
    app.run(debug=True)
