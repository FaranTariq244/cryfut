import streamlit as st
import matplotlib.pyplot as plt

st.set_page_config(page_title="Futures P/L Calculator", layout="wide")
st.title("Futures Profit & Loss Calculator")

def calculate_pnl(position, entry, market, amount, leverage):
    if entry == 0:
        return 0.0, 0.0
    quantity = amount * leverage / entry
    if position == "Long":
        profit = (market - entry) * quantity
    else:
        profit = (entry - market) * quantity
    profit_percent = (profit / amount) * 100
    return round(profit, 2), round(profit_percent, 2)

def calculate_liquidation_price(entry, leverage, wallet_balance, amount, position):
    if entry == 0 or leverage == 0:
        return 0.0
    maintenance_margin_rate = 0.005
    total_balance = wallet_balance if margin_mode == "Cross" else amount
    if position == "Long":
        liq_price = entry * (1 - (total_balance * (1 - maintenance_margin_rate)) / (amount * leverage))
    else:
        liq_price = entry * (1 + (total_balance * (1 - maintenance_margin_rate)) / (amount * leverage))
    return round(liq_price, 6)

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Trade Setup")

    col_margin_leverage = st.columns(2)
    with col_margin_leverage[0]:
        margin_mode = st.radio("Margin Mode:", ["Cross", "Isolated"], horizontal=True)
    with col_margin_leverage[1]:
        leverage = st.number_input("Leverage (x):", min_value=1, max_value=500, value=20)

    position_type = st.radio("Position Type:", ["Long", "Short"], horizontal=True)

    col_wallet_amount = st.columns(2)
    if margin_mode == "Cross":
        with col_wallet_amount[0]:
            wallet_balance = st.number_input("Wallet Balance (USD):", min_value=0.0, format="%.2f")
        with col_wallet_amount[1]:
            invested_amount = st.number_input("Amount Invested (USD):", min_value=0.0, format="%.2f")
    else:
        wallet_balance = 0.0
        with col_wallet_amount[1]:
            invested_amount = st.number_input("Amount Invested (USD):", min_value=0.0, format="%.2f")

    col_entry_market = st.columns(2)
    with col_entry_market[0]:
        entry_price = st.number_input("Entry Price:", min_value=0.0, format="%.6f")
    with col_entry_market[1]:
        market_price = st.number_input("Current Market Price:", min_value=0.0, format="%.6f", value=entry_price)

    col_tp_sl_input = st.columns(2)
    with col_tp_sl_input[0]:
        tp_yield_pct = st.number_input("Target Profit on Capital (%)", min_value=0.0, value=40.0, format="%.2f")
    with col_tp_sl_input[1]:
        sl_yield_pct = st.number_input("Max Loss on Capital (%)", min_value=0.0, value=40.0, format="%.2f")

    if st.button("Calculate Profit/Loss"):
        profit, profit_percent = calculate_pnl(position_type, entry_price, market_price, invested_amount, leverage)
        liq_price = calculate_liquidation_price(entry_price, leverage, wallet_balance, invested_amount, position_type)

        with col2:
            st.subheader("Result")
            color = "green" if profit >= 0 else "red"
            st.markdown(f"""
            <div style='border:2px solid #ccc; border-radius:12px; padding:20px; background-color:#f9f9f9;'>
                <h4>Trade Summary</h4>
                <ul>
                    <li><b>Position:</b> <span style='color:{'green' if position_type=='Short' else 'red'}'>{position_type}</span></li>
                    <li><b>Margin Mode:</b> {margin_mode}</li>
                    <li><b>Leverage:</b> {leverage}x</li>
                    <li><b>Entry Price:</b> ${entry_price}</li>
                    <li><b>Current Market Price:</b> ${market_price}</li>
                    <li><b>Profit:</b> <span style='color:{color}'>${profit}</span></li>
                    <li><b>Profit %:</b> <span style='color:{color}'>{profit_percent}%</span></li>
                    <li><b>Liquidation Price:</b> ${liq_price}</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

        chart_col, _ = st.columns([1, 0.01])

        dca_losses = [20, 40, 60]
        if position_type == "Long":
            dca_prices = [entry_price * (1 - (loss / 100) / leverage) for loss in dca_losses]
        else:
            dca_prices = [entry_price * (1 + (loss / 100) / leverage) for loss in dca_losses]

        all_prices = [entry_price] + dca_prices
        max_dca_budget = wallet_balance - invested_amount if margin_mode == "Cross" else 0
        suggested_dca = round(min(max_dca_budget, invested_amount), 2)
        all_amounts = [invested_amount] + [suggested_dca] * len(dca_prices)
        total_amount = sum(all_amounts)
        avg_price = sum(p * a for p, a in zip(all_prices, all_amounts)) / total_amount

        tp_price = avg_price + (tp_yield_pct / 100) * invested_amount / (invested_amount * leverage / avg_price)
        sl_price = avg_price - (sl_yield_pct / 100) * invested_amount / (invested_amount * leverage / avg_price)

        if position_type == "Short":
            tp_price = avg_price - (tp_yield_pct / 100) * invested_amount / (invested_amount * leverage / avg_price)
            sl_price = avg_price + (sl_yield_pct / 100) * invested_amount / (invested_amount * leverage / avg_price)

        if position_type == "Long" and sl_price <= liq_price:
            sl_price = liq_price
        elif position_type == "Short" and sl_price >= liq_price:
            sl_price = liq_price

        with chart_col:
            st.subheader("Trade Price Levels")
            fig, ax = plt.subplots(figsize=(10, 2))
            prices = [liq_price, entry_price, market_price]
            labels = ['Liquidation', 'Entry', 'Current']
            colors = ['red', 'blue', 'green']

            for price, label, color in zip(prices, labels, colors):
                ax.axvline(price, label=f"{label}: ${price:.2f}", color=color, linewidth=2)

            liq_distance_percent = abs((market_price - liq_price) / market_price) * 100
            ax.text((liq_price + market_price) / 2, 0.4, f"Distance to Liq: {liq_distance_percent:.2f}%", ha='center', va='center', fontsize=10, color='black', transform=ax.get_xaxis_transform())

            for i, dca_price in enumerate(dca_prices):
                ax.axvline(dca_price, linestyle='--', color='gold', linewidth=1.5, label=f"DCA {i+1}: ${dca_price:.2f}")

            ax.axvline(tp_price, linestyle=':', color='lime', linewidth=2, label=f"TP: ${tp_price:.2f}")
            ax.axvline(sl_price, linestyle=':', color='red', linewidth=2, label=f"SL: ${sl_price:.2f}")

            ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.2), ncol=3)
            ax.set_xlim(min(prices + dca_prices + [tp_price, sl_price]) * 0.95, max(prices + dca_prices + [tp_price, sl_price]) * 1.05)
            ax.set_yticks([])
            ax.set_xlabel("Price Range")
            ax.set_title("Trade Visualization")
            st.pyplot(fig)

        with col2:
            st.subheader("DCA & Risk Management")

            risk_level = "Safe" if liq_distance_percent >= 20 else "Medium Risk" if liq_distance_percent >= 10 else "High Risk"
            risk_color = "green" if risk_level == "Safe" else "orange" if risk_level == "Medium Risk" else "red"

            dca_lines = ""
            for i, loss_pct in enumerate(dca_losses):
                dca_price = entry_price * (1 - (loss_pct / 100) / leverage) if position_type == "Long" else entry_price * (1 + (loss_pct / 100) / leverage)
                dca_lines += f"<li>${dca_price:.2f} (-{loss_pct}% loss)</li>"

            st.markdown(f"""
            <div style='border:2px solid #ccc; border-radius:12px; padding:20px; background-color:#f9f9f9;'>
                <h4>Risk & DCA Strategy</h4>
                <ul>
                    <li><b>Risk Level:</b> <span style='color:{risk_color}'>{risk_level}</span> (Liq is {liq_distance_percent:.2f}% away)</li>
                    <li><b>Max Suggested DCA Amount:</b> ${suggested_dca}</li>
                    <li><b>DCA Tip:</b> First entry around -20% loss, followed by more if needed.</li>
                    <li><b>DCA Entry Suggestions:</b>
                        <ul>{dca_lines}<li><b>Avg Entry After DCA:</b> ${avg_price:.2f}</li></ul>
                    </li>
                    <li><b>TP Target:</b> ${tp_price:.2f}</li>
                    <li><b>SL Target:</b> ${sl_price:.2f}</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
    else:
        with col2:
            st.info("Enter values and click 'Calculate Profit/Loss' to see the results.")
