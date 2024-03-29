from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os
import pandas as pd
from werkzeug.utils import secure_filename
from datetime import datetime
from flask import flash
from flask_sqlalchemy import SQLAlchemy



app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a secure secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)


# Database initialization
conn = sqlite3.connect('database.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users 
(id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, password TEXT, role TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS products 
(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, category TEXT, barcode TEXT, description TEXT, vendor TEXT, manufacturer TEXT, price REAL, discount REAL, tax REAL, image_url TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS sales 
(id INTEGER PRIMARY KEY AUTOINCREMENT, invoice_number TEXT, product_id INTEGER, quantity INTEGER, date TEXT, FOREIGN KEY (product_id) REFERENCES products (id))''')
c.execute('''CREATE TABLE IF NOT EXISTS categories 
(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS payments 
(id INTEGER PRIMARY KEY AUTOINCREMENT, sales_id INTEGER, amount REAL, date TEXT, FOREIGN KEY (sales_id) REFERENCES sales (id))''')
c.execute('''CREATE TABLE IF NOT EXISTS customers 
(id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT, phone TEXT, segment TEXT, location TEXT, gender TEXT, contact_person TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS invoices 
(id INTEGER PRIMARY KEY, customer_id INTEGER, invoice_number TEXT UNIQUE, date TEXT, type TEXT, FOREIGN KEY (customer_id) REFERENCES customers (id))''')
c.execute('''CREATE TABLE IF NOT EXISTS invoice_items 
(id INTEGER PRIMARY KEY AUTOINCREMENT, invoice_id INTEGER, product_id INTEGER, quantity INTEGER, FOREIGN KEY (invoice_id) REFERENCES invoices (id), FOREIGN KEY (product_id) REFERENCES products (id))''')
c.execute('''CREATE TABLE IF NOT EXISTS inventory 
(id INTEGER PRIMARY KEY AUTOINCREMENT, product_id INTEGER, quantity INTEGER, FOREIGN KEY (product_id) REFERENCES products (id))''')


conn.commit()
conn.close()

# Set session timeout to 2 minutes (120 seconds)
app.config['PERMANENT_SESSION_LIFETIME'] = 120

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
        user_role = get_user_role()
        if user_role in ['admin', 'manager']:
            return render_template('base.html', username=session['username'], role=get_user_role(), is_logged_in=is_logged_in)
        else:
            # Redirect to a page indicating unauthorized access
            return render_template('unauthorized.html')
    else:
        return redirect(url_for('login'))
 # Route for listing all sales and payments
@app.route('/sales_and_payments')
def sales_and_payments():
    if is_logged_in():
        user_role = get_user_role()
        if user_role in ['admin', 'manager']:
            conn = sqlite3.connect('database.db')
            c = conn.cursor()
            c.execute("SELECT s.id, p.name, s.quantity, s.date, py.amount, py.date FROM sales s JOIN products p ON s.product_id = p.id LEFT JOIN payments py ON s.id = py.sales_id")
            sales_and_payments = c.fetchall()
            conn.close()
            return render_template('sales_and_payments.html', data=sales_and_payments, is_logged_in=is_logged_in)
        else:
            # Redirect to a page indicating unauthorized access
            return render_template('unauthorized.html')
    else:
        return redirect(url_for('login'))
# Route for importing sales from Excel file
@app.route('/import_sales', methods=['GET', 'POST'])
def import_sales():
    if is_logged_in():
        user_role = get_user_role()
        if user_role in ['admin', 'manager']:
            if request.method == 'POST':
                # Check if the post request has the file part
                if 'file' not in request.files:
                    return redirect(request.url)
                file = request.files['file']
                # If the user does not select a file, the browser submits an empty file without a filename
                if file.filename == '':
                    return redirect(request.url)
                if file:
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(file_path)
                    
                    # Parse Excel file
                    try:
                        sales_data = pd.read_excel(file_path)
                        # Insert data into the database
                        conn = sqlite3.connect('database.db')
                        c = conn.cursor()
                        for index, row in sales_data.iterrows():
                            c.execute("""
                                INSERT INTO sales (product_id, quantity, date)
                                VALUES (?, ?, ?)
                            """, (row['product_id'], row['quantity'], row['date']))
                        conn.commit()
                        conn.close()
                        return redirect(url_for('sales_and_payments'))
                    except Exception as e:
                        # Handle parsing or database insertion errors
                        os.remove(file_path)  # Delete uploaded file
                        return render_template('import_sales.html', error=str(e))
            
            return render_template('import_sales.html', is_logged_in=is_logged_in())
        else:
            # Redirect to a page indicating unauthorized access
            return render_template('unauthorized.html')
    else:
        return redirect(url_for('login'))

@app.route('/sales_by_date', methods=['GET', 'POST'])
def sales_by_date():
    if is_logged_in():
        user_role = get_user_role()
        if user_role in ['admin', 'manager']:
            if request.method == 'POST':
                start_date_str = request.form['start_date']
                end_date_str = request.form['end_date']
                
                try:
                    start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
                    end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
                    
                    conn = sqlite3.connect('database.db')
                    c = conn.cursor()
                    c.execute("""
                        SELECT * FROM sales
                        WHERE date BETWEEN ? AND ?
                    """, (start_date, end_date))
                    sales_data = c.fetchall()
                    conn.close()
                    
                    return render_template('sales_by_date.html', sales_data=sales_data)
                
                except Exception as e:
                    return render_template('error.html', error=str(e))
            
            return render_template('sales_by_date.html', is_logged_in=is_logged_in())
        else:
            return render_template('unauthorized.html')
    else:
        return redirect(url_for('login'))
 # Route for importing products from Excel file
@app.route('/import_products', methods=['GET', 'POST'])
def import_products():
    if is_logged_in():
        user_role = get_user_role()
        if user_role in ['admin', 'manager']:
            if request.method == 'POST':
                if 'file' not in request.files:
                    return redirect(request.url)
                file = request.files['file']
                if file.filename == '':
                    return redirect(request.url)
                if file:
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(file_path)
                    
                    try:
                        products_data = pd.read_excel(file_path)
                        conn = sqlite3.connect('database.db')
                        c = conn.cursor()
                        for index, row in products_data.iterrows():
                            c.execute("""
                                INSERT INTO products (name, category, barcode, description, vendor, manufacturer, price, discount, tax, image_url)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (row['name'], row['category'], row['barcode'], row['description'], row['vendor'], row['manufacturer'], row['price'], row['discount'], row['tax'], row['image_url']))
                        conn.commit()
                        conn.close()
                        flash('Products imported successfully!', 'success')
                        return redirect(url_for('products'))
                    except Exception as e:
                        os.remove(file_path)
                        return render_template('import_products.html', error=str(e))
        
            return render_template('import_products.html', is_logged_in=is_logged_in())
        else:
            # Redirect to a page indicating unauthorized access
            return render_template('unauthorized.html')
    else:
        return redirect(url_for('login'))

# Route for importing customers from Excel file
@app.route('/import_customers', methods=['GET', 'POST'])
def import_customers():
    if is_logged_in():
        user_role = get_user_role()
        if user_role in ['admin', 'manager']:
            if request.method == 'POST':
                if 'file' not in request.files:
                    return redirect(request.url)
                file = request.files['file']
                if file.filename == '':
                    return redirect(request.url)
                if file:
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(file_path)
                    
                    try:
                        customers_data = pd.read_excel(file_path)
                        conn = sqlite3.connect('database.db')
                        c = conn.cursor()
                        for index, row in customers_data.iterrows():
                            c.execute("""
                                INSERT INTO customers (name, email, phone, segment, location, gender, contact_person)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                            """, (row['name'], row['email'], row['phone'], row['segment'], row['location'], row['gender'], row['contact_person']))
                        conn.commit()
                        conn.close()
                        flash('Customers imported successfully!', 'success')
                        return redirect(url_for('customers'))
                    except Exception as e:
                        os.remove(file_path)
                        return render_template('import_customers.html', error=str(e))
            
            return render_template('import_customers.html', is_logged_in=is_logged_in())
        else:
            # Redirect to a page indicating unauthorized access
            return render_template('unauthorized.html')
    else:
        return redirect(url_for('login'))

# HTML templates for import_products.html and import_customers.html are similar to import_sales.html

# Route for listing all products
@app.route('/products')
def products():
    if is_logged_in():
        user_role = get_user_role()
        if user_role in ['admin', 'manager']:
        # Fetch all products from the database
            conn = sqlite3.connect('database.db')
            c = conn.cursor()
            c.execute("SELECT * FROM products")
            products = c.fetchall()
            conn.close()

            return render_template('products.html', products=products, is_logged_in=is_logged_in)
        else:
            # Redirect to a page indicating unauthorized a    
            return render_template('unauthorized.html') 
    else:
        return redirect(url_for('login'))

# Configuration for file uploads
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# Route for creating products
@app.route('/create_product', methods=['GET', 'POST'])
def create_product():
    if is_logged_in():
        user_role = get_user_role()
        if user_role in ['admin', 'manager']:
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
            
            return render_template('create_product.html', categories=categories, is_logged_in=is_logged_in())
        else:
            # Redirect to a page indicating unauthorized access
            return render_template('unauthorized.html') 
    else:
        return redirect(url_for('login'))
@app.route('/edit_product/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    if is_logged_in():
        user_role = get_user_role()
        if user_role in ['admin', 'manager']:
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

            return render_template('edit_product.html', product=product, is_logged_in=is_logged_in())
        else:
            # Redirect to a page indicating unauthorized access
            return render_template('unauthorized.html') 
    else:
        return redirect(url_for('login'))
        
@app.route('/delete_product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    if is_logged_in():
        user_role = get_user_role()
        if user_role in ['admin', 'manager']:
            # Delete the product from the database
            conn = sqlite3.connect('database.db')
            c = conn.cursor()
            c.execute("DELETE FROM products WHERE id=?", (product_id,))
            conn.commit()
            conn.close()

            return redirect(url_for('products'))
        else:
            # Redirect to a page indicating unauthorized access
            return render_template('unauthorized.html') 
    else:
        return redirect(url_for('login'))
# Route for listing all categories
@app.route('/categories')
def categories():
    if is_logged_in():
        user_role = get_user_role()
        if user_role in ['admin', 'manager']:
            # Fetch all categories from the database
            conn = sqlite3.connect('database.db')
            c = conn.cursor()
            c.execute("SELECT * FROM categories")
            categories = c.fetchall()  # Fetch categories, not products
            conn.close()

            return render_template('categories.html', categories=categories, is_logged_in=is_logged_in)
        else:
            # Redirect to a page indicating unauthorized access
            return render_template('unauthorized.html') 
    else:
        return redirect(url_for('login'))

# Route for creating a new category
@app.route('/create_category', methods=['GET', 'POST'])
def create_category():
    if is_logged_in():
        user_role = get_user_role()
        if user_role in ['admin', 'manager']:
            if request.method == 'POST':
                name = request.form['name']

                # Save the new category to the database
                conn = sqlite3.connect('database.db')
                c = conn.cursor()
                c.execute("INSERT INTO categories (name) VALUES (?)", (name,))
                conn.commit()
                conn.close()

                return redirect(url_for('categories'))

            return render_template('create_category.html', is_logged_in=is_logged_in)
        else:
            # Redirect to a page indicating unauthorized access
            return render_template('unauthorized.html') 
    else:
        return redirect(url_for('login'))
        
# Route for editing an existing category
@app.route('/edit_category/<int:category_id>', methods=['GET', 'POST'])
def edit_category(category_id):
    if is_logged_in():
        user_role = get_user_role()
        if user_role in ['admin', 'manager']:
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
            # Redirect to a page indicating unauthorized access
            return render_template('unauthorized.html') 
    else:
        return redirect(url_for('login'))
# Route for deleting a category
@app.route('/delete_category/<int:category_id>', methods=['POST'])
def delete_category(category_id):
    if is_logged_in():
        user_role = get_user_role()
        if user_role in ['admin', 'manager']:
            # Delete the category from the database
            conn = sqlite3.connect('database.db')
            c = conn.cursor()
            c.execute("DELETE FROM categories WHERE id=?", (category_id,))
            conn.commit()
            conn.close()

            return redirect(url_for('categories'))
        else:
            # Redirect to a page indicating unauthorized access
            return render_template('unauthorized.html') 
    else:
        return redirect(url_for('login'))
# Routes for listing all invoices and all customers
@app.route('/invoices')
def invoices():
    if is_logged_in():
        user_role = get_user_role()
        if user_role in ['admin', 'manager']:
            conn = sqlite3.connect('database.db')
            c = conn.cursor()
            c.execute("SELECT * FROM invoices")
            invoices = c.fetchall()
            conn.close()
            return render_template('invoices.html', invoices=invoices, is_logged_in=is_logged_in())
        else:
            # Redirect to a page indicating unauthorized access
            return render_template('unauthorized.html') 
    else:
        return redirect(url_for('login'))
# Route for creating sales invoices
# Route for creating invoices
@app.route('/create_invoice', methods=['GET', 'POST'])
def create_invoice():
    if is_logged_in():
        user_role = get_user_role()
        if user_role in ['admin', 'manager']:
            if request.method == 'POST':
                # Fetch data from the form
                customer_id = request.form['customer_id']
                product_ids = request.form.getlist('product_id[]')
                quantities = request.form.getlist('quantity[]')

                # Insert the invoice data into the database
                conn = sqlite3.connect('database.db')
                c = conn.cursor()
                c.execute("""
                    INSERT INTO invoices (customer_id, date)
                    VALUES (?, datetime('now'))
                """, (customer_id,))
                invoice_id = c.lastrowid

                # Insert invoice items into the database
                for i in range(len(product_ids)):
                    c.execute("""
                        INSERT INTO invoice_items (invoice_id, product_id, quantity)
                        VALUES (?, ?, ?)
                    """, (invoice_id, product_ids[i], quantities[i]))
                conn.commit()
                conn.close()

                # Redirect to the invoices page after creating the invoice
                return redirect(url_for('invoices'))
            else:
                # If GET request, render the create invoice form
                conn = sqlite3.connect('database.db')
                c = conn.cursor()
                c.execute("SELECT * FROM customers")
                customers = c.fetchall()
                c.execute("SELECT * FROM products")
                products = c.fetchall()
                conn.close()
                return render_template('create_invoice.html', customers=customers, products=products, is_logged_in=is_logged_in())
        else:
            # Redirect to a page indicating unauthorized access
            return render_template('unauthorized.html') 
    else:
        return redirect(url_for('login'))
        
@app.route('/edit_invoice/<int:invoice_id>', methods=['GET', 'POST'])
def edit_invoice(invoice_id):
    if is_logged_in():
        user_role = get_user_role()
        if user_role in ['admin', 'manager']:
            if request.method == 'POST':
                # Get form data
                updated_data = {
                    'name': request.form['name'],
                    'amount': request.form['amount'],
                    'customer_id': request.form['customer_id'],
                    'date': request.form['date'],
                    'notes': request.form['notes'],
                    # Add more fields as needed
                }

                # Update the invoice in the database using updated_data
                conn = sqlite3.connect('database.db')
                c = conn.cursor()
                c.execute("""
                     UPDATE invoices
                SET name = ?, amount = ?, customer_id = ?, date = ?, notes = ? -- Add more fields here as needed
                WHERE id = ?
                """, (updated_data['name'], updated_data['amount'], updated_data['customer_id'], updated_data['date'], updated_data['notes'], invoice_id))
                conn.commit()
                conn.close()

                # Redirect to the invoices page after editing
                return redirect(url_for('invoices'))

            else:
                # Fetch the invoice details from the database based on invoice_id
                conn = sqlite3.connect('database.db')
                c = conn.cursor()
                c.execute("SELECT * FROM invoices WHERE id = ?", (invoice_id,))
                invoice_details = c.fetchone()
                conn.close()

                # Render a template with the form to edit the invoice
                return render_template('edit_invoice.html', invoice=invoice_details)
        else:
            # Redirect to a page indicating unauthorized access
            return render_template('unauthorized.html') 
    else:
        return redirect(url_for('login'))
@app.route('/delete_invoice/<int:invoice_id>', methods=['POST'])
def delete_invoice(invoice_id):
    if is_logged_in():
        user_role = get_user_role()
        if user_role in ['admin', 'manager']:
            # Delete the invoice from the database
            conn = sqlite3.connect('database.db')
            c = conn.cursor()
            c.execute("DELETE FROM invoices WHERE id=?", (invoice_id,))
            conn.commit()
            conn.close()

            return redirect(url_for('invoices'))
        else:
            # Redirect to a page indicating unauthorized access
            return render_template('unauthorized.html') 
    else:
        return redirect(url_for('login'))
@app.route('/inventory')
def inventory():
    if is_logged_in():
        user_role = get_user_role()
        if user_role in ['admin', 'manager']:
            conn = sqlite3.connect('database.db')
            c = conn.cursor()
            c.execute("SELECT name, quantity FROM inventory JOIN products ON inventory.product_id = products.id")
            inventory = c.fetchall()
            conn.close()
            return render_template('inventory.html', inventory=inventory, is_logged_in=is_logged_in())
        else:
            return render_template('unauthorized.html') 
    else:
        return redirect(url_for('login'))
@app.route('/create_purchase_invoice', methods=['GET', 'POST'])
def create_purchase_invoice():
    if is_logged_in():
        user_role = get_user_role()
        if user_role in ['admin', 'manager']:
            if request.method == 'POST':
                vendor = request.form['vendor']
                product_ids = request.form.getlist('product_id[]')
                quantities = request.form.getlist('quantity[]')

                # Insert the purchase invoice data into the database
                conn = sqlite3.connect('database.db')
                c = conn.cursor()
                c.execute("""
                    INSERT INTO invoices (vendor, date)
                    VALUES (?, datetime('now'))
                """, (vendor,))
                invoice_id = c.lastrowid

                # Update inventory with purchased products
                for i in range(len(product_ids)):
                    product_id = product_ids[i]
                    quantity = int(quantities[i])

                    # Update inventory
                    c.execute("""
                        UPDATE inventory
                        SET quantity = quantity + ?
                        WHERE product_id = ?
                    """, (quantity, product_id))

                conn.commit()
                conn.close()

                # Redirect to the inventory page after creating the invoice
                return redirect(url_for('inventory'))
            else:
                # If GET request, render the create purchase invoice form
                conn = sqlite3.connect('database.db')
                c = conn.cursor()
                c.execute("SELECT * FROM products")
                products = c.fetchall()
                conn.close()
                return render_template('create_purchase_invoice.html', products=products, is_logged_in=is_logged_in())
        else:
            # Redirect to a page indicating unauthorized access
            return render_template('unauthorized.html') 
    else:
        return redirect(url_for('login'))

@app.route('/customers')
def customers():
    if is_logged_in():
        user_role = get_user_role()
        if user_role in ['admin', 'manager']:
            conn = sqlite3.connect('database.db')
            c = conn.cursor()
            c.execute("SELECT * FROM customers")
            customers = c.fetchall()
            conn.close()
            return render_template('customers.html', customers=customers, is_logged_in=is_logged_in())
        else:
            # Redirect to a page indicating unauthorized access
            return render_template('unauthorized.html') 
    else:
        return redirect(url_for('login'))

# Route for adding a new customer
@app.route('/add_customer', methods=['GET', 'POST'])
def add_customer():
    if is_logged_in():
        user_role = get_user_role()
        if user_role in ['admin', 'manager']:
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
            # Redirect to a page indicating unauthorized access
            return render_template('unauthorized.html') 
    else:
        return redirect(url_for('login'))
# Define your route to edit a customer
@app.route('/edit_customer/<int:id>', methods=['GET', 'POST'])
def edit_customer(id):
    if is_logged_in():
        user_role = get_user_role()
        if user_role in ['admin', 'manager']:
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
            # Redirect to a page indicating unauthorized access
            return render_template('unauthorized.html') 
    else:
        return redirect(url_for('login'))
@app.route('/delete_customer/<int:customer_id>', methods=['POST'])
def delete_customer(customer_id):
    if is_logged_in():
        user_role = get_user_role()
        if user_role in ['admin', 'manager']:
            # Delete the customer with the provided ID from the database
            conn = sqlite3.connect('database.db')
            c = conn.cursor()
            c.execute("DELETE FROM customers WHERE id=?", (customer_id,))
            conn.commit()
            conn.close()
            # Redirect to the customers page after deletion
            return redirect(url_for('customers'))
        else:
            # Redirect to a page indicating unauthorized access
            return render_template('unauthorized.html') 
    else:
        return redirect(url_for('login'))

# Route for creating payments
@app.route('/create_payment', methods=['GET', 'POST'])
def create_payment():
    if is_logged_in():
        user_role = get_user_role()
        if user_role in ['admin', 'manager']:
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
            return render_template('create_payment.html', sales=sales, is_logged_in=is_logged_in())
        else:
            # Redirect to a page indicating unauthorized access
            return render_template('unauthorized.html') 
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
from flask import send_file
import pandas as pd

@app.route('/export_excel')
def export_excel():
    # Query the database to retrieve reports data
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM reports")
    reports_data = c.fetchall()
    conn.close()

    # Convert data to DataFrame (using Pandas)
    df = pd.DataFrame(reports_data, columns=['Column1', 'Column2', ...])  # Replace Column1, Column2, ... with actual column names

    # Create Excel file from DataFrame
    excel_file_path = 'reports.xlsx'
    df.to_excel(excel_file_path, index=False)

    # Serve the Excel file for download
    return send_file(excel_file_path, as_attachment=True)
# Route to fetch online users
@app.route('/get_online_users')
def get_online_users():
    online_users = session.get('online_users', [])
    online_users_html = '<ul>'
    for user in online_users:
        online_users_html += f'<li>{user}</li>'
    online_users_html += '</ul>'
    return online_users_html
# Define the User model

@app.route('/register', methods=['GET', 'POST'])
def register():
    # Check if the user is logged in and has the admin role
    if is_logged_in() and get_user_role() == 'admin':
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
    else:
        return render_template('unauthorized.html')

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
            session['role'] = user[3]  # Assuming role is stored in the third column
            return redirect(url_for('home'))
        else:
            return render_template('login.html', error='Invalid username or password.')
    return render_template('login.html')

# Route for logging out
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))
    # Define the User model

@app.route('/user/<int:user_id>')
def get_user(user_id):
    # Assuming User is your model representing users in your database
    user = User.query.get_or_404(user_id)
    return render_template('user.html', user=user)

# Routes for user management
@app.route('/users')
def users():
    if is_logged_in() and get_user_role() == 'admin':
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users")
        users = c.fetchall()  # Corrected variable name
        conn.close()
        return render_template('users.html', users=users)  # Passing users instead of customers
    else:
        return render_template('unauthorized.html')

@app.route('/edit_user/<int:user_iid>', methods=['GET', 'POST'])
def edit_user(user_iid):
    if is_logged_in() and get_user_role() == 'admin':
        if request.method == 'POST':
            # Update user data
            username = request.form['username']
            password = request.form['password']
            user.role = request.form['role']

            # Update the users in the database
            conn = sqlite3.connect('database.db')
            c = conn.cursor()
            c.execute("UPDATE users SET name=?, password=?, role=?, WHERE id=?", (name, password, role, id))
            conn.commit()
            conn.close()
            return redirect(url_for('users'))
        else:
            return render_template('edit_user.html', user=user_iid, is_logged_in=is_logged_in())
    else:
        return render_template('unauthorized.html')

@app.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    if is_logged_in() and get_user_role() == 'admin':
        # Delete the users with the provided ID from the database
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("DELETE FROM users WHERE id=?", (user_id,))
        conn.commit()
        conn.close()
        # Redirect to the users page after deletion
        return redirect(url_for('users'))
    else:
        return render_template('unauthorized.html')
 
if __name__ == '__main__':
    app.run(debug=True)
