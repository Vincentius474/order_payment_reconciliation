# Order-Payment Reconciliation System

A data reconciliation system for e-commerce order and payment validation. The project matches orders from an Order Management System (OMS) against payments from a payment gateway, and handles partial payments, overpayments, duplicates, currency conversion, and data quality issues.

<img width="1489" height="1025" alt="screenshotB" src="https://github.com/user-attachments/assets/1f190788-9f40-42b1-869f-322a6654c252" />


## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Data Generation](#data-generation)
- [Reconciliation Logic](#reconciliation-logic)
- [Visualization](#visualization)
- [Output Examples](#output-examples)
- [Contributing](#contributing)
- [License](#license)

## Overview

This project simulates a real-world reconciliation workflow. Synthetic orders and payments are generated with deliberate discrepancies, then reconciled to surface anything that does not add up.

**Who it helps**

| Team | Use |
| --- | --- |
| Finance | Reconcile daily transactions |
| Auditors | Verify payment completeness |
| Operations | Identify payment anomalies |
| Customer Support | Resolve payment disputes |

## Features

**Core capabilities**

- **Synthetic data generation:** realistic orders and payments with intentional discrepancies
- **Basic reconciliation:** matches orders to payments and flags mismatches
- **Advanced reconciliation:** currency conversion, duplicate detection, and partial-payment handling
- **Risk detection:** flags high-risk transactions and anomalies
- **Dashboard:** visual summary of payment patterns
- **CSV reports:** exportable results for further analysis

**Scenarios handled**

- Partial payments and installments
- Multi-currency transactions (USD/EUR)
- Payment timing analysis
- Duplicate payment detection
- Payment method analytics
- Data quality issues (nulls, negative amounts, future dates)

## Project Structure

```
order_payment_reconciliation/
├── data/
│   ├── raw/                          # Generated raw data
│   │   ├── orders.csv
│   │   └── payments.csv
│   └── processed/                    # Reconciliation results
│       ├── reconciliation_basic.csv
│       └── reconciliation_advanced.csv
├── notebooks/                        # Exploration notebooks
│   ├── 01_data_generation.ipynb
│   ├── 02_reconciliation.ipynb
│   ├── 03_advanced_reconciliation.ipynb
│   └── 04_visualization.ipynb
├── scripts/
│   ├── generate_data.py              # Data generation
│   ├── reconcile_basic.py            # Basic reconciliation
│   ├── reconcile_advanced.py         # Advanced reconciliation
│   └── visualize_results.py          # Dashboard creation
├── outputs/
│   ├── reports/                      # CSV reports
│   │   ├── basic_summary.csv
│   │   ├── advanced_summary.csv
│   │   ├── duplicate_payments.csv
│   │   └── payment_schedule.csv
│   └── visualizations/
│       └── reconciliation_dashboard.png
├── requirements.txt
├── README.md
└── .gitignore
```

## Installation

### Prerequisites

- Python 3.8 or higher
- pip
- (Optional) a virtual environment tool

### 1. Clone the repository

```bash
git clone https://github.com/vincentius474/order-payment-reconciliation.git
cd order-payment-reconciliation
```

### 2. Create a virtual environment

**Windows**

```bash
python -m venv venv
venv\Scripts\activate
```

**macOS / Linux**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

If you run into installation issues, install the packages one at a time:

```bash
pip install numpy==1.24.3
pip install pandas==2.1.0
pip install matplotlib==3.7.2
pip install seaborn==0.13.0
pip install openpyxl==3.1.2
pip install Faker==20.0.0
```

### 4. Verify the installation

```bash
python -c "import pandas; print(f'Pandas version: {pandas.__version__}')"
```

## Quick Start

Run the full pipeline:

```bash
# 1. Create the output directories
mkdir -p data/raw data/processed outputs/reports outputs/visualizations

# 2. Generate synthetic data
python scripts/generate_data.py

# 3. Run basic reconciliation
python scripts/reconcile_basic.py

# 4. Run advanced reconciliation
python scripts/reconcile_advanced.py

# 5. Create the dashboard
python scripts/visualize_results.py
```

**Expected output**

- Reconciliation statistics printed to the console
- CSV files in `data/processed/` and `outputs/reports/`
- A dashboard image in `outputs/visualizations/`

## Data Generation

`generate_data.py` creates two datasets.

### Orders (500 records)

- Sequential order IDs
- Customer IDs in UUID format
- Order dates spanning 90 days
- Multiple line items with tax and shipping
- Status tracking: pending, completed, shipped, cancelled, refunded
- Dual currency support (USD/EUR)

### Payments (record count varies)

- Payment methods: credit card, PayPal, bank transfer, crypto
- Transaction statuses: success, pending, failed
- Intentional discrepancies across orders:

  | Scenario | Share of orders |
  | --- | --- |
  | Full payments | 80% |
  | Partial payments | 10% |
  | Overpayments | 5% |
  | Missing payments | 5% |

- Duplicate payments on 8% of orders
- Currency conversion edge cases
- Data quality issues: nulls, negative amounts, and future dates

## Reconciliation Logic

### Basic reconciliation

1. Match orders to payments
2. Calculate the total paid per order
3. Classify each order as one of:
   - **Fully Paid**
   - **Underpaid**
   - **Overpaid**
   - **No Payment**

### Advanced reconciliation

1. **Currency standardisation**
   - Converts all payments to USD using exchange rates
   - Handles multi-currency transactions
2. **Duplicate detection**
   - Identifies potential duplicate payments within time windows
   - Flags transactions with similar amounts
3. **Payment schedule analysis**
   - Calculates days to first payment
   - Analyses payment patterns
   - Identifies installment payments
4. **Risk assessment**
   - Flags orders with multiple payments
   - Identifies significant overpayments
   - Detects unusual payment patterns
5. **Data quality checks**
   - Validates payment dates
   - Filters out failed transactions
   - Handles null values

## Visualization

The dashboard contains six plots:

1. **Payment status distribution:** bar chart of reconciliation statuses
2. **Order value distribution:** histogram comparing paid orders with all orders
3. **Payment rate analysis:** distribution of payment completeness
4. **Payment timing analysis:** histogram of days to first payment
5. **Payment methods:** pie chart of payment method usage
6. **Risk analysis:** order value by risk level

## Output Examples

*Illustrative figures; your generated data will differ.*

### Basic summary report

```
Total Orders:             500
Total Order Value:        $45,231.50
Total Payments Received:  $43,120.75
Orders Fully Paid:        380
Orders Underpaid:         85
Orders Overpaid:          20
Orders No Payment:        15
```

### Sample reconciliation results

| order_id | total_amount | total_paid | difference | status | high_risk |
| --- | --- | --- | --- | --- | --- |
| ORD-00001 | $150.00 | $150.00 | $0.00 | Fully Paid | False |
| ORD-00002 | $75.50 | $50.00 | $25.50 | Underpaid | False |
| ORD-00003 | $200.00 | $210.00 | -$10.00 | Overpaid | True |

## Contributing

Contributions are welcome.

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/AmazingFeature`
3. Commit your changes: `git commit -m "Add AmazingFeature"`
4. Push to the branch: `git push origin feature/AmazingFeature`
5. Open a Pull Request

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Faker](https://faker.readthedocs.io/) for realistic data generation
- [pandas](https://pandas.pydata.org/docs/) for data manipulation
- [Matplotlib](https://matplotlib.org/) and [Seaborn](https://seaborn.pydata.org/) for visualisation

## Links

- Project: https://github.com/vincentius474/order-payment-reconciliation
- [Python virtual environments guide](https://realpython.com/python-virtual-environments-a-primer/)

If this project helped you, consider giving it a star on GitHub.
