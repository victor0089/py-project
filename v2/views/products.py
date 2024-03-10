from flask import Blueprint, render_template, request, redirect, url_for, session
from models import db
from models.product import Product

products_bp = Blueprint('products', __name__)

@products_bp.route('/create_product', methods=['GET', 'POST'])
def create_product():
    if request.method == 'POST':
        # Extract data from the form
        name = request.form['name']
        price = request.form['price']
        
        # Create a new Product object
        product = Product(name=name, price=price)
        
        # Add the Product object to the database session
        db.session.add(product)
        
        # Commit the transaction to the database
        db.session.commit()
        
        # Redirect to the home page or a success page
        return redirect(url_for('home'))
    
    # Render the form template for creating products
    return render_template('create_product.html')

# Add more routes for managing products as needed
