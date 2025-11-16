import pandas as pd

def monthly(P,r,n):
    r=r/100/12
    return P*(r*(1+r)**n)/((1+r)**n-1)

def recalc_all(state):
    fin=state.data['finance']
    P=fin['so_tien_vay']; r=fin['lai_suat_p_a']; n=fin['thoi_han_thang']
    pay=monthly(P,r,n); bal=P
    rows=[]
    for m in range(1,n+1):
        interest=bal*r/100/12
        principal=pay-interest
        bal-=principal
        rows.append({"month":m,"payment":pay,"interest":interest,"principal":principal,"balance":bal})
    df=pd.DataFrame(rows)
    state.summary={"monthly_payment":pay}
    return df
