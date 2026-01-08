import matplotlib.pyplot as plt
import pandas as pd
import json
import os
from datetime import datetime

class PersonalFinanceTracker:
    def __init__(self, filename='finance_data_2025.json'):
        self.filename = filename
        self.transactions = []
        self.load_data()

    def load_data(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r') as f:
                    data = json.load(f)
                    for trans in data:
                        if all(key in trans for key in ['Date', 'Category', 'Amount', 'Type']):
                            self.transactions.append(trans)
                    print(f"Data loaded: {len(self.transactions)} transactions\n")
            except Exception as e:
                print(f"Error loading data: {e}. Starting fresh.\n")
        else:
            print("No saved data found. Starting fresh.\n")

    def save_data(self):
        backup_file = self.filename + '.backup_' + datetime.now().strftime("%Y%m%d_%H%M%S")
        if os.path.exists(self.filename):
            os.rename(self.filename, backup_file)
            print(f"Backup created: {backup_file}")
        
        with open(self.filename, 'w') as f:
            json.dump(self.transactions, f, indent=4)
        print(f"Data saved to {self.filename}\n")

    def add_transaction(self, date, category, amount, trans_type):
        try:
            datetime.strptime(date, '%Y-%m-%d')
            amount = float(amount)
            if trans_type not in ['Income', 'Expense']:
                raise ValueError("Type must be 'Income' or 'Expense'")
            
            transaction = {
                'Date': date,
                'Category': category,
                'Amount': amount if trans_type == 'Income' else -abs(amount),
                'Type': trans_type
            }
            self.transactions.append(transaction)
            print(f"✓ Added: {trans_type} ₹{abs(amount):,.2f} - {category} on {date}\n")
            return True
        except Exception as e:
            print(f"✗ Invalid input: {e}\n")
            return False

    def get_dataframe(self):
        if not self.transactions:
            return pd.DataFrame()
        df = pd.DataFrame(self.transactions)
        df['Date'] = pd.to_datetime(df['Date'])
        return df.sort_values('Date')

    def analyze_statements(self):
        df = self.get_dataframe()
        if df.empty:
            print("No transactions to analyze yet.\n")
            return
        
        total_income = df[df['Amount'] > 0]['Amount'].sum()
        total_expenses = abs(df[df['Amount'] < 0]['Amount'].sum())
        net_savings = total_income - total_expenses
        
        print("=== 2025/2026 Financial Summary ===")
        print(f"Total Income       : ₹{total_income:,.2f}")
        print(f"Total Expenses     : ₹{total_expenses:,.2f}")
        print(f"Net Savings        : ₹{net_savings:,.2f}")
        print(f"Savings Rate       : {(net_savings / total_income * 100) if total_income > 0 else 0:.2f}%\n")

        print("Expenses by Category:")
        expenses = df[df['Amount'] < 0].groupby('Category')['Amount'].sum().abs()
        if expenses.empty:
            print("No expenses recorded yet.\n")
        else:
            print(expenses.sort_values(ascending=False).to_string(dtype=False, formatters={'Amount': '₹{:,.2f}'.format}))
            print()

    def calculate_loan_eligibility(self, max_emi_ratio=0.4, tenure_years=20, interest_rate=0.09):
        df = self.get_dataframe()
        if df.empty:
            print("No data available for loan calculation.\n")
            return
        
        # Assuming 12 months of data or annualized
        total_months = len(df.resample('M', on='Date')) if 'Date' in df.columns else 1
        avg_monthly_income = df[df['Amount'] > 0]['Amount'].sum() / max(total_months, 1)
        avg_monthly_expenses = abs(df[df['Amount'] < 0]['Amount'].sum()) / max(total_months, 1)
        disposable = avg_monthly_income - avg_monthly_expenses
        max_emi = disposable * max_emi_ratio

        if max_emi <= 0:
            print("Insufficient disposable income for loan EMI.\n")
            return

        monthly_rate = interest_rate / 12
        months = tenure_years * 12
        loan_amount = max_emi * ((1 + monthly_rate)**months - 1) / (monthly_rate * (1 + monthly_rate)**months)

        print("=== Loan Eligibility Estimate ===")
        print(f"Avg Monthly Income   : ₹{avg_monthly_income:,.2f}")
        print(f"Avg Monthly Expenses : ₹{avg_monthly_expenses:,.2f}")
        print(f"Disposable Income    : ₹{disposable:,.2f}")
        print(f"Max EMI (40%)        : ₹{max_emi:,.2f}")
        print(f"Eligible Loan Amount : ₹{loan_amount:,.2f} @ {interest_rate*100}% for {tenure_years} years\n")

    def visualize_trends(self):
        df = self.get_dataframe()
        if df.empty:
            print("No data to visualize yet.\n")
            return
        
        # Monthly net flow
        df['Month'] = df['Date'].dt.to_period('M')
        df_monthly = df.groupby('Month')['Amount'].sum()
        
        plt.figure(figsize=(12, 6))
        bars = plt.bar(range(len(df_monthly)), df_monthly.values, 
                       color=['green' if x > 0 else 'red' for x in df_monthly.values])
        plt.title('Monthly Net Cash Flow')
        plt.ylabel('Amount (₹)')
        plt.xlabel('Month')
        plt.xticks(range(len(df_monthly)), [str(m) for m in df_monthly.index], rotation=45)
        plt.grid(axis='y', alpha=0.3)
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + (height/abs(height))*500 if height != 0 else 500,
                     f'₹{height:,.0f}', ha='center', va='bottom' if height > 0 else 'top')
        
        plt.tight_layout()
        plt.show()

        # Expense pie chart
        expenses = df[df['Amount'] < 0].groupby('Category')['Amount'].sum().abs()
        if not expenses.empty and len(expenses) > 1:
            plt.figure(figsize=(8, 8))
            plt.pie(expenses, labels=expenses.index, autopct='%1.1f%%', startangle=90)
            plt.title('Expense Breakdown by Category')
            plt.show()
        elif len(expenses) == 1:
            print("Only one expense category — skipping pie chart.\n")


