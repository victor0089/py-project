from flask import Blueprint, render_template, request, redirect, url_for, session
from models import db
from models.sale import Sale
from models.payment import Payment

sales_bp = Blueprint('sales', __name__)

@sales_bp.route('/create_invoice', methods=['GET', 'POST'])
def create_invoice():
    if request.method == 'POST':
        # Extract form data
        product_id = request.form['product_id']
        quantity = request.form['quantity']
        
        # Create a new Sale object
        sale = Sale(product_id=product_id, quantity=quantity)
        
        # Add the Sale object to the database session
        db.session.add(sale)
        
        # Commit the transaction to the database
        db.session.commit()
        
        # Redirect to the home page or a success page
        return redirect(url_for('home'))
    
    # Render the form template for creating invoices
    return render_template('create_invoice.html')

@sales_bp.route('/create_payment', methods=['GET', 'POST'])
def create_payment():
    if request.method == 'POST':
        # Extract form data
        sale_id = request.form['sale_id']
        amount = request.form['amount']
        
        # Create a new Payment object
        payment = Payment(sale_id=sale_id, amount=amount)
        
        # Add the Payment object to the database session
        db.session.add(payment)
        
        # Commit the transaction to the database
        db.session.commit()
        
        # Redirect to the home page or a success page
        return redirect(url_for('home'))
    
    # Render the form template for creating payments
    return render_template('create_payment.html')

@sales_bp.route('/sales_and_payments')
def sales_and_payments():
    # Retrieve sales and payments data from the database
    sales = Sale.query.all()
    payments = Payment.query.all()
    
    # Render a template to display sales and payments
    return render_template('sales_and_payments.html', sales=sales, payments=payments)
