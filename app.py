from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import login_user, login_required, logout_user, current_user
import os
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

from extensions import db, login_manager
from models import User, Service, ServiceType, SERVICE_PRICES, PaymentMethod, InvoiceType, Frequency
from reports import generate_monthly_report

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///temple.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Convert ServiceType enum to a dict for template use
    service_types_dict = {
        service_type.value: {
            'name': service_type.name,
            'value': service_type.value
        }
        for service_type in ServiceType
    }
    
    return render_template('dashboard.html', 
                         service_types=service_types_dict, 
                         service_prices=SERVICE_PRICES)

@app.route('/temple-management/services', methods=['POST'])
@login_required
def create_service():
    try:
        service_type = int(request.args.get('serviceType'))
        data = request.get_json()
        
        # Create service
        service = Service(
            service_type=service_type,
            invoice_type=data.get('invoiceType'),
            frequency=data.get('frequency', 'SINGLE'),
            payment_method=data.get('paymentMethod'),
            devotee_name=data.get('devoteeName'),
            contact_number=data.get('devoteeContactNum'),
            gothram=data.get('gothram'),
            puja_details=data.get('pujaDetails'),
            service_name=ServiceType(service_type).name,
            invoice_number=Service.generate_invoice_number(data.get('invoiceType')),
            valid_till=Service.calculate_valid_till(data.get('frequency', 'SINGLE')),
            amount=Service.calculate_amount(service_type, data.get('frequency', 'SINGLE'))
        )
        
        # Set address fields if provided
        if data.get('address'):
            addr = data['address']
            service.address1 = addr.get('address1')
            service.address2 = addr.get('address2')
            service.address3 = addr.get('address3')
            service.address4 = addr.get('address4')
            service.city = addr.get('city')
            service.district = addr.get('district')
            service.state = addr.get('state')
            service.pincode = addr.get('pincode')
        
        db.session.add(service)
        db.session.commit()
        
        # Prepare response with print data
        response_data = {
            'message': 'Service created successfully',
            'id': service.invoice_number,
            'amount': service.amount,
            'validTill': service.valid_till.isoformat(),
            'serviceName': ServiceType(service_type).name.replace('_', ' ').title(),
            'devoteeName': data.get('devoteeName'),
            'gothram': data.get('gothram'),
            'pujaDetails': data.get('pujaDetails'),
            'address': {
                'address1': service.address1,
                'address2': service.address2,
                'address3': service.address3,
                'address4': service.address4,
                'city': service.city,
                'district': service.district,
                'state': service.state,
                'pincode': service.pincode
            } if service.address1 else None
        }
        
        return jsonify(response_data), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 400

@app.route('/reports/monthly', methods=['GET'])
@login_required
def monthly_report():
    """Generate and download a monthly report"""
    # Get year and month from query parameters, default to current month
    year = request.args.get('year', datetime.now().year, type=int)
    month = request.args.get('month', datetime.now().month, type=int)
    
    try:
        # Generate the report
        report_file = generate_monthly_report(year, month)
        
        # Get the filename from the path
        filename = os.path.basename(report_file)
        
        # Send the file as an attachment
        return send_file(report_file, as_attachment=True, download_name=filename)
    except Exception as e:
        flash(f'Error generating report: {str(e)}', 'danger')
        return redirect(url_for('dashboard'))

def init_db():
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Create admin user if not exists
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', role='admin')
            admin.set_password('admin123')
            db.session.add(admin)
            
            # Create clerk user if not exists
            if not User.query.filter_by(username='clerk').first():
                clerk = User(username='clerk', role='clerk')
                clerk.set_password('clerk123')
                db.session.add(clerk)
            
            db.session.commit()

if __name__ == '__main__':
    init_db()  # Initialize database and create tables
    app.run(host='0.0.0.0', port=5000, debug=True)