# === Interactive Menu Loop ===
if __name__ == "__main__":
    print("🚀 Personal Finance Tracker - 2026 Edition 🚀\n")
    tracker = PersonalFinanceTracker()

    while True:
        print("═" * 50)
        print("                  MAIN MENU                  ")
        print("═" * 50)
        print("1. Add Income")
        print("2. Add Expense")
        print("3. View Financial Summary")
        print("4. Check Loan Eligibility")
        print("5. Visualize Trends (Charts)")
        print("6. Save & Exit")
        print("7. Exit Without Saving")
        print("═" * 50)

        choice = input("Enter your choice (1-7): ").strip()

        if choice == '1' or choice == '2':
            trans_type = "Income" if choice == '1' else "Expense"
            print(f"\n--- Add {trans_type} ---")
            date = input(f"Date (YYYY-MM-DD, today: {datetime.now().strftime('%Y-%m-%d')}): ").strip()
            if not date:
                date = datetime.now().strftime('%Y-%m-%d')
            category = input("Category (e.g., Salary, Rent, Groceries): ").strip()
            if not category:
                print("✗ Category required.\n")
                continue
            try:
                amount = float(input("Amount (₹): ").strip())
                if amount <= 0:
                    print("✗ Amount must be positive.\n")
                    continue
            except:
                print("✗ Invalid amount.\n")
                continue
            
            tracker.add_transaction(date, category, amount, trans_type)

        elif choice == '3':
            print("\n")
            tracker.analyze_statements()

        elif choice == '4':
            print("\n")
            tracker.calculate_loan_eligibility()

        elif choice == '5':
            print("\nOpening charts...\n")
            tracker.visualize_trends()

        elif choice == '6':
            tracker.save_data()
            print("Thank you for using Personal Finance Tracker! Stay wealthy! 💰")
            break

        elif choice == '7':
            print("Exiting without saving. Goodbye!")
            break

        else:
            print("✗ Invalid choice. Please try again.\n")

        input("Press Enter to continue...")  # Pause before clearing menu