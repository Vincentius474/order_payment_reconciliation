import pandas as pd
import numpy as np

def load_data():
    """Load the generated data"""
    orders = pd.read_csv('../data/raw/orders.csv', parse_dates=['order_date'])
    payments = pd.read_csv('../data/raw/payments.csv', parse_dates=['payment_date'])
    return orders, payments

def basic_reconciliation(orders, payments):
    """Perform basic order-payment reconciliation"""
    
    # Clean payments: remove failed transactions and handle nulls
    payments_clean = payments[
        (payments['transaction_status'] == 'success') & 
        (payments['amount'] > 0) &
        (payments['amount'].notna())
    ].copy()
    
    # Aggregate payments by order
    payment_summary = payments_clean.groupby('order_id').agg({
        'amount': 'sum',
        'payment_id': 'count',
        'payment_method': lambda x: ', '.join(x.unique())
    }).rename(columns={'amount': 'total_paid', 'payment_id': 'payment_count'})
    
    # Merge with orders
    reconciliation = orders.merge(payment_summary, on='order_id', how='left')
    
    # Fill NaN values for orders with no payments
    reconciliation['total_paid'] = reconciliation['total_paid'].fillna(0)
    reconciliation['payment_count'] = reconciliation['payment_count'].fillna(0)
    
    # Calculate differences
    reconciliation['difference'] = reconciliation['total_amount'] - reconciliation['total_paid']
    reconciliation['abs_difference'] = abs(reconciliation['difference'])
    
    # Determine status
    def get_status(row):
        if row['total_paid'] == 0:
            return 'No Payment'
        elif abs(row['difference']) < 0.01:  # Account for floating point
            return 'Fully Paid'
        elif row['difference'] > 0:
            return 'Underpaid'
        else:
            return 'Overpaid'
    
    reconciliation['status'] = reconciliation.apply(get_status, axis=1)
    
    return reconciliation

def generate_report(reconciliation):
    """Create summary report"""
    
    report = {
        'total_orders': len(reconciliation),
        'total_order_value': reconciliation['total_amount'].sum(),
        'total_paid': reconciliation['total_paid'].sum(),
        'total_difference': reconciliation['difference'].sum(),
        'orders_fully_paid': (reconciliation['status'] == 'Fully Paid').sum(),
        'orders_underpaid': (reconciliation['status'] == 'Underpaid').sum(),
        'orders_overpaid': (reconciliation['status'] == 'Overpaid').sum(),
        'orders_no_payment': (reconciliation['status'] == 'No Payment').sum(),
        'total_underpayment_amount': reconciliation[reconciliation['difference'] > 0]['difference'].sum(),
        'total_overpayment_amount': abs(reconciliation[reconciliation['difference'] < 0]['difference'].sum())
    }
    
    return pd.DataFrame([report])

# Run reconciliation
orders, payments = load_data()
reconciliation = basic_reconciliation(orders, payments)
summary = generate_report(reconciliation)

print("="*60)
print("BASIC RECONCILIATION REPORT")
print("="*60)
print(summary.to_string(index=False))

print("\nSample of Reconciled Orders:")
print(reconciliation[['order_id', 'total_amount', 'total_paid', 'difference', 'status']].head(10))

# Save results
try:
    reconciliation.to_csv('../data/processed/reconciliation_basic.csv', index=False)
    summary.to_csv('../outputs/reports/basic_summary.csv', index=False)
except Exception as e:
    print(e)