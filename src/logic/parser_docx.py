# src/logic/parser_docx.py
import re
from docx import Document

def parse_vnd_number(s):
    """Chuyển chuỗi có dấu '.' hoặc ',' thành int (VND)."""
    if not s:
        return 0
    s = str(s)
    s = s.replace(".", "").replace(",", "").replace(" ", "")
    try:
        return int(float(s))
    except:
        return 0

def first_group(pattern, text, flags=0):
    m = re.search(pattern, text, flags)
    return m.group(1).strip() if m else None

def find_collateral_blocks(lines):
    """
    Trả về list các dòng hoặc block chứa thông tin TSĐB.
    Heuristic: tìm các dòng có 'Tài sản' / 'Bất động sản' / 'Giá trị' / 'Tài sản bảo đảm'
    """
    blocks = []
    for i, L in enumerate(lines):
        low = L.lower()
        if any(k in low for k in ("tài sản", "tài sản bảo đảm", "bất động sản", "giá trị")):
            # collect a small window of lines to form a block
            window = " ".join(lines[i:i+6])
            blocks.append(window)
    return blocks

def parse_docx_streamlit(uploaded_file):
    """
    Parse docx into a dict with keys:
      - identification: {ten, cccd, dia_chi, phone, email}
      - finance: {muc_dich, tong_nhu_cau, von_doi_ung, so_tien_vay, lai_suat_p_a, thoi_han_thang}
      - collateral: list of {loai, gia_tri, dia_chi, ltv_percent, giay_to}
      - income: {thu_nhap_hang_thang, chi_phi_hang_thang}
    Uses heuristics tuned for PASDV-like documents.
    """
    doc = Document(uploaded_file)
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text and p.text.strip() != ""]
    text = "\n".join(paragraphs)
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    # Identification
    identification = {"ten": "", "cccd": "", "dia_chi": "", "phone": "", "email": ""}

    # Try several patterns to find name
    name = first_group(r"Họ và tên[:\s]*([A-Za-zÀ-ỹ0-9\.\-\s]+)", text, flags=re.IGNORECASE)
    if not name:
        name = first_group(r"^Họ và tên\s*[:\-]\s*([^\n\r]+)", text, flags=re.IGNORECASE)
    if not name:
        # fallback: look for line starting with "1. Họ và tên"
        name = first_group(r"\d+\.\s*Họ và tên[:\s]*([^\n\r]+)", text, flags=re.IGNORECASE)
    identification["ten"] = name or ""

    # CCCD / CMND
    cccd = first_group(r"(?:CCCD|CMND|Số CMND|Số CCCD)[:\s]*([0-9]{9,12})", text, flags=re.IGNORECASE)
    identification["cccd"] = cccd or ""

    # Phone
    phone = first_group(r"(?:Số điện thoại|Điện thoại|ĐT|Phone)[:\s]*([\d\+\-\s]{7,20})", text, flags=re.IGNORECASE)
    identification["phone"] = phone or ""

    # Address
    addr = first_group(r"(?:Nơi cư trú|Địa chỉ|Đ/c|Địa chỉ hiện tại)[:\s]*([^\n\r]+)", text, flags=re.IGNORECASE)
    identification["dia_chi"] = addr or ""

    # Email (optional)
    email = first_group(r"Email[:\s]*([^\s,;]+@[^\s,;]+)", text, flags=re.IGNORECASE)
    identification["email"] = email or ""

    # Finance
    finance = {
        "muc_dich": "",
        "tong_nhu_cau": 0,
        "von_doi_ung": 0,
        "so_tien_vay": 0,
        "lai_suat_p_a": 8.5,
        "thoi_han_thang": 60
    }

    # Purpose
    purpose = first_group(r"Mục đích[:\s]*([^\n\r]+)", text, flags=re.IGNORECASE)
    finance["muc_dich"] = purpose or finance["muc_dich"]

    # Numbers (attempt several phrasings)
    tn = first_group(r"Tổng nhu cầu vốn[:\s]*([0-9\.,\s]+)\s*đồng", text, flags=re.IGNORECASE)
    if not tn:
        tn = first_group(r"Tổng nhu cầu[:\s]*([0-9\.,\s]+)\s*đ", text, flags=re.IGNORECASE)
    if tn:
        finance["tong_nhu_cau"] = parse_vnd_number(tn)

    vo = first_group(r"Vốn đối ứng[:\s]*([0-9\.,\s]+)\s*đồng", text, flags=re.IGNORECASE)
    if vo:
        finance["von_doi_ung"] = parse_vnd_number(vo)

    sv = first_group(r"(?:Số tiền vay|Vốn vay|Vốn vay Agribank)[:\s]*([0-9\.,\s]+)\s*đồng", text, flags=re.IGNORECASE)
    if sv:
        finance["so_tien_vay"] = parse_vnd_number(sv)
    else:
        # fallback: if not explicit, use tổng nhu cầu - vốn đối ứng
        if finance["tong_nhu_cau"] and finance["von_doi_ung"]:
            finance["so_tien_vay"] = max(0, finance["tong_nhu_cau"] - finance["von_doi_ung"])
        elif finance["tong_nhu_cau"]:
            finance["so_tien_vay"] = finance["tong_nhu_cau"]

    # Interest rate
    lai = first_group(r"Lãi suất[:\s]*([0-9\.,]+)\s*%?", text, flags=re.IGNORECASE)
    if lai:
        try:
            finance["lai_suat_p_a"] = float(lai.replace(",", "."))
        except:
            finance["lai_suat_p_a"] = finance["lai_suat_p_a"]

    # Term (months)
    th = first_group(r"Thời hạn(?: vay)?[:\s]*([0-9]+)\s*tháng", text, flags=re.IGNORECASE)
    if th:
        try:
            finance["thoi_han_thang"] = int(th)
        except:
            finance["thoi_han_thang"] = finance["thoi_han_thang"]

    # Income & cost
    income = {"thu_nhap_hang_thang": 0, "chi_phi_hang_thang": 0}
    thu = first_group(r"(?:Thu nhập|Tổng thu nhập).*?([0-9\.,\s]+)\s*đồng", text, flags=re.IGNORECASE)
    if thu:
        income["thu_nhap_hang_thang"] = parse_vnd_number(thu)
    chi = first_group(r"(?:Tổng chi phí|Chi phí).*?([0-9\.,\s]+)\s*đồng", text, flags=re.IGNORECASE)
    if chi:
        income["chi_phi_hang_thang"] = parse_vnd_number(chi)

    # Collateral detection (take blocks)
    collateral = []
    coll_blocks = find_collateral_blocks(lines)
    for blk in coll_blocks:
        # find first numeric value in block
        val = first_group(r"([0-9\.,\s]+)\s*đồng", blk, flags=re.IGNORECASE)
        valn = parse_vnd_number(val) if val else 0
        # try address in block
        addr_b = first_group(r"Địa chỉ[:\s]*([^\n\r]+)", blk, flags=re.IGNORECASE)
        # find type mention
        loai = "Bất động sản" if ("bất động sản" in blk.lower() or "nhà" in blk.lower()) else "Tài sản"
        collateral.append({"loai": loai, "gia_tri": valn, "dia_chi": addr_b or "", "ltv_percent": 0.0, "giay_to": ""})

    # ensure at least one collateral record exists
    if not collateral:
        collateral.append({"loai": "", "gia_tri": 0, "dia_chi": "", "ltv_percent": 0.0, "giay_to": ""})

    # Final defaults
    finance.setdefault("muc_dich", finance.get("muc_dich", ""))
    finance.setdefault("tong_nhu_cau", finance.get("tong_nhu_cau", 0))
    finance.setdefault("von_doi_ung", finance.get("von_doi_ung", 0))
    finance.setdefault("so_tien_vay", finance.get("so_tien_vay", 0))
    finance.setdefault("lai_suat_p_a", finance.get("lai_suat_p_a", 8.5))
    finance.setdefault("thoi_han_thang", finance.get("thoi_han_thang", 60))

    return {
        "identification": identification,
        "finance": finance,
        "collateral": collateral,
        "income": income
    }
