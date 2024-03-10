from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a secure secret key

# Database initialization
conn = sqlite3.connect('database.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, password TEXT, role TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS products 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, price REAL)''')
c.execute('''CREATE TABLE IF NOT EXISTS sales 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, product_id INTEGER, quantity INTEGER, date TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS payments 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, sales_id INTEGER, amount REAL, date TEXT)''')
conn.commit()
conn.close()

# Function to check if a user is logged in
def is_logged_in():
    return 'username' in session

# Function to get the role of the logged-in user
def get_user_role():
    if is_logged_in():
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT role FROM users WHERE username=?", (session['username'],))
        role = c.fetchone()[0]
        conn.close()
        return role
    else:
        return None

# Route for the admin panel homepage
@app.route('/')
def home():
    if is_logged_in():
        return render_template('admin_panel.html', username=session['username'], role=get_user_role())
    else:
        return redirect(url_for('login'))
 # Route for listing all sales and payments
@app.route('/sales_and_payments')
def sales_and_payments():
    if is_logged_in():
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT s.id, p.name, s.quantity, s.date, py.amount, py.date FROM sales s JOIN products p ON s.product_id = p.id LEFT JOIN payments py ON s.id = py.sales_id")
        sales_and_payments = c.fetchall()
        conn.close()
        return render_template('sales_and_payments.html', data=sales_and_payments)
    else:
        return redirect(url_for('login'))

# Route for creating products
@app.route('/create_product', methods=['GET', 'POST'])
def create_product():
    if is_logged_in():
        if request.method == 'POST':
            name = request.form['name']
            price = request.form['price']
            conn = sqlite3.connect('database.db')
            c = conn.cursor()
            c.execute("INSERT INTO products (name, price) VALUES (?, ?)", (name, price))
            conn.commit()
            conn.close()
            return redirect(url_for('home'))
        return render_template('create_product.html')
    else:
        return redirect(url_for('login'))

# Route for creating sales invoices
@app.route('/create_invoice', methods=['GET', 'POST'])
def create_invoice():
    if is_logged_in():
        if request.method == 'POST':
            product_id = request.form['product_id']
            quantity = request.form['quantity']
            date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn = sqlite3.connect('database.db')
            c = conn.cursor()
            c.execute("INSERT INTO sales (product_id, quantity, date) VALUES (?, ?, ?)", (product_id, quantity, date))
            conn.commit()
            conn.close()
            return redirect(url_for('home'))
        
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT * FROM products")
        products = c.fetchall()
        conn.close()
        return render_template('create_invoice.html', products=products)
    else:
        return redirect(url_for('login'))

# Route for creating payments
@app.route('/create_payment', methods=['GET', 'POST'])
def create_payment():
    if is_logged_in():
        if request.method == 'POST':
            sales_id = request.form['sales_id']
            amount = request.form['amount']
            date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn = sqlite3.connect('database.db')
            c = conn.cursor()
            c.execute("INSERT INTO payments (sales_id, amount, date) VALUES (?, ?, ?)", (sales_id, amount, date))
            conn.commit()
            conn.close()
            return redirect(url_for('home'))
        
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT * FROM sales")
        sales = c.fetchall()
        conn.close()
        return render_template('create_payment.html', sales=sales)
    else:
        return redirect(url_for('login'))
        
# Route to fetch sales data
@app.route('/get_sales')
def get_sales():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM sales")
    sales = c.fetchall()
    conn.close()
    sales_html = '<ul>'
    for sale in sales:
        sales_html += f'<li>{sale}</li>'
    sales_html += '</ul>'
    return sales_html

# Route to fetch payment data
@app.route('/get_payments')
def get_payments():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM payments")
    payments = c.fetchall()
    conn.close()
    payments_html = '<ul>'
    for payment in payments:
        payments_html += f'<li>{payment}</li>'
    payments_html += '</ul>'
    return payments_html

# Route to fetch online users
@app.route('/get_online_users')
def get_online_users():
    online_users = session.get('online_users', [])
    online_users_html = '<ul>'
    for user in online_users:
        online_users_html += f'<li>{user}</li>'
    online_users_html += '</ul>'
    return online_users_html


# Route for the registration form
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']  # You can add more sophisticated role management here
        
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, password, role))
        conn.commit()
        conn.close()
        
        return redirect(url_for('login'))
    return render_template('register.html')

# Route for the sign-in form
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = c.fetchone()
        conn.close()
        
        if user:
            session['username'] = user[1]
            return redirect(url_for('home'))
        else:
            return render_template('login.html', error='Invalid username or password.')
    return render_template('login.html')

# Route for logging out
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
