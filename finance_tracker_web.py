import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import json
import os
from datetime import datetime

# Page Config
st.set_page_config(page_title="Finance Tracker", page_icon="💰", layout="wide", initial_sidebar_state="auto")

# Custom CSS
st.markdown("""
<style>
    .main .block-container {padding: 1.5rem; max-width: 95%}
    .stButton>button {width: 100%; height: 2.8rem; font-size: 1rem}
    h1 {text-align: center;}
</style>
""", unsafe_allow_html=True)

st.title("💰 Finance Tracker 2026")

# Session State
if 'transactions' not in st.session_state:
    st.session_state.transactions = []
    st.session_state.file = 'finance_2026.json'

# Load/Save
def load():
    if os.path.exists(st.session_state.file):
        with open(st.session_state.file) as f:
            st.session_state.transactions = [t for t in json.load(f) if all(k in t for k in ['Date','Category','Amount','Type'])]

def save():
    backup = f"{st.session_state.file}.bak_{datetime.now():%Y%m%d_%H%M}"
    if os.path.exists(st.session_state.file): os.rename(st.session_state.file, backup)
    with open(st.session_state.file, 'w') as f: json.dump(st.session_state.transactions, f, indent=2)

load()  # Auto-load

# Sidebar
with st.sidebar:
    st.header("Controls")
    if st.button("💾 Save"): save(); st.success("Saved!")
    if st.button("🔄 Reload"): load(); st.rerun()
    st.caption(f"📅 {datetime.today():%b %d, %Y}")

# Tabs
tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "➕ Add", "📈 More"])

with tab1:
    if not st.session_state.transactions:
        st.info("No data yet — add a transaction!")
    else:
        df = pd.DataFrame(st.session_state.transactions)
        df['Date'] = pd.to_datetime(df['Date'])

        income = df[df['Amount'] > 0]['Amount'].sum()
        expense = abs(df[df['Amount'] < 0]['Amount'].sum())
        savings = income - expense
        rate = savings / income * 100 if income else 0

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Income", f"₹{income:,.0f}")
        c2.metric("Expense", f"₹{expense:,.0f}")
        c3.metric("Savings", f"₹{savings:,.0f}")
        c4.metric("Rate", f"{rate:.1f}%")

        with st.expander("Recent Transactions"):
            disp = df.copy()
            disp['Amt'] = disp['Amount'].abs()
            disp['Net'] = disp['Amount']
            disp = disp[['Date','Type','Category','Amt','Net']]
            disp['Date'] = disp['Date'].dt.strftime('%b %d')
            st.dataframe(disp.style.format({'Amt':'₹{:.0f}','Net':'₹{:+,.0f}'}), hide_index=True, use_container_width=True)

with tab2:
    col1, col2 = st.columns(2)
    type_ = col1.radio("Type", ["Income", "Expense"], horizontal=True)
    date = col2.date_input("Date", datetime.today())

    category = st.text_input("Category")
    amount = st.number_input("Amount ₹", min_value=0.01, step=500.0)

    if st.button("Add Transaction", type="primary", use_container_width=True):
        if category.strip():
            st.session_state.transactions.append({
                'Date': date.strftime('%Y-%m-%d'),
                'Category': category.strip(),
                'Amount': amount if type_ == "Income" else -amount,
                'Type': type_
            })
            st.success("Added!")
            st.rerun()
        else:
            st.error("Enter category")

with tab3:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Loan Eligibility")
        if st.session_state.transactions:
            df = pd.DataFrame(st.session_state.transactions)
            df['Date'] = pd.to_datetime(df['Date'])
            months = max(df['Date'].dt.to_period('M').nunique(), 1)
            avg_inc = df[df['Amount']>0]['Amount'].sum() / months
            avg_exp = abs(df[df['Amount']<0]['Amount'].sum()) / months
            emi = (avg_inc - avg_exp) * 0.4
            if emi > 0:
                loan = emi * ((1 + 0.09/12)**(240) - 1) / (0.09/12 * (1 + 0.09/12)**240)
                st.success(f"**₹{loan:,.0f}** @9% 20yrs")
                st.caption(f"Avg Income ₹{avg_inc:,.0f} | Expense ₹{avg_exp:,.0f}")
            else:
                st.warning("Need more income data")
        else:
            st.info("Add data first")

        st.subheader("Charts")
        if st.session_state.transactions:
            df = pd.DataFrame(st.session_state.transactions)
            df['Date'] = pd.to_datetime(df['Date'])
            df['Month'] = df['Date'].dt.to_period('M')
            monthly = df.groupby('Month')['Amount'].sum()
            fig, ax = plt.subplots()
            monthly.plot(kind='bar', color=['g' if x>0 else 'r' for x in monthly], ax=ax)
            ax.set_title("Monthly Flow")
            st.pyplot(fig, use_container_width=True)

    with col2:
        st.subheader("Export / Import")
        if st.session_state.transactions:
            exp = pd.DataFrame(st.session_state.transactions)
            exp['Amount (₹)'] = exp['Amount'].abs()
            exp = exp[['Date','Type','Category','Amount (₹)']]
            st.download_button("📥 Download CSV", exp.to_csv(index=False).encode(),
                               f"finance_{datetime.now():%Y%m%d}.csv", "text/csv")
        
        uploaded = st.file_uploader("📤 Upload CSV", type="csv")
        if uploaded:
            df_up = pd.read_csv(uploaded)
            if all(c in df_up.columns for c in ['Date','Type','Category','Amount (₹)']):
                added = 0
                for _, r in df_up.iterrows():
                    t = r['Type'].strip()
                    if t in ['Income','Expense']:
                        st.session_state.transactions.append({
                            'Date': str(r['Date'])[:10],
                            'Category': str(r['Category']).strip(),
                            'Amount': r['Amount (₹)'] if t=='Income' else -abs(r['Amount (₹)']),
                            'Type': t
                        })
                        added += 1
                st.success(f"Imported {added} rows")
                st.rerun()
            else:
                st.error("Missing columns")

st.caption("Concise • Responsive • MoraX, Jan 2026 🚀")