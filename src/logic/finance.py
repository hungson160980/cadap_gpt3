# src/logic/finance.py
import pandas as pd

def monthly_payment(principal, annual_rate_percent, months):
    """
    Trả về khoản thanh toán hàng tháng (annuity).
    principal: số tiền vay (int/float)
    annual_rate_percent: %/năm (vd 8.5)
    months: số tháng
    """
    principal = float(principal or 0)
    months = int(months or 0)
    if principal <= 0 or months <= 0:
        return 0.0
    monthly_rate = annual_rate_percent / 100.0 / 12.0
    if monthly_rate == 0:
        return principal / months
    # chuẩn công thức annuity
    return principal * (monthly_rate * (1 + monthly_rate) ** months) / ((1 + monthly_rate) ** months - 1)

def amortization_schedule(principal, annual_rate_percent, months):
    """
    Trả về DataFrame gồm các cột: month, payment, interest, principal, balance
    interest, principal, payment, balance là float
    """
    principal = float(principal or 0)
    months = int(months or 0)
    if months <= 0 or principal <= 0:
        # empty dataframe with expected columns
        return pd.DataFrame(columns=["month", "payment", "interest", "principal", "balance"])
    monthly_rate = annual_rate_percent / 100.0 / 12.0
    payment = monthly_payment(principal, annual_rate_percent, months)
    balance = principal
    rows = []
    for m in range(1, months + 1):
        interest = balance * monthly_rate
        principal_paid = payment - interest
        # numeric guard: if last payment rounding may overshoot
        if principal_paid > balance:
            principal_paid = balance
            payment = interest + principal_paid
        balance = balance - principal_paid
        rows.append({
            "month": m,
            "payment": float(payment),
            "interest": float(interest),
            "principal": float(principal_paid),
            "balance": float(max(balance, 0.0))
        })
    df = pd.DataFrame(rows)
    return df

def recalc_all(session_state):
    """
    session_state: st.session_state-like dict/object with key 'data'
    Return: schedule DataFrame and populate session_state['summary']
    """
    data = session_state.get("data", {}) if isinstance(session_state, dict) else session_state.data
    finance = data.get("finance", {}) or {}
    income = data.get("income", {}) or {}
    collateral = data.get("collateral", []) or []

    principal = finance.get("so_tien_vay") or finance.get("tong_nhu_cau") or 0
    rate = finance.get("lai_suat_p_a") if finance.get("lai_suat_p_a") is not None else 8.5
    months = int(finance.get("thoi_han_thang") or 0)

    schedule = amortization_schedule(principal, rate, months)

    monthly_debt_service = float(schedule["payment"].iloc[0]) if (not schedule.empty) else 0.0
    annual_ds = monthly_debt_service * 12.0
    annual_income = float(income.get("thu_nhap_hang_thang") or 0) * 12.0
    dsr = (annual_ds / annual_income * 100.0) if annual_income > 0 else None

    coll_value = sum([c.get("gia_tri") or 0 for c in collateral])
    ltv = (principal / coll_value * 100.0) if coll_value > 0 else None

    summary = {
        "monthly_payment": monthly_debt_service,
        "dsr_percent": dsr,
        "ltv_percent": ltv,
        "principal": principal,
        "annual_income": annual_income
    }

    # populate into session_state consistently (works for both dict and streamlit's session_state)
    try:
        session_state["summary"] = summary
    except Exception:
        try:
            session_state.summary = summary
        except:
            pass

    return schedule
