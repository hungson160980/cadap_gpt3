import streamlit as st
from src.logic.finance import recalc_all

def sidebar_api_input():
    return st.sidebar.text_input("Gemini API Key", type="password")

def layout_tabs(data, recalc_callback):
    tabs=st.tabs(["Định danh","Tài chính","TSĐB","Tính toán","Biểu đồ"])
    with tabs[0]:
        idf=data["identification"]
        idf["ten"]=st.text_input("Tên",idf["ten"])
        idf["cccd"]=st.text_input("CCCD",idf["cccd"])
        idf["dia_chi"]=st.text_input("Địa chỉ",idf["dia_chi"])
        idf["phone"]=st.text_input("SĐT",idf["phone"])

    with tabs[1]:
        fin=data["finance"]
        fin["muc_dich"]=st.text_input("Mục đích",fin["muc_dich"])
        fin["tong_nhu_cau"]=st.number_input("Tổng nhu cầu",value=fin["tong_nhu_cau"])
        fin["von_doi_ung"]=st.number_input("Vốn đối ứng",value=fin["von_doi_ung"])
        fin["so_tien_vay"]=st.number_input("Tiền vay",value=fin["so_tien_vay"])
        fin["lai_suat_p_a"]=st.number_input("Lãi suất",value=fin["lai_suat_p_a"])
        fin["thoi_han_thang"]=st.number_input("Thời hạn",value=fin["thoi_han_thang"])

    with tabs[2]:
        col=data["collateral"]
        for i,c in enumerate(col):
            c["loai"]=st.text_input(f"Loại {i+1}",c["loai"])
            c["gia_tri"]=st.number_input(f"Giá trị {i+1}",value=c["gia_tri"])
            c["dia_chi"]=st.text_input(f"Địa chỉ {i+1}",c["dia_chi"])
            c["ltv_percent"]=st.number_input(f"LTV {i+1}",value=c["ltv_percent"])

    with tabs[3]:
        df=recalc_callback()
        st.dataframe(df.head())

    with tabs[4]:
        import altair as alt
        df=recalc_callback()
        chart=alt.Chart(df).mark_line().encode(x="month",y="payment")
        st.altair_chart(chart, use_container_width=True)
