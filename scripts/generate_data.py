import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from faker import Faker
import random

fake = Faker()
np.random.seed(42)
random.seed(42)

def generate_orders(num_orders=500):
    """Generate realistic order data"""
    
    order_statuses = ['pending', 'completed', 'shipped', 'cancelled', 'refunded']
    status_weights = [0.15, 0.60, 0.15, 0.05, 0.05]
    
    customers = [fake.uuid4() for _ in range(num_orders // 3)]  # Some repeat customers
    
    orders = []
    for i in range(1, num_orders + 1):
        order_date = fake.date_time_between(start_date='-90d', end_date='now')
        customer_id = random.choice(customers)
        
        # Generate realistic order items
        num_items = random.randint(1, 5)
        prices = [round(random.uniform(10,1000), 2) for i in range(1, num_items+1)]
        subtotal = sum(prices)
        tax = round(subtotal * 0.15, 2)  # 15% tax
        shipping = round(random.uniform(0, 25), 2)
        total_amount = round(subtotal + tax + shipping, 2)
        
        # Currency: 80% USD, 20% EUR
        currency = random.choices(['USD', 'EUR'], weights=[0.8, 0.2])[0]
        
        orders.append({
            'order_id': f'ORD-{i:05d}',
            'customer_id': customer_id,
            'order_date': order_date,
            'num_items': num_items,
            'subtotal': subtotal,
            'tax': tax,
            'shipping': shipping,
            'total_amount': total_amount,
            'currency': currency,
            'status': random.choices(order_statuses, weights=status_weights)[0]
        })
    
    return pd.DataFrame(orders)

def generate_payments(orders_df):
    """Generate payment records with intentional discrepancies"""
    
    payment_methods = ['credit_card', 'paypal', 'bank_transfer', 'crypto']
    method_weights = [0.6, 0.25, 0.10, 0.05]
    
    payments = []
    
    for _, order in orders_df.iterrows():
        order_id = order['order_id']
        order_total = order['total_amount']
        order_currency = order['currency']
        order_status = order['status']
        
        # Skip payments for cancelled orders (except if they were mistakenly paid)
        if order_status == 'cancelled' and random.random() > 0.2:
            continue
            
        # Determine payment scenario based on order status
        scenario = 'normal'
        if order_status == 'refunded':
            scenario = 'refund'
        elif order_status == 'pending' and random.random() < 0.3:
            scenario = 'partial'
        elif random.random() < 0.05:  # 5% overpayment
            scenario = 'overpayment'
        elif random.random() < 0.08:  # 8% duplicate payment
            scenario = 'duplicate'
        elif random.random() < 0.03:  # 3% missing payment
            scenario = 'missing'
        
        if scenario == 'missing':
            continue
            
        # Calculate payment amount
        if scenario == 'partial':
            amount = round(order_total * random.uniform(0.3, 0.95), 2)
        elif scenario == 'overpayment':
            amount = round(order_total * random.uniform(1.01, 1.2), 2)
        elif scenario == 'refund':
            amount = -round(order_total * random.uniform(0.5, 1.0), 2)  # Negative for refund
        else:  # normal
            amount = order_total
        
        # Payment date (can be before, on, or after order date)
        order_date = order['order_date']
        days_delay = random.gauss(2, 3)  # Mean 2 days delay
        payment_date = order_date + timedelta(days=max(-1, days_delay))
        
        # Handle currency conversion for some payments
        payment_currency = order_currency
        if random.random() < 0.1:  # 10% of payments in different currency
            payment_currency = 'EUR' if order_currency == 'USD' else 'USD'
            # Add approximate conversion (simplified)
            if payment_currency == 'EUR':
                amount = round(amount * 0.92, 2)
            else:
                amount = round(amount * 1.09, 2)
        
        # Create 1-3 payment records for the same order (installments)
        num_payments = 1
        if scenario == 'normal' and random.random() < 0.15:  # 15% split payments
            num_payments = random.randint(2, 3)
            amounts = [round(amount / num_payments, 2)] * (num_payments - 1)
            amounts.append(round(amount - sum(amounts), 2))
        else:
            amounts = [amount]
        
        for i, payment_amount in enumerate(amounts):
            payment = {
                'payment_id': fake.uuid4(),
                'order_id': order_id,
                'payment_date': payment_date + timedelta(days=i*random.randint(1,3)),
                'amount': payment_amount,
                'currency': payment_currency,
                'payment_method': random.choices(payment_methods, weights=method_weights)[0],
                'transaction_status': random.choices(['success', 'pending', 'failed'], 
                                                    weights=[0.9, 0.07, 0.03])[0]
            }
            payments.append(payment)
        
        # Add duplicate payment for some orders
        if scenario == 'duplicate':
            duplicate = {
                'payment_id': fake.uuid4(),
                'order_id': order_id,
                'payment_date': payment_date + timedelta(days=random.randint(1, 5)),
                'amount': round(order_total * random.uniform(0.5, 1.0), 2),
                'currency': order_currency,
                'payment_method': random.choice(payment_methods),
                'transaction_status': 'success'
            }
            payments.append(duplicate)
    
    return pd.DataFrame(payments)

def add_data_quality_issues(df):
    """Add intentional data quality issues for reconciliation challenges"""
    
    df_issues = df.copy()
    
    # Add some null values
    null_indices = np.random.choice(df_issues.index, size=min(10, len(df_issues)), replace=False)
    df_issues.loc[null_indices, 'amount'] = np.nan
    
    # Add some negative amounts (errors)
    neg_indices = np.random.choice(df_issues.index, size=min(5, len(df_issues)), replace=False)
    df_issues.loc[neg_indices, 'amount'] = -abs(df_issues.loc[neg_indices, 'amount'])
    
    # Add future dates
    future_indices = np.random.choice(df_issues.index, size=min(3, len(df_issues)), replace=False)
    df_issues.loc[future_indices, 'payment_date'] = datetime.now() + timedelta(days=random.randint(1, 30))
    
    return df_issues

# Generate and save the data
# For orders
try:
    print("Generating orders...")
    orders = generate_orders(500)
    print(f"Generated {len(orders)} orders")

    # Save to csv file
    orders.to_csv('../data/raw/orders.csv', index=False)
    print(f"Orders File saved to: - data/raw/orders.csv ({len(orders)} records)")

    # Display sample
    print("\nSample Orders:")
    print(orders.head())

except Exception as e:
    print(e)

# For payments
try:
    print("\nGenerating payments...")
    payments = generate_payments(orders)
    print(f"Generated {len(payments)} payment records")

    print("\nAdding data quality issues...")
    payments = add_data_quality_issues(payments)

    # Save to csv file
    payments.to_csv('../data/raw/payments.csv', index=False)
    print(f"Payments File saved to: - data/raw/orders.csv ({len(orders)} records)")

    # Display sample
    print("\nSample Payments:")
    print(payments.head())

except Exception as e:
    print(e)
