# main.py (Full working)
import streamlit as st
from src.ui.components import sidebar_api_input, layout_tabs
from src.logic.parser_docx import parse_docx_streamlit
from src.logic.finance import recalc_all
from src.export.export_excel import export_schedule_excel
from src.export.export_docx import export_docx
from src.ai.gemini_client import GeminiClient

st.set_page_config(page_title='Thẩm định vay vốn', layout='wide')
st.title("Thẩm định Phương Án Sử Dụng Vốn")

api_key = sidebar_api_input()

uploaded = st.file_uploader("Upload DOCX", type=["docx"])
if "data" not in st.session_state:
    st.session_state.data = None

if uploaded:
    st.session_state.data = parse_docx_streamlit(uploaded)
    st.success("Đã đọc DOCX!")

if st.session_state.data is None:
    st.session_state.data = {
        "identification":{"ten":"Nguyễn Văn A","cccd":"123456789","dia_chi":"HN","phone":"0900000000"},
        "finance":{"muc_dich":"Mua nhà","tong_nhu_cau":5000000000,
                   "von_doi_ung":1000000000,"so_tien_vay":4000000000,
                   "lai_suat_p_a":8.5,"thoi_han_thang":60},
        "collateral":[{"loai":"BĐS","gia_tri":6000000000,
                        "dia_chi":"HN","ltv_percent":80,"giay_to":"GCN"}],
        "income":{"thu_nhap_hang_thang":100000000,"chi_phi_hang_thang":30000000}
    }

layout_tabs(st.session_state.data, recalc_callback=lambda: recalc_all(st.session_state))

st.markdown("---")
st.header("Xuất dữ liệu")

if st.button("Xuất Excel"):
    df = recalc_all(st.session_state)
    x = export_schedule_excel(df)
    st.download_button("Tải Excel", x, file_name="ke_hoach.xlsx")

if st.button("Xuất DOCX"):
    df = recalc_all(st.session_state)
    x = export_docx(st.session_state.data, df)
    st.download_button("Tải DOCX", x, file_name="bao_cao.docx")

if api_key:
    p = st.sidebar.text_input("Chat Gemini")
    if st.sidebar.button("Gửi"):
        st.sidebar.write(GeminiClient(api_key).chat(p))
