import pandas as pd
import numpy as np
from datetime import timedelta

from reconcile import load_data

class AdvancedReconciliation:
    def __init__(self, orders, payments):
        self.orders = orders.copy()
        self.payments = payments.copy()
        self.results = None
        
    def clean_data(self):
        """Advanced data cleaning"""
        # Handle currency conversion
        exchange_rate = 1.09  # USD to EUR (simplified)
        
        def standardize_currency(row):
            if row['currency'] == 'EUR' and row['amount'] > 0:
                return row['amount'] / exchange_rate
            return row['amount']
        
        self.payments['amount_usd'] = self.payments.apply(standardize_currency, axis=1)
        
        # Filter valid payments
        self.payments = self.payments[
            (self.payments['transaction_status'] == 'success') &
            (self.payments['amount_usd'] > 0) &
            (self.payments['payment_date'] <= pd.Timestamp.now())
        ].copy()
        
        return self
    
    def detect_duplicates(self, time_window_days=7, amount_tolerance=0.01):
        """Detect potential duplicate payments"""
        duplicates = []
        
        for order_id in self.payments['order_id'].unique():
            order_payments = self.payments[self.payments['order_id'] == order_id].copy()
            
            for i, payment1 in order_payments.iterrows():
                for j, payment2 in order_payments.iterrows():
                    if i >= j:
                        continue
                    
                    # Check if payments are within time window and similar amount
                    time_diff = abs((payment1['payment_date'] - payment2['payment_date']).days)
                    amount_diff = abs(payment1['amount_usd'] - payment2['amount_usd'])
                    
                    if time_diff <= time_window_days and amount_diff <= amount_tolerance:
                        duplicates.append({
                            'order_id': order_id,
                            'payment_id_1': payment1['payment_id'],
                            'payment_id_2': payment2['payment_id'],
                            'amount_1': payment1['amount_usd'],
                            'amount_2': payment2['amount_usd'],
                            'days_apart': time_diff
                        })
        
        return pd.DataFrame(duplicates)
    
    def calculate_payment_schedule(self):
        """Analyze payment timing and patterns"""
        payment_schedule = []
        
        for order_id in self.orders['order_id']:
            order_date = self.orders[self.orders['order_id'] == order_id]['order_date'].iloc[0]
            order_payments = self.payments[self.payments['order_id'] == order_id].copy()
            
            if len(order_payments) == 0:
                continue
                
            first_payment = order_payments['payment_date'].min()
            last_payment = order_payments['payment_date'].max()
            
            payment_schedule.append({
                'order_id': order_id,
                'days_to_first_payment': (first_payment - order_date).days,
                'days_to_last_payment': (last_payment - order_date).days,
                'num_payments': len(order_payments),
                'payment_methods': ', '.join(order_payments['payment_method'].unique())
            })
        
        return pd.DataFrame(payment_schedule)
    
    def perform_reconciliation(self):
        """Main reconciliation logic with advanced features"""
        
        # Aggregate payments
        payment_summary = self.payments.groupby('order_id').agg({
            'amount_usd': ['sum', 'count', 'std'],
            'payment_method': lambda x: ', '.join(x.unique())
        }).round(2)
        
        payment_summary.columns = ['total_paid', 'payment_count', 'payment_std', 'payment_methods']
        payment_summary = payment_summary.reset_index()
        
        # Merge with orders
        self.results = self.orders.merge(payment_summary, on='order_id', how='left')
        
        # Fill NaN values
        self.results['total_paid'] = self.results['total_paid'].fillna(0)
        self.results['payment_count'] = self.results['payment_count'].fillna(0)
        
        # Calculate metrics
        self.results['difference'] = self.results['total_amount'] - self.results['total_paid']
        self.results['payment_rate'] = self.results['total_paid'] / self.results['total_amount']
        self.results['payment_rate'] = self.results['payment_rate'].clip(0, None)
        
        # Classification
        def classify_payment(row):
            if row['total_paid'] == 0:
                return 'Missing'
            elif row['payment_rate'] >= 0.999:
                return 'Complete'
            elif row['payment_rate'] > 1:
                return 'Excess'
            elif row['payment_rate'] >= 0.5:
                return 'Partial (>50%)'
            else:
                return 'Partial (<50%)'
        
        self.results['payment_class'] = self.results.apply(classify_payment, axis=1)
        
        # Add risk flags
        self.results['high_risk'] = (
            (self.results['payment_count'] > 3) |  # Too many payments
            (self.results['payment_rate'] > 1.05) |  # Significant overpayment
            (self.results['payment_std'] > self.results['total_amount'] * 0.3)  # High variability
        )
        
        return self.results
    
    def generate_detailed_report(self):
        """Create comprehensive reconciliation report"""
        
        report = {
            'Metric': [
                'Total Orders',
                'Total Order Value (USD)',
                'Total Payments Received (USD)',
                'Total Outstanding (USD)',
                'Orders - Complete Payment',
                'Orders - Partial Payment',
                'Orders - Missing Payment',
                'Orders - Excess Payment',
                'Total Overpayment Amount (USD)',
                'Total Underpayment Amount (USD)',
                'Average Payment per Order (USD)',
                'Average Days to First Payment',
                'Orders with Multiple Payments',
                'High Risk Orders'
            ],
            'Value': [
                len(self.results),
                f"${self.results['total_amount'].sum():,.2f}",
                f"${self.results['total_paid'].sum():,.2f}",
                f"${self.results[self.results['difference'] > 0]['difference'].sum():,.2f}",
                (self.results['payment_class'] == 'Complete').sum(),
                self.results['payment_class'].str.contains('Partial').sum(),
                (self.results['payment_class'] == 'Missing').sum(),
                (self.results['payment_class'] == 'Excess').sum(),
                f"${abs(self.results[self.results['difference'] < 0]['difference'].sum()):,.2f}",
                f"${self.results[self.results['difference'] > 0]['difference'].sum():,.2f}",
                f"${self.results[self.results['total_paid'] > 0]['total_paid'].mean():,.2f}",
                "Calculated in schedule",
                (self.results['payment_count'] > 1).sum(),
                self.results['high_risk'].sum()
            ]
        }
        
        return pd.DataFrame(report)
    
    def export_results(self):
        """Export all reconciliation outputs"""
        
        # Main results
        self.results.to_csv('../data/processed/reconciliation_advanced.csv', index=False)
        
        # Summary report
        report = self.generate_detailed_report()
        report.to_csv('../outputs/reports/advanced_summary.csv', index=False)
        
        # Duplicate detection
        duplicates = self.detect_duplicates()
        if len(duplicates) > 0:
            duplicates.to_csv('../outputs/reports/duplicate_payments.csv', index=False)
        
        # Payment schedule
        schedule = self.calculate_payment_schedule()
        schedule.to_csv('../outputs/reports/payment_schedule.csv', index=False)
        
        print("\nAdvanced reconciliation complete!")
        print(f"Results saved to:")
        print(f"   - data/processed/reconciliation_advanced.csv")
        print(f"   - outputs/reports/advanced_summary.csv")
        print(f"   - outputs/reports/duplicate_payments.csv ({len(duplicates)} duplicates found)")
        print(f"   - outputs/reports/payment_schedule.csv")

# Run advanced reconciliation
orders, payments = load_data()
reconciler = AdvancedReconciliation(orders, payments)
reconciler.clean_data()
results = reconciler.perform_reconciliation()
reconciler.export_results()

print("\n" + "="*60)
print("SAMPLE RECONCILIATION RESULTS")
print("="*60)
print(results[['order_id', 'total_amount', 'total_paid', 'payment_rate', 'payment_class', 'high_risk']].head(10))