import io
import pandas as pd

def export_schedule_excel(df):
    buf=io.BytesIO()
    with pd.ExcelWriter(buf,engine="openpyxl") as w:
        df.to_excel(w,index=False)
    buf.seek(0)
    return buf.getvalue()
