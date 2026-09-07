"""
list_schema.py
يجيب كل الجداول والـ Views الموجودة فعليًا في قاعدة البيانات + أعمدة كل واحد،
مباشرة من السيرفر (من غير ما تكتبيهم يدوي في كود تاني)، وبيسألك تحفظي ملف
الإكسيل فين (زي باقي البرامج).

الفكرة: Supabase بيبني تلقائيًا "OpenAPI schema" لكل جدول/فيو متاح على REST API،
والسكريبت ده بيجيبه ويطلعه في شكل مرتب + ملف Excel.
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import requests
import pandas as pd
from datetime import datetime

# --- نفس بيانات الاتصال المستخدمة في باقي البرامج ---
SUPABASE_URL = "https://akjyrmmqsnxdbkslxmvb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFranlybW1xc254ZGJrc2x4bXZiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2NDg4NTE4NywiZXhwIjoyMDgwNDYxMTg3fQ.hNBIzJZ118KZL53RvDBwxFlQ2XEbS7CL__ktJBjyu2M"


def fetch_openapi_schema():
    """يجيب الـ OpenAPI spec من PostgREST، ودي بتحتوي كل الجداول/الفيوز المتاحة على REST API"""
    url = f"{SUPABASE_URL}/rest/v1/"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Accept-Profile": "public",
    }
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()


def extract_tables_and_columns(spec):
    """
    PostgREST بيرجع الشكل ده في نسختين محتملتين:
    - OpenAPI 2.0 (Swagger): spec["definitions"][table_name]["properties"]
    - OpenAPI 3.0:           spec["components"]["schemas"][table_name]["properties"]
    السكريبت بيجرب الاتنين.
    """
    schemas = {}

    if "definitions" in spec:
        schemas = spec["definitions"]
    elif "components" in spec and "schemas" in spec["components"]:
        schemas = spec["components"]["schemas"]

    result = {}
    for name, definition in schemas.items():
        props = definition.get("properties", {})
        columns = []
        for col_name, col_info in props.items():
            col_type = col_info.get("format") or col_info.get("type") or "?"
            description = col_info.get("description", "")
            columns.append({"العمود": col_name, "النوع": col_type, "ملاحظات": description})
        result[name] = columns

    return result


def save_schema_to_excel(tables, save_path):
    """يحفظ شيت 'ملخص' + شيت لكل جدول/فيو بأعمدته"""
    with pd.ExcelWriter(save_path, engine="openpyxl") as writer:
        summary_rows = [{"الاسم": name, "عدد الأعمدة": len(cols)} for name, cols in sorted(tables.items())]
        pd.DataFrame(summary_rows).to_excel(writer, sheet_name="ملخص", index=False)

        used_sheet_names = set()
        for name, cols in tables.items():
            df = pd.DataFrame(cols) if cols else pd.DataFrame({"ملاحظة": ["لا توجد أعمدة"]})
            # اسم الشيت في إكسيل أقصاه 31 حرف ولازم يكون فريد
            base_name = (name[:31] if name else "بدون_اسم")
            sheet_name = base_name
            i = 1
            while sheet_name in used_sheet_names:
                suffix = f"_{i}"
                sheet_name = base_name[: 31 - len(suffix)] + suffix
                i += 1
            used_sheet_names.add(sheet_name)
            df.to_excel(writer, sheet_name=sheet_name, index=False)


def run_export(save_path, loading_window, status_label):
    try:
        status_label.config(text="⏳ بيجيب هيكل القاعدة من السيرفر...")
        root.update()
        spec = fetch_openapi_schema()
        tables = extract_tables_and_columns(spec)

        if not tables:
            loading_window.destroy()
            messagebox.showerror("خطأ", "مقدرش يجيب أي جداول. تأكد من الـ SUPABASE_URL والـ KEY.")
            return

        save_schema_to_excel(tables, save_path)

        loading_window.destroy()
        status_label.config(text="✅ النظام جاهز للعمل")
        messagebox.showinfo(
            "نجاح",
            f"✅ تم استخراج هيكل القاعدة بنجاح\n\n"
            f"عدد الجداول/الفيوز: {len(tables)}\n"
            f"الملف: {save_path}"
        )
    except Exception as e:
        if loading_window.winfo_exists():
            loading_window.destroy()
        status_label.config(text="❌ حدث خطأ")
        messagebox.showerror("خطأ", f"فشل جلب هيكل القاعدة:\n{str(e)}")


def start_export():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_path = filedialog.asksaveasfilename(
        defaultextension=".xlsx",
        filetypes=[("Excel files", "*.xlsx")],
        initialfile=f"schema_snapshot_{timestamp}.xlsx"
    )
    if not save_path:
        return

    loading_window = tk.Toplevel(root)
    loading_window.title("جاري الاستخراج")
    loading_window.geometry("300x120")
    loading_window.grab_set()
    tk.Label(loading_window, text="⏳ جاري جلب هيكل القاعدة...", font=("Arial", 9)).pack(pady=15)
    prog = ttk.Progressbar(loading_window, mode='indeterminate')
    prog.pack(fill='x', padx=30)
    prog.start()

    threading.Thread(target=run_export, args=(save_path, loading_window, status_label)).start()


# ============================================================
# --- واجهة بسيطة ---
# ============================================================
root = tk.Tk()
root.title("استخراج هيكل قاعدة البيانات")
root.geometry("420x220")
root.configure(bg="#f8f9fa")

tk.Label(root, text="📋 استخراج هيكل قاعدة البيانات",
         font=("Arial", 14, "bold"), bg="#f8f9fa", fg="#2c3e50", pady=12).pack(fill="x")

tk.Label(
    root,
    text="بيجيب كل الجداول والـ Views الموجودة فعليًا على السيرفر دلوقتي،\n"
         "وكل عمود جواهم، ويحفظهم في ملف Excel تختاري مكانه بنفسك.",
    font=("Arial", 9), bg="#f8f9fa", fg="#64768a", wraplength=380, justify="center"
).pack(pady=(0, 15))

tk.Button(
    root, text="📥 استخراج وحفظ Excel...",
    command=start_export,
    bg="#16a085", fg="white", font=("Arial", 11, "bold")
).pack(pady=5, ipadx=10, ipady=6)

status_label = tk.Label(root, text="✅ النظام جاهز للعمل",
                         font=("Arial", 9), bg="#f8f9fa", fg="#7f8c8d")
status_label.pack(pady=(15, 0))

if __name__ == "__main__":
    root.mainloop()
