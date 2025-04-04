import os
import pandas as pd
import sqlite3
from datetime import datetime
from enum import Enum
from models import ServiceType, PaymentMethod

def generate_monthly_report(year=None, month=None):
    """
    Generate a monthly Excel report with service-wise and payment-wise data in separate tabs.
    
    Args:
        year (int): Year for the report (defaults to current year if None)
        month (int): Month for the report (defaults to current month if None)
        
    Returns:
        str: Path to the generated Excel file
    """
    # Use current year and month if not specified
    if year is None:
        year = datetime.now().year
    if month is None:
        month = datetime.now().month
    
    # Create reports directory if it doesn't exist
    reports_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reports')
    os.makedirs(reports_dir, exist_ok=True)
    
    # Connect to the database
    conn = sqlite3.connect('temple.db')
    
    # Create a month name for the file
    month_name = datetime.strptime(f"{year}-{month}", "%Y-%m").strftime("%B_%Y")
    excel_file = os.path.join(reports_dir, f"Temple_Report_{month_name}.xlsx")
    
    # Create Excel writer
    with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
        # Create a summary sheet
        create_summary_sheet(conn, writer, year, month)
        
        # Create service-wise sheets
        create_service_sheets(conn, writer, year, month)
        
        # Create payment-wise sheets
        create_payment_sheets(conn, writer, year, month)
    
    conn.close()
    return excel_file

def create_summary_sheet(conn, writer, year, month):
    """Create a summary sheet with overall statistics"""
    # Query for summary data
    query = """
    SELECT 
        COUNT(*) as total_services,
        SUM(amount) as total_amount,
        COUNT(DISTINCT devotee_name) as unique_devotees
    FROM service
    WHERE strftime('%Y', created_at) = ? AND strftime('%m', created_at) = ?
    """
    
    summary_df = pd.read_sql_query(query, conn, params=(str(year), str(month).zfill(2)))
    
    # Add service type breakdown
    service_type_query = """
    SELECT 
        service_type,
        COUNT(*) as count,
        SUM(amount) as total_amount
    FROM service
    WHERE strftime('%Y', created_at) = ? AND strftime('%m', created_at) = ?
    GROUP BY service_type
    ORDER BY total_amount DESC
    """
    
    service_breakdown = pd.read_sql_query(service_type_query, conn, params=(str(year), str(month).zfill(2)))
    
    # Map service_type numbers to names
    service_breakdown['service_name'] = service_breakdown['service_type'].apply(
        lambda x: ServiceType(x).name.replace('_', ' ').title()
    )
    
    # Payment method breakdown
    payment_query = """
    SELECT 
        payment_method,
        COUNT(*) as count,
        SUM(amount) as total_amount
    FROM service
    WHERE strftime('%Y', created_at) = ? AND strftime('%m', created_at) = ?
    GROUP BY payment_method
    ORDER BY total_amount DESC
    """
    
    payment_breakdown = pd.read_sql_query(payment_query, conn, params=(str(year), str(month).zfill(2)))
    
    # Map payment method numbers to names
    payment_breakdown['payment_name'] = payment_breakdown['payment_method'].apply(
        lambda x: PaymentMethod(x).name.title()
    )
    
    # Write to Excel
    summary_df.to_excel(writer, sheet_name='Summary', index=False, startrow=1)
    service_breakdown[['service_name', 'count', 'total_amount']].to_excel(
        writer, sheet_name='Summary', index=False, startrow=5
    )
    payment_breakdown[['payment_name', 'count', 'total_amount']].to_excel(
        writer, sheet_name='Summary', index=False, startrow=len(service_breakdown) + 8
    )
    
    # Get the worksheet
    worksheet = writer.sheets['Summary']
    worksheet.cell(row=1, column=1).value = f"Monthly Report: {datetime.strptime(str(month), '%m').strftime('%B')} {year}"
    worksheet.cell(row=5, column=1).value = "Service Type Breakdown:"
    worksheet.cell(row=len(service_breakdown) + 8, column=1).value = "Payment Method Breakdown:"

