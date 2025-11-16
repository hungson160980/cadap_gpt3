# main.py
import streamlit as st
from src.ui.components import sidebar_api_input, layout_tabs, format_vnd
from src.logic.parser_docx import parse_docx_streamlit
from src.logic.finance import recalc_all
from src.export.export_excel import export_schedule_excel
from src.export.export_docx import export_docx
from src.ai.gemini_client import GeminiClient
import altair as alt

st.set_page_config(page_title="Thẩm định vay vốn", layout="wide")
st.title("📝 Ứng dụng Thẩm định Phương Án Sử Dụng Vốn")

api_key = sidebar_api_input()

# Upload & parse
uploaded = st.file_uploader("Upload file .docx (mẫu PASDV)", type=["docx"])
if "data" not in st.session_state:
    st.session_state.data = None

if uploaded is not None:
    with st.spinner("Đang phân tích file..."):
        st.session_state.data = parse_docx_streamlit(uploaded)
    st.success("Đã trích xuất dữ liệu — kiểm tra và chỉnh sửa nếu cần.")

# default sample when no upload
if st.session_state.data is None:
    st.info("Chưa upload file — dùng dữ liệu mẫu (có thể chỉnh sửa).")
    st.session_state.data = {
        "identification": {"ten": "", "cccd": "", "dia_chi": "", "phone": ""},
        "finance": {"muc_dich": "", "tong_nhu_cau": 0, "von_doi_ung": 0, "so_tien_vay": 0, "lai_suat_p_a": 8.5, "thoi_han_thang": 60},
        "collateral": [{"loai": "", "gia_tri": 0, "dia_chi": "", "ltv_percent": 0.0, "giay_to": ""}],
        "income": {"thu_nhap_hang_thang": 0, "chi_phi_hang_thang": 0}
    }

# show parsed identification summary at top for quick check
idf = st.session_state.data.get("identification", {})
col1, col2, col3 = st.columns(3)
with col1:
    st.subheader("👤 Khách hàng")
    st.write("Họ và tên:", idf.get("ten", ""))
    st.write("CCCD/CMND:", idf.get("cccd", ""))
with col2:
    st.subheader("📞 Liên hệ")
    st.write("Địa chỉ:", idf.get("dia_chi", ""))
    st.write("SĐT:", idf.get("phone", ""))
with col3:
    st.subheader("🎯 Phương án")
    fin = st.session_state.data.get("finance", {})
    st.write("Mục đích:", fin.get("muc_dich", ""))
    st.write("Số tiền vay:", format_vnd(fin.get("so_tien_vay", 0)))

# Main editable tabs (component handles editing)
layout_tabs(st.session_state.data, recalc_callback=lambda: recalc_all(st.session_state))

# After editing / parsing — compute schedule
schedule_df = recalc_all(st.session_state)

st.markdown("---")
st.header("📈 Kết quả & Lịch trả nợ")

# Summary metrics
summary = st.session_state.get("summary", {})
c1, c2, c3 = st.columns(3)
c1.metric("Thanh toán hàng tháng", format_vnd(round(summary.get("monthly_payment", 0))))
dsr_text = f'{summary["dsr_percent"]:.2f}%' if summary.get("dsr_percent") is not None else "Không có dữ liệu"
c2.metric("DSR (ước tính)", dsr_text)
ltv_text = f'{summary["ltv_percent"]:.2f}%' if summary.get("ltv_percent") is not None else "Không có dữ liệu"
c3.metric("LTV (ước tính)", ltv_text)

# Table (first 24 months)
st.subheader("Lịch trả nợ (24 tháng đầu)")
if not schedule_df.empty:
    st.dataframe(schedule_df.head(24).assign(payment=lambda df: df["payment"].apply(lambda x: f"{int(round(x)):,}".replace(",", "."))))

# Chart - Altair
st.subheader("Biểu đồ nghĩa vụ trả nợ hàng tháng")
if not schedule_df.empty:
    chart = alt.Chart(schedule_df).mark_line().encode(
        x=alt.X("month:Q", title="Tháng"),
        y=alt.Y("payment:Q", title="Thanh toán (đồng)")
    ).properties(width="container", height=300)
    st.altair_chart(chart, use_container_width=True)

# Export area
st.markdown("---")
st.header("📤 Xuất")
colx, coly = st.columns(2)
with colx:
    if st.button("Xuất Excel"):
        xbytes = export_schedule_excel(schedule_df)
        st.download_button("Tải Excel (.xlsx)", data=xbytes, file_name="ke_hoach_tra_no.xlsx")
with coly:
    if st.button("Xuất DOCX"):
        dbytes = export_docx(st.session_state.data, schedule_df)
        st.download_button("Tải DOCX", data=dbytes, file_name="bao_cao_thamdinh.docx")

# Sidebar: Gemini (if API key provided)
st.sidebar.markdown("---")
st.sidebar.header("AI / Gemini")
if api_key:
    gem = GeminiClient(api_key)
    q = st.sidebar.text_area("Nhập prompt phân tích")
    if st.sidebar.button("Gọi Gemini"):
        with st.spinner("Gọi Gemini..."):
            res = gem.analyze_risk("edited", st.session_state.data)
            st.sidebar.text_area("Kết quả", value=res, height=200)
else:
    st.sidebar.info("Nhập API key vào thanh bên để bật Gemini")
