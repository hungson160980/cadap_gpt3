from docx import Document
import re

def parse_vnd(s):
    if not s: return 0
    s = s.replace('.', '').replace(',', '').replace(' ', '')
    try: return int(s)
    except: return 0

def parse_docx_streamlit(f):
    doc=Document(f)
    txt="\n".join(p.text for p in doc.paragraphs)

    name=re.search(r'Họ và tên[:\s]*(.*)', txt)
    ten=name.group(1).strip() if name else ""

    cccd=re.search(r'(?:CCCD|CMND)[:\s]*(\d{9,12})', txt)
    cccd=cccd.group(1) if cccd else ""

    tong=re.search(r'Tổng nhu cầu.*?([\d\., ]+) đồng', txt)
    t=parse_vnd(tong.group(1)) if tong else 0

    von=re.search(r'Vốn đối ứng.*?([\d\., ]+) đồng', txt)
    v=parse_vnd(von.group(1)) if von else 0

    vay=re.search(r'(?:Vốn vay|Số tiền vay).*?([\d\., ]+) đồng', txt)
    sv=parse_vnd(vay.group(1)) if vay else t

    lai=re.search(r'Lãi suất.*?([\d\.,]+)', txt)
    ls=float(lai.group(1).replace(',','.')) if lai else 8.5

    th=re.search(r'Thời hạn.*?(\d+)', txt)
    thang=int(th.group(1)) if th else 60

    return {
        "identification":{"ten":ten,"cccd":cccd,"dia_chi":"","phone":""},
        "finance":{"muc_dich":"","tong_nhu_cau":t,"von_doi_ung":v,
                   "so_tien_vay":sv,"lai_suat_p_a":ls,"thoi_han_thang":thang},
        "collateral":[{"loai":"BĐS","gia_tri":0,"dia_chi":"","ltv_percent":0,"giay_to":""}],
        "income":{"thu_nhap_hang_thang":0,"chi_phi_hang_thang":0}
    }
