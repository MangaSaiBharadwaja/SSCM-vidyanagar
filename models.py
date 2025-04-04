from datetime import datetime, timedelta
from enum import Enum
from extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class ServiceType(Enum):
    ABHISHEKAM = 1
    ASHTOTHRAM = 2
    VISHNUSAHASRANAMAM = 3
    VISHNUSAHASRANAMAM_WITH_POST = 4
    PALLAKISEVA = 5
    SAI_SATHYA_VRATHAM = 6
    ANNADANAM = 7
    RUDRABHISHEKAM = 8
    SAMUHIKA_RUDRABHISHEKAM = 9
    SASWATHA_VISHNUSAHASRANAMA_PUJA = 10
    SASWATHA_DUNI_PUJA = 11
    SASWATHA_AKANDA_DEEPA_SEVA = 12
    SASWATHA_VISHNUSAHASRANAMA_PUJA_ALLFESTIVALS = 13
    SASWATHA_ANNADANAM = 14
    SASWATHA_ANNADANAM_ALLFESTIVALS = 15
    SARVASEVA = 16
    ANNADANAM_YEARLYONCE = 17
    DHUNIPUJA_WITH_PUJA_MATERIAL = 18
    DHUNIPUJA_WITHOUT_PUJA_MATERIAL = 19

class InvoiceType(Enum):
    TOKEN = "TOKEN"
    RECEIPT = "RECEIPT"

class PaymentMethod(Enum):
    UPI = "UPI"
    CASH = "CASH"
    CARD = "CARD"

class Frequency(Enum):
    SINGLE = "SINGLE"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"

SERVICE_PRICES = {
    1: 16,     # ABHISHEKAM
    2: 11,     # ASHTOTHRAM
    3: 50,     # VISHNUSAHASRANAMAM
    4: 60,     # VISHNUSAHASRANAMAM_WITH_POST
    5: 200,    # PALLAKISEVA
    6: 150,    # SAI_SATHYA_VRATHAM
    7: 1116,   # ANNADANAM
    8: 2000,   # RUDRABHISHEKAM
    9: 250,    # SAMUHIKA_RUDRABHISHEKAM
    10: 1116,  # SASWATHA_VISHNUSAHASRANAMA_PUJA
    11: 1516,  # SASWATHA_DUNI_PUJA
    12: 1516,  # SASWATHA_AKANDA_DEEPA_SEVA
    13: 5116,  # SASWATHA_VISHNUSAHASRANAMA_PUJA_ALLFESTIVALS
    14: 2116,  # SASWATHA_ANNADANAM
    15: 10116, # SASWATHA_ANNADANAM_ALLFESTIVALS
    16: 5116,  # SARVASEVA
    17: 3516,  # ANNADANAM_YEARLYONCE
    18: 100,   # DHUNIPUJA_WITH_PUJA_MATERIAL
    19: 35     # DHUNIPUJA_WITHOUT_PUJA_MATERIAL
}

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'admin' or 'clerk'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service_type = db.Column(db.Integer, nullable=False)
    service_name = db.Column(db.String(100), nullable=False)
    invoice_type = db.Column(db.String(10), nullable=False)
    invoice_number = db.Column(db.String(10), unique=True, nullable=False)
    frequency = db.Column(db.String(10), nullable=False, default="SINGLE")
    valid_till = db.Column(db.DateTime, nullable=False)
    
    # Devotee Details
    devotee_name = db.Column(db.String(100))
    contact_number = db.Column(db.String(15))
    gothram = db.Column(db.String(50))
    puja_details = db.Column(db.Text)
    
    # Address Details
    address1 = db.Column(db.String(100))
    address2 = db.Column(db.String(100))
    address3 = db.Column(db.String(100))
    address4 = db.Column(db.String(100))
    city = db.Column(db.String(50))
    district = db.Column(db.String(50))
    state = db.Column(db.String(50))
    pincode = db.Column(db.String(10))
    
    # Payment Details
    payment_method = db.Column(db.String(10), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    @staticmethod
    def generate_invoice_number(invoice_type):
        """Generate a unique invoice number based on type (TOKEN/RECEIPT)"""
        prefix = "T" if invoice_type == "TOKEN" else "R"
        last_service = Service.query.filter(
            Service.invoice_number.like(f"{prefix}%")
        ).order_by(Service.invoice_number.desc()).first()
        
        if not last_service:
            return f"{prefix}A0001"
            
        last_num = int(last_service.invoice_number[2:])
        new_num = last_num + 1
        
        if new_num > 9999:
            # Increment the letter
            letter = chr(ord(last_service.invoice_number[1]) + 1)
            if letter > 'Z':
                raise ValueError("Invoice number limit reached")
            return f"{prefix}{letter}0001"
            
        return f"{prefix}{last_service.invoice_number[1]}{new_num:04d}"

    @staticmethod
    def calculate_amount(service_type, frequency="SINGLE"):
        """Calculate service amount based on type and frequency"""
        base_amount = SERVICE_PRICES.get(service_type)
        if not base_amount:
            raise ValueError("Invalid service type")
            
        if frequency == "WEEKLY":
            return base_amount * 7
        elif frequency == "MONTHLY":
            return base_amount * 30
        return base_amount

    @staticmethod
    def calculate_valid_till(frequency="SINGLE"):
        """Calculate validity period based on frequency"""
        now = datetime.utcnow()
        if frequency == "WEEKLY":
            return now + timedelta(days=7)
        elif frequency == "MONTHLY":
            return now + timedelta(days=30)
        return now + timedelta(days=1)  # Single day validity for SINGLE frequency