def create_service_sheets(conn, writer, year, month):
    """Create separate sheets for each service type"""
    # Get all services for the month
    query = """
    SELECT *
    FROM service
    WHERE strftime('%Y', created_at) = ? AND strftime('%m', created_at) = ?
    """
    
    all_services = pd.read_sql_query(query, conn, params=(str(year), str(month).zfill(2)))
    
    if all_services.empty:
        # No data for this month
        return
    
    # Get unique service types
    service_types = all_services['service_type'].unique()
    
    for service_type in service_types:
        # Filter data for this service type
        service_data = all_services[all_services['service_type'] == service_type].copy()
        
        # Get service name
        service_name = ServiceType(service_type).name.replace('_', ' ').title()
        
        # Format the data for display
        service_data['created_at'] = pd.to_datetime(service_data['created_at'])
        service_data['valid_till'] = pd.to_datetime(service_data['valid_till'])
        service_data['payment_method'] = service_data['payment_method'].apply(
            lambda x: PaymentMethod(x).name.title()
        )
        
        # Select and rename columns for better readability
        display_columns = {
            'invoice_number': 'Invoice Number',
            'created_at': 'Date',
            'devotee_name': 'Devotee Name',
            'gothram': 'Gothram',
            'contact_number': 'Contact',
            'amount': 'Amount',
            'payment_method': 'Payment Method',
            'puja_details': 'Puja Details'
        }
        
        # Create the sheet
        sheet_name = f"{service_name[:28]}"  # Excel has a 31 character limit for sheet names
        service_data[list(display_columns.keys())].rename(columns=display_columns).to_excel(
            writer, sheet_name=sheet_name, index=False
        )
        
        # Format the sheet
        worksheet = writer.sheets[sheet_name]
        worksheet.column_dimensions['A'].width = 15  # Invoice number
        worksheet.column_dimensions['B'].width = 20  # Date
        worksheet.column_dimensions['C'].width = 25  # Devotee name
        worksheet.column_dimensions['H'].width = 30  # Puja details

def create_payment_sheets(conn, writer, year, month):
    """Create separate sheets for each payment method"""
    # Get all services for the month
    query = """
    SELECT *
    FROM service
    WHERE strftime('%Y', created_at) = ? AND strftime('%m', created_at) = ?
    """
    
    all_services = pd.read_sql_query(query, conn, params=(str(year), str(month).zfill(2)))
    
    if all_services.empty:
        # No data for this month
        return
    
    # Get unique payment methods
    payment_methods = all_services['payment_method'].unique()
    
    for payment_method in payment_methods:
        # Filter data for this payment method
        payment_data = all_services[all_services['payment_method'] == payment_method].copy()
        
        # Get payment method name
        payment_name = PaymentMethod(payment_method).name.title()
        
        # Format the data for display
        payment_data['created_at'] = pd.to_datetime(payment_data['created_at'])
        payment_data['service_type'] = payment_data['service_type'].apply(
            lambda x: ServiceType(x).name.replace('_', ' ').title()
        )
        
        # Select and rename columns for better readability
        display_columns = {
            'invoice_number': 'Invoice Number',
            'created_at': 'Date',
            'service_type': 'Service Type',
            'devotee_name': 'Devotee Name',
            'amount': 'Amount',
            'puja_details': 'Puja Details'
        }
        
        # Create the sheet
        sheet_name = f"Payment_{payment_name[:20]}"  # Excel has a 31 character limit for sheet names
        payment_data[list(display_columns.keys())].rename(columns=display_columns).to_excel(
            writer, sheet_name=sheet_name, index=False
        )
        
        # Format the sheet
        worksheet = writer.sheets[sheet_name]
        worksheet.column_dimensions['A'].width = 15  # Invoice number
        worksheet.column_dimensions['B'].width = 20  # Date
        worksheet.column_dimensions['C'].width = 25  # Service type
        worksheet.column_dimensions['D'].width = 25  # Devotee name
        worksheet.column_dimensions['F'].width = 30  # Puja details

if __name__ == "__main__":
    # Generate report for current month
    report_file = generate_monthly_report()
    print(f"Report generated: {report_file}")
