from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a secure secret key

# Database initialization
conn = sqlite3.connect('database.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users 
(id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, password TEXT, role TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS products 
(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, category TEXT, barcode TEXT, description TEXT, vendor TEXT, manufacturer TEXT, price REAL, discount REAL, tax REAL, image_url TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS sales 
(id INTEGER PRIMARY KEY AUTOINCREMENT, product_id INTEGER quantity INTEGER, date TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS categories 
(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS payments 
(id INTEGER PRIMARY KEY AUTOINCREMENT, sales_id INTEGER, amount REAL, date TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS customers 
(id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT, phone TEXT, segment TEXT, location TEXT, gender TEXT, contact_person TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS invoices 
(id INTEGER PRIMARY KEY, customer_id INTEGER, product_id INTEGER, quantity INTEGER, date TEXT, type TEXT, FOREIGN KEY (customer_id) REFERENCES customers (id), FOREIGN KEY (product_id) REFERENCES products (id))''')
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
        return render_template('base.html', username=session['username'], role=get_user_role(), is_logged_in=is_logged_in)
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
        return render_template('sales_and_payments.html', data=sales_and_payments, is_logged_in=is_logged_in)
    else:
        return redirect(url_for('login'))
        
# Route for listing all products
@app.route('/products')
def products():
    if is_logged_in():
        # Fetch all products from the database
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT * FROM products")
        products = c.fetchall()
        conn.close()

        return render_template('products.html', products=products, is_logged_in=is_logged_in)
    else:
        return redirect(url_for('login'))

# Configuration for file uploads
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# Route for creating products
@app.route('/create_product', methods=['GET', 'POST'])
def create_product():
    if is_logged_in():
        if request.method == 'POST':
            name = request.form['name']
            price = request.form['price']
            category = request.form['category']
            barcode = request.form['barcode']
            description = request.form['description']
            vendor = request.form['vendor']
            manufacturer = request.form['manufacturer']
            discount = request.form['discount']
            tax = request.form['tax']
            image = request.files['image']

            # Save the product to the database
            conn = sqlite3.connect('database.db')
            c = conn.cursor()
            c.execute("INSERT INTO products (name, price, category, barcode, description, vendor, manufacturer, discount, tax, image_url) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                      (name, price, category, barcode, description, vendor, manufacturer, discount, tax, image.filename))
            conn.commit()
            conn.close()

            # Save the image file
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(image.filename)))

            return redirect(url_for('home'))

        # Fetch categories from the database
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT * FROM categories")
        categories = c.fetchall()
        conn.close()
        return render_template('create_product.html', categories=categories, is_logged_in=is_logged_in)
    else:
        return redirect(url_for('login'))
@app.route('/edit_product/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    if is_logged_in():
        if request.method == 'POST':
            name = request.form['name']
            price = request.form['price']

            # Update the product in the database
            conn = sqlite3.connect('database.db')
            c = conn.cursor()
            c.execute("UPDATE products SET name=?, price=? WHERE id=?", (name, price, product_id))
            conn.commit()
            conn.close()

            return redirect(url_for('products'))

        # Fetch the product details from the database
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT * FROM products WHERE id=?", (product_id,))
        product = c.fetchone()
        conn.close()

        return render_template('edit_product.html', product=product, is_logged_in=is_logged_in)
    else:
        return redirect(url_for('login'))
@app.route('/delete_product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    if is_logged_in():
        # Delete the product from the database
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("DELETE FROM products WHERE id=?", (product_id,))
        conn.commit()
        conn.close()

        return redirect(url_for('products'))
    else:
        return redirect(url_for('login'))
# Route for listing all categories
@app.route('/categories')
def categories():
    if is_logged_in():
        # Fetch all categories from the database
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT * FROM categories")
        categories = c.fetchall()  # Fetch categories, not products
        conn.close()

        return render_template('categories.html', categories=categories, is_logged_in=is_logged_in)
    else:
        return redirect(url_for('login'))
# Route for creating a new category
@app.route('/create_category', methods=['GET', 'POST'])
def create_category():
    if is_logged_in():
        if request.method == 'POST':
            name = request.form['name']

            # Save the new category to the database
            conn = sqlite3.connect('database.db')
            c = conn.cursor()
            c.execute("INSERT INTO categories (name) VALUES (?)", (name,))
            conn.commit()
            conn.close()

            return redirect(url_for('categories'))

        return render_template('create_category.html',  is_logged_in=is_logged_in)
    else:
        return redirect(url_for('login'))

# Route for editing an existing category
@app.route('/edit_category/<int:category_id>', methods=['GET', 'POST'])
def edit_category(category_id):
    if is_logged_in():
        if request.method == 'POST':
            name = request.form['name']

            # Update the category in the database
            conn = sqlite3.connect('database.db')
            c = conn.cursor()
            c.execute("UPDATE categories SET name=? WHERE id=?", (name, category_id))
            conn.commit()
            conn.close()

            return redirect(url_for('categories'))

        # Fetch the category details from the database
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT * FROM categories WHERE id=?", (category_id,))
        category = c.fetchone()
        conn.close()

        return render_template('edit_category.html', category=category)
    else:
        return redirect(url_for('login'))

# Route for deleting a category
@app.route('/delete_category/<int:category_id>', methods=['POST'])
def delete_category(category_id):
    if is_logged_in():
        # Delete the category from the database
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("DELETE FROM categories WHERE id=?", (category_id,))
        conn.commit()
        conn.close()

        return redirect(url_for('categories'))
    else:
        return redirect(url_for('login'))
# Routes for listing all invoices and all customers
@app.route('/invoices')
def invoices():
    if is_logged_in():
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT * FROM invoices")
        invoices = c.fetchall()
        conn.close()
        return render_template('invoices.html', invoices=invoices, is_logged_in=is_logged_in())
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
            invoice_type = request.form['type']  # Assuming a form field named 'type' to select invoice type
            conn = sqlite3.connect('database.db')
            c = conn.cursor()
            c.execute("INSERT INTO invoices (product_id, quantity, date, type) VALUES (?, ?, ?, ?)",
                      (product_id, quantity, date, invoice_type))
            conn.commit()
            conn.close()
            return redirect(url_for('home'))
        
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT * FROM products")
        products = c.fetchall()
        conn.close()
        return render_template('create_invoice.html', products=products, is_logged_in=is_logged_in())
    else:
        return redirect(url_for('login'))
# Route for listing all customers
@app.route('/customers')
def customers():
    if is_logged_in():
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT * FROM customers")
        customers = c.fetchall()
        conn.close()
        return render_template('customers.html', customers=customers, is_logged_in=is_logged_in())
    else:
        return redirect(url_for('login'))

# Route for adding a new customer
@app.route('/add_customer', methods=['GET', 'POST'])
def add_customer():
    if is_logged_in():
        if request.method == 'POST':
            name = request.form['name']
            segment = request.form['segment']
            location = request.form['location']
            gender = request.form['gender']
            contact_person = request.form['contact_person']
            
            conn = sqlite3.connect('database.db')
            c = conn.cursor()
            c.execute("INSERT INTO customers (name, segment, location, gender, contact_person) VALUES (?, ?, ?, ?, ?)",
                      (name, segment, location, gender, contact_person))
            conn.commit()
            conn.close()
            return redirect(url_for('customers'))
        
        return render_template('add_customer.html', is_logged_in=is_logged_in())
    else:
        return redirect(url_for('login'))
# Define your route to edit a customer
@app.route('/edit_customer/<int:id>', methods=['GET', 'POST'])
def edit_customer(id):
    if is_logged_in():
        if request.method == 'POST':
            name = request.form['name']
            segment = request.form['segment']
            location = request.form['location']
            gender = request.form['gender']
            contact_person = request.form['contact_person']

            # Update the customer in the database
            conn = sqlite3.connect('database.db')
            c = conn.cursor()
            c.execute("UPDATE customers SET name=?, segment=?, location=?, gender=?, contact_person=? WHERE id=?", (name, segment, location, gender, contact_person, id))
            conn.commit()
            conn.close()

            return redirect(url_for('customers'))

        # Fetch the customer from the database
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT * FROM customers WHERE id=?", (id,))
        customer = c.fetchone()
        conn.close()

        return render_template('edit_customer.html', customer=customer, is_logged_in=is_logged_in())
    else:
        return redirect(url_for('login'))
@app.route('/delete_customer/<int:customer_id>', methods=['POST'])
def delete_customer(customer_id):
    if is_logged_in():
        # Delete the customer with the provided ID from the database
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("DELETE FROM customers WHERE id=?", (customer_id,))
        conn.commit()
        conn.close()
        # Redirect to the customers page after deletion
        return redirect(url_for('customers'))
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
        return render_template('create_payment.html', sales=sales, is_logged_in=is_logged_in)
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