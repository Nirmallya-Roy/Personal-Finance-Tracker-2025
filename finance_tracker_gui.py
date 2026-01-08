import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import json
import os
from datetime import datetime

class PersonalFinanceTrackerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Personal Finance Tracker - 2026 Edition 💰")
        self.root.geometry("1000x700")
        self.root.configure(bg="#f0f0f0")

        self.filename = 'finance_data_2026.json'
        self.transactions = []
        self.load_data()

        self.setup_ui()
        self.refresh_summary()

    def load_data(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r') as f:
                    data = json.load(f)
                    for trans in data:
                        if all(k in trans for k in ['Date', 'Category', 'Amount', 'Type']):
                            self.transactions.append(trans)
            except Exception as e:
                messagebox.showerror("Error", f"Could not load data: {e}")

    def save_data(self):
        backup_file = self.filename + '.backup_' + datetime.now().strftime("%Y%m%d_%H%M%S")
        if os.path.exists(self.filename):
            os.replace(self.filename, backup_file)  # Backup old file
        
        with open(self.filename, 'w') as f:
            json.dump(self.transactions, f, indent=4)
        messagebox.showinfo("Saved", "Data saved successfully!")

    def add_transaction(self, trans_type):
        date = simpledialog.askstring("Date", f"Enter date (YYYY-MM-DD)\nLeave blank for today ({datetime.now().strftime('%Y-%m-%d')})")
        if date is None:
            return
        if not date.strip():
            date = datetime.now().strftime('%Y-%m-%d')

        category = simpledialog.askstring("Category", "Enter category (e.g., Salary, Rent, Food)")
        if not category:
            messagebox.showwarning("Input Required", "Category is required!")
            return

        amount_str = simpledialog.askstring("Amount", "Enter amount (₹)")
        if not amount_str:
            return
        try:
            amount = float(amount_str)
            if amount <= 0:
                raise ValueError()
        except:
            messagebox.showerror("Invalid", "Please enter a valid positive number.")
            return

        try:
            datetime.strptime(date, '%Y-%m-%d')
            transaction = {
                'Date': date,
                'Category': category.strip(),
                'Amount': amount if trans_type == 'Income' else -abs(amount),
                'Type': trans_type
            }
            self.transactions.append(transaction)
            messagebox.showinfo("Success", f"{trans_type} of ₹{amount:,.2f} added!")
            self.refresh_summary()
            self.refresh_treeview()
        except:
            messagebox.showerror("Error", "Invalid date format. Use YYYY-MM-DD")

    def get_dataframe(self):
        if not self.transactions:
            return pd.DataFrame()
        df = pd.DataFrame(self.transactions)
        df['Date'] = pd.to_datetime(df['Date'])
        return df.sort_values('Date')

    def refresh_summary(self):
        df = self.get_dataframe()
        if df.empty:
            self.summary_label.config(text="No transactions yet. Add some to get started!")
            return

        total_income = df[df['Amount'] > 0]['Amount'].sum()
        total_expenses = abs(df[df['Amount'] < 0]['Amount'].sum())
        net_savings = total_income - total_expenses
        savings_rate = (net_savings / total_income * 100) if total_income > 0 else 0

        summary_text = (
            f"Total Income: ₹{total_income:,.2f}    |    "
            f"Total Expenses: ₹{total_expenses:,.2f}\n"
            f"Net Savings: ₹{net_savings:,.2f}    |    "
            f"Savings Rate: {savings_rate:.1f}%"
        )
        self.summary_label.config(text=summary_text)

    def refresh_treeview(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        df = self.get_dataframe()
        if not df.empty:
            display_df = df.copy()
            display_df['Amount'] = display_df['Amount'].abs()
            display_df['Signed'] = df['Amount']
            for _, row in display_df.iterrows():
                self.tree.insert('', 'end', values=(
                    row['Date'].strftime('%Y-%m-%d'),
                    row['Type'],
                    row['Category'],
                    f"₹{row['Amount']:,.2f}",
                    f"₹{row['Signed']:,+,.2f}"
                ))

    def show_loan_eligibility(self):
        df = self.get_dataframe()
        if df.empty:
            messagebox.showinfo("No Data", "Add transactions first to calculate loan eligibility.")
            return

        months = max(len(df.resample('M', on='Date')), 1)
        avg_income = df[df['Amount'] > 0]['Amount'].sum() / months
        avg_expense = abs(df[df['Amount'] < 0]['Amount'].sum()) / months
        disposable = avg_income - avg_expense
        max_emi = disposable * 0.4

        if max_emi <= 0:
            messagebox.showinfo("Loan Eligibility", "Insufficient disposable income for loan EMI.")
            return

        monthly_rate = 0.09 / 12
        months_tenure = 20 * 12
        loan_amount = max_emi * ((1 + monthly_rate)**months_tenure - 1) / (monthly_rate * (1 + monthly_rate)**months_tenure)

        info = (
            f"Avg Monthly Income: ₹{avg_income:,.2f}\n"
            f"Avg Monthly Expenses: ₹{avg_expense:,.2f}\n"
            f"Disposable Income: ₹{disposable:,.2f}\n"
            f"Max EMI (40%): ₹{max_emi:,.2f}\n\n"
            f"Eligible Loan Amount:\n₹{loan_amount:,.2f}\n@ 9% interest for 20 years"
        )
        messagebox.showinfo("Loan Eligibility", info)

    def show_charts(self):
        df = self.get_dataframe()
        if df.empty:
            messagebox.showinfo("No Data", "Add transactions to visualize trends.")
            return

        chart_window = tk.Toplevel(self.root)
        chart_window.title("Financial Trends")
        chart_window.geometry("1000x600")

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

        # Monthly Cash Flow
        df_monthly = df.resample('M', on='Date')['Amount'].sum()
        ax1.bar(df_monthly.index.strftime('%b %Y'), df_monthly.values,
                color=['green' if x > 0 else 'red' for x in df_monthly.values])
        ax1.set_title('Monthly Net Cash Flow')
        ax1.set_ylabel('Amount (₹)')
        ax1.tick_params(axis='x', rotation=45)
        ax1.grid(axis='y', alpha=0.3)

        # Expense Pie
        expenses = df[df['Amount'] < 0].groupby('Category')['Amount'].sum().abs()
        if len(expenses) > 1:
            ax2.pie(expenses, labels=expenses.index, autopct='%1.1f%%', startangle=90)
            ax2.set_title('Expense Breakdown')
        else:
            ax2.text(0.5, 0.5, 'Not enough\ncategories', ha='center', va='center', fontsize=14)
            ax2.set_title('Expense Breakdown')

        plt.tight_layout()
        canvas = FigureCanvasTkAgg(fig, chart_window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def export_csv(self):
        if not self.transactions:
            messagebox.showinfo("Empty", "No transactions to export.")
            return
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile=f"finance_export_{datetime.now().strftime('%Y%m%d')}.csv"
        )
        if filename:
            df = self.get_dataframe()
            export_df = df.copy()
            export_df['Amount (₹)'] = export_df['Amount'].abs()
            export_df = export_df[['Date', 'Type', 'Category', 'Amount (₹)']]
            export_df.to_csv(filename, index=False)
            messagebox.showinfo("Exported", f"Saved to {filename}")

    def import_csv(self):
        filename = filedialog.askopenfilename(
            filetypes=[("CSV files", "*.csv")]
        )
        if not filename:
            return
        try:
            df = pd.read_csv(filename)
            required = ['Date', 'Type', 'Category', 'Amount (₹)']
            if not all(col in df.columns for col in required):
                messagebox.showerror("Format Error", f"CSV must have columns: {', '.join(required)}")
                return

            count = 0
            for _, row in df.iterrows():
                try:
                    trans_type = row['Type'].strip()
                    if trans_type not in ['Income', 'Expense']:
                        continue
                    self.transactions.append({
                        'Date': str(row['Date'])[:10],
                        'Category': str(row['Category']).strip(),
                        'Amount': row['Amount (₹)'] if trans_type == 'Income' else -abs(row['Amount (₹)']),
                        'Type': trans_type
                    })
                    count += 1
                except:
                    continue
            messagebox.showinfo("Imported", f"{count} transactions imported!")
            self.refresh_summary()
            self.refresh_treeview()
        except Exception as e:
            messagebox.showerror("Error", f"Import failed: {e}")

    def setup_ui(self):
        style = ttk.Style()
        style.theme_use('clam')

        # Header
        header = tk.Label(self.root, text="Personal Finance Tracker 2026", font=("Helvetica", 18, "bold"), bg="#f0f0f0", fg="#2c3e50")
        header.pack(pady=10)

        # Summary
        self.summary_label = tk.Label(self.root, text="", font=("Helvetica", 12), bg="#f0f0f0", fg="#27ae60")
        self.summary_label.pack(pady=5)

        # Buttons Frame
        btn_frame = tk.Frame(self.root, bg="#f0f0f0")
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="➕ Add Income", command=lambda: self.add_transaction("Income")).grid(row=0, column=0, padx=10)
        ttk.Button(btn_frame, text="➖ Add Expense", command=lambda: self.add_transaction("Expense")).grid(row=0, column=1, padx=10)
        ttk.Button(btn_frame, text="💳 Loan Eligibility", command=self.show_loan_eligibility).grid(row=0, column=2, padx=10)
        ttk.Button(btn_frame, text="📊 View Charts", command=self.show_charts).grid(row=0, column=3, padx=10)
        ttk.Button(btn_frame, text="📤 Export CSV", command=self.export_csv).grid(row=1, column=0, padx=10, pady=5)
        ttk.Button(btn_frame, text="📥 Import CSV", command=self.import_csv).grid(row=1, column=1, padx=10, pady=5)
        ttk.Button(btn_frame, text="💾 Save & Exit", command=lambda: [self.save_data(), self.root.quit()]).grid(row=1, column=3, padx=10, pady=5)

        # Transactions Table
        table_frame = tk.LabelFrame(self.root, text="Recent Transactions", font=("Helvetica", 12))
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)

        cols = ("Date", "Type", "Category", "Amount", "Net")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=12)
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=150)
        self.tree.pack(side=tk.LEFT, fill="both", expand=True)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill="y")

        self.refresh_treeview()

        self.root.protocol("WM_DELETE_WINDOW", lambda: [self.save_data(), self.root.destroy()])


if __name__ == "__main__":
    root = tk.Tk()
    app = PersonalFinanceTrackerGUI(root)
    root.mainloop()