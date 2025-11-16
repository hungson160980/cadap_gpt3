import streamlit as st
from src.ui.components import sidebar_api_input, layout_tabs
from src.logic.parser_docx import parse_docx_streamlit
from src.logic.finance import recalc_all
from src.export.export_excel import export_schedule_excel
from src.export.export_docx import export_docx
from src.ai.gemini_client import GeminiClient

st.set_page_config(page_title='Thẩm định vay vốn', layout='wide')

st.title("📝 THẨM ĐỊNH PHƯƠNG ÁN SỬ DỤNG VỐN")

api_key = sidebar_api_input()

uploaded = st.file_uploader("📄 Upload file .docx mẫu PASDV", type=["docx"])
if "data" not in st.session_state:
    st.session_state.data = None

# =========================================
# 1. NHẬN & PARSE FILE DOCX
# =========================================
if uploaded:
    with st.spinner("Đang phân tích file DOCX..."):
        parsed = parse_docx_streamlit(uploaded)
        st.session_state.data = parsed
    st.success("🎉 Đã trích xuất dữ liệu từ file!")

# Nếu chưa upload → dùng dữ liệu mẫu
if st.session_state.data is None:
    st.info("⚠️ Chưa upload file DOCX → dùng dữ liệu mẫu")
    st.session_state.data = {
        "identification": {
            "ten": "Nguyễn Văn Minh",
            "cccd": "001085012345",
            "dia_chi": "Số 123 — Bắc Ninh",
            "phone": "0912345678",
        },
        "finance": {
            "muc_dich": "Mua nhà",
            "tong_nhu_cau": 5_000_000_000,
            "von_doi_ung": 1_000_000_000,
            "so_tien_vay": 4_000_000_000,
            "lai_suat_p_a": 8.5,
            "thoi_han_thang": 60,
        },
        "collateral": [
            {
                "loai": "BĐS",
                "gia_tri": 6_000_000_000,
                "dia_chi": "Lô 45, Nguyễn Văn Cừ",
                "ltv_percent": 75,
                "giay_to": "GCN 123"
            }
        ],
        "income": {
            "thu_nhap_hang_thang": 100_000_000,
            "chi_phi_hang_thang": 45_000_000
        }
    }

# =========================================
# 2. GIAO DIỆN EDIT (Tabs)
# =========================================
layout_tabs(st.session_state.data, recalc_callback=lambda: recalc_all(st.session_state))


# =========================================
# 3. XUẤT FILE DOCX & EXCEL
# =========================================
st.markdown("---")
st.header("📤 Xuất dữ liệu / Báo cáo")

col1, col2 = st.columns(2)
with col1:
    if st.button("📊 Xuất Excel – Kế hoạch trả nợ"):
        df = recalc_all(st.session_state)
        excel_bytes = export_schedule_excel(df)
        st.download_button(
            "Tải Excel (.xlsx)",
            data=excel_bytes,
            file_name="ke_hoach_tra_no.xlsx",
        )

with col2:
    if st.button("📝 Xuất DOCX – Báo cáo thẩm định"):
        df = recalc_all(st.session_state)
        docx_bytes = export_docx(st.session_state.data, df)
        st.download_button(
            "Tải DOCX",
            data=docx_bytes,
            file_name="bao_cao_thamdinh.docx",
        )

# =========================================
# 4. AI GEMINI
# =========================================
st.sidebar.markdown("---")
st.sidebar.subheader("🤖 Gemini AI")

if api_key:
    gem = GeminiClient(api_key)
    question = st.sidebar.text_area("Nhập câu hỏi cho AI")
    if st.sidebar.button("Gửi"):
        st.sidebar.write(gem.chat(question))
else:
    st.sidebar.info("Nhập API Key để bật AI Gemini")
