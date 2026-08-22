import tkinter as tk
from tkinter import filedialog, messagebox, ttk, simpledialog
import pandas as pd
import numpy as np
import threading
from supabase import create_client, Client
from datetime import datetime
import os
import json

# --- إعدادات الاتصال بـ Supabase ---
SUPABASE_URL = "https://akjyrmmqsnxdbkslxmvb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFranlybW1xc254ZGJrc2x4bXZiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2NDg4NTE4NywiZXhwIjoyMDgwNDYxMTg3fQ.hNBIzJZ118KZL53RvDBwxFlQ2XEbS7CL__ktJBjyu2M"

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    print(f"Connection Error: {e}")

VIEW_NAME_LAGNA = "بيانات اللجنة المعلقة (لم يتم تحوي"

# ✅ جدول أرشيف اللجان القديمة (يتراكم شهر بعد شهر - لا يُمسح أبدًا)
OLD_COMMITTEES_TABLE = "اللجان_القديمة"

# --- تعريف الجداول والـ Views ---
TABLES_AND_VIEWS = {
    "Tables": {
        "assessments": "جدول التقييمات",
        "bank_loans_data": "جدول بيانات قروض البنك",
        "loans": "جدول القروض",
        "meza_cards": "جدول بطاقات ميزة",
        "operations": "جدول العمليات",
        "users": "جدول المستخدمين",
        "قيد_اللجنة_7": "جدول قيد اللجنة 7",
        OLD_COMMITTEES_TABLE: "جدول أرشيف اللجان القديمة"
    },
    "Views": {
        "bank_export_view": "فيو تصدير البنك",
        "client_full_profile": "فيو الملف الكامل للعميل",
        "operations_with_details": "فيو العمليات مع التفاصيل",
        "summary_bank_export_view": "فيو ملخص تصدير البنك",
        "البيانات كاملة المومرفوعة للتنفيز": "فيو البيانات الكاملة للتنفيذ",
        "بيانات_عمليات_الرفع_الكاملة": "فيو بيانات عمليات الرفع الكاملة",
        VIEW_NAME_LAGNA: "فيو بيانات اللجنة المعلقة"
    }
}

# --- تعريف الـ Views مع جملة CREATE الخاصة بها ---
VIEW_DEFINITIONS = {
    "bank_export_view": """
CREATE OR REPLACE VIEW bank_export_view AS
SELECT b.*, l.*
FROM bank_loans_data b
LEFT JOIN loans l ON b.رقم_البطاقة = l.الرقم_القومى
WHERE b.تاريخ_الرفع >= CURRENT_DATE - INTERVAL '30 days'
""",
    "client_full_profile": """
CREATE OR REPLACE VIEW client_full_profile AS
SELECT l.*, a.*, m.*
FROM loans l
LEFT JOIN assessments a ON l.الرقم_القومى = a.رقم_البطاقة
LEFT JOIN meza_cards m ON l.الرقم_القومى = m.رقم_البطاقة
WHERE l.تاريخ_القرض IS NOT NULL
""",
    "operations_with_details": """
CREATE OR REPLACE VIEW operations_with_details AS
SELECT o.*, l.الاسم, l.رقم_القرض, meza.رقم_بطاقة_ميزة
FROM operations o
LEFT JOIN loans l ON o.رقم_القومى = l.الرقم_القومى
LEFT JOIN meza_cards meza ON o.رقم_القومى = meza.رقم_البطاقة
ORDER BY o.تاريخ_الرفع DESC
""",
    "summary_bank_export_view": """
CREATE OR REPLACE VIEW summary_bank_export_view AS
SELECT 
    DATE(تاريخ_الرفع) as تاريخ_الرفع,
    COUNT(*) as عدد_القروض,
    SUM(قيمة_القرض) as اجمالي_القروض,
    SUM(المصاريف_الادارية) as اجمالي_المصاريف
FROM bank_loans_data
GROUP BY DATE(تاريخ_الرفع)
ORDER BY DATE(تاريخ_الرفع) DESC
""",
    "البيانات كاملة المومرفوعة للتنفيز": """
CREATE OR REPLACE VIEW "البيانات كاملة المومرفوعة للتنفيز" AS
SELECT l.*, a.*, b.*, m.*
FROM loans l
LEFT JOIN assessments a ON l.الرقم_القومى = a.رقم_البطاقة
LEFT JOIN bank_loans_data b ON l.الرقم_القومى = b.رقم_البطاقة
LEFT JOIN meza_cards m ON l.الرقم_القومى = m.رقم_البطاقة
WHERE l.الحالة = 'موافق عليه'
""",
    "بيانات_عمليات_الرفع_الكاملة": """
CREATE OR REPLACE VIEW "بيانات_عمليات_الرفع_الكاملة" AS
SELECT o.*, u.name as اسم_المستخدم, u.email as بريد_المستخدم
FROM operations o
LEFT JOIN users u ON o.user_id = u.id
WHERE o.نوع_العملية = 'رفع'
ORDER BY o.تاريخ_الرفع DESC
""",
    VIEW_NAME_LAGNA: f"""
CREATE OR REPLACE VIEW "{VIEW_NAME_LAGNA}" AS
SELECT *
FROM bank_loans_data
WHERE تم_التحويل IS NULL OR تم_التحويل = false
ORDER BY تاريخ_الرفع DESC
"""
}

# --- قائمة الجداول التي سيتم مسحها (بدون users وبدون أرشيف اللجان القديمة) ---
TABLES_TO_CLEAR = [
    "assessments",
    "bank_loans_data",
    "loans",
    "meza_cards",
    "operations",
    "قيد_اللجنة_7"
]


def get_current_month_name():
    months_ar = {
        1: "يناير", 2: "فبراير", 3: "مارس", 4: "أبريل",
        5: "مايو", 6: "يونيو", 7: "يوليو", 8: "أغسطس",
        9: "سبتمبر", 10: "أكتوبر", 11: "نوفمبر", 12: "ديسمبر"
    }
    return months_ar[datetime.now().month]


def clear_all_tables():
    password = simpledialog.askstring("تأكيد مسح البيانات",
                                      "⚠️ تحذير: هذا الإجراء سيمسح جميع البيانات من الجداول!\n\n"
                                      "الجداول التي سيتم مسحها:\n"
                                      "- assessments\n- bank_loans_data\n- loans\n"
                                      "- meza_cards\n- operations\n- قيد_اللجنة_7\n\n"
                                      "ملاحظة: جدول users وأرشيف اللجان القديمة لن يتم مسحهما!\n\n"
                                      "أدخل كلمة المرور للمتابعة (123):",
                                      show='*')
    if password != "123":
        messagebox.showerror("خطأ", "❌ كلمة المرور غير صحيحة!\nتم إلغاء عملية المسح.")
        return

    confirm = messagebox.askyesno("تأكيد نهائي",
                                  "⚠️ تحذير نهائي: أنت على وشك مسح جميع البيانات من 6 جداول!\n\n"
                                  "هذا الإجراء لا يمكن التراجع عنه.\n\nهل أنت متأكد 100%؟")
    if not confirm:
        messagebox.showinfo("إلغاء", "تم إلغاء عملية مسح البيانات.")
        return

    def clear_tables_thread():
        win = tk.Toplevel(root)
        win.title("جاري المسح")
        win.geometry("300x120")
        win.grab_set()
        tk.Label(win, text="⏳ جاري مسح البيانات...", font=("Arial", 9)).pack(pady=15)
        prog = ttk.Progressbar(win, mode='indeterminate')
        prog.pack(fill='x', padx=30)
        prog.start()
        try:
            cleared_tables, failed_tables = [], []
            for table_name in TABLES_TO_CLEAR:
                try:
                    supabase.table(table_name).delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
                    cleared_tables.append(table_name)
                except:
                    try:
                        response = supabase.table(table_name).select("*").limit(1).execute()
                        if response.data:
                            pk = list(response.data[0].keys())[0]
                            supabase.table(table_name).delete().neq(pk, "---DEL---").execute()
                            cleared_tables.append(table_name)
                        else:
                            failed_tables.append(f"{table_name}: الجدول فارغ بالفعل")
                    except Exception as e2:
                        failed_tables.append(f"{table_name}: {str(e2)[:50]}")
            win.destroy()
            if cleared_tables:
                messagebox.showinfo("نجاح",
                                    f"✅ تم مسح البيانات بنجاح من {len(cleared_tables)} جدول\n\n"
                                    f"الجداول: {', '.join(cleared_tables)}\n\n"
                                    f"❌ فشل: {chr(10).join(failed_tables) if failed_tables else 'لا يوجد'}\n\n"
                                    f"📌 جدول users وأرشيف اللجان القديمة لم يتم مسحهما")
            else:
                messagebox.showerror("خطأ", "❌ فشل مسح جميع الجداول!")
        except Exception as e:
            win.destroy()
            messagebox.showerror("خطأ", f"حدث خطأ:\n{str(e)}")

    threading.Thread(target=clear_tables_thread).start()


def fetch_all_data(table_name):
    try:
        all_data, page, page_size = [], 0, 1000
        while True:
            response = supabase.table(table_name).select("*").range(
                page * page_size, (page + 1) * page_size - 1).execute()
            if not response.data:
                break
            all_data.extend(response.data)
            if len(response.data) < page_size:
                break
            page += 1
        return all_data
    except Exception as e:
        print(f"خطأ في جلب بيانات {table_name}: {str(e)}")
        return []


def safe_sql_value(val):
    if val is None or pd.isna(val):
        return "NULL"
    if isinstance(val, (list, tuple, np.ndarray)):
        try:
            return f"'{json.dumps(val, ensure_ascii=False)}'"
        except:
            return "'[]'"
    if isinstance(val, dict):
        try:
            return f"'{json.dumps(val, ensure_ascii=False)}'"
        except:
            return "'{}'"
    if isinstance(val, (int, np.integer)):
        return str(val)
    if isinstance(val, (float, np.floating)):
        return str(val)
    if isinstance(val, (datetime, pd.Timestamp)):
        return f"'{val.strftime('%Y-%m-%d %H:%M:%S')}'"
    if isinstance(val, str):
        return f"'{val.replace(chr(39), chr(39)*2)}'"
    try:
        return f"'{str(val).replace(chr(39), chr(39)*2)}'"
    except:
        return "NULL"


def export_to_sql_with_views():
    current_month = get_current_month_name()
    current_year = datetime.now().year
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_path = filedialog.asksaveasfilename(
        defaultextension=".sql",
        filetypes=[("SQL files", "*.sql")],
        initialfile=f"supabase_export_{current_month}_{current_year}_{timestamp}.sql"
    )
    if not save_path:
        return
    try:
        with open(save_path, 'w', encoding='utf-8') as f:
            f.write(f"-- تصدير قاعدة البيانات - {current_month} {current_year}\n")
            f.write(f"-- تاريخ التصدير: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            for table_name, description in TABLES_AND_VIEWS["Tables"].items():
                status_label.config(text=f"جاري تصدير: {table_name}...")
                root.update()
                data = fetch_all_data(table_name)
                f.write(f"-- جدول: {table_name} ({len(data)} سجل)\n")
                if data:
                    df = pd.DataFrame(data)
                    columns = list(df.columns)
                    f.write(f"CREATE TABLE IF NOT EXISTS {table_name} (\n")
                    for i, col in enumerate(columns):
                        f.write(f"    {col} TEXT{',' if i < len(columns)-1 else ''}\n")
                    f.write(");\n\n")
                    for idx, row in df.iterrows():
                        try:
                            values = [safe_sql_value(row[col]) for col in columns]
                            f.write(f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(values)});\n")
                        except Exception as re:
                            f.write(f"-- خطأ في السجل {idx+1}: {str(re)}\n")
                    f.write("\n")

            f.write("\n-- الـ VIEWS\n\n")
            for view_name in VIEW_DEFINITIONS:
                f.write(VIEW_DEFINITIONS[view_name])
                f.write("\n\n")

        status_label.config(text="اكتمل التصدير!")
        messagebox.showinfo("نجاح", f"✅ تم التصدير بنجاح\n{save_path}")
    except Exception as e:
        status_label.config(text="حدث خطأ!")
        messagebox.showerror("خطأ", f"فشل التصدير:\n{str(e)}")


def export_all_data_to_excel_with_views():
    current_month = get_current_month_name()
    current_year = datetime.now().year
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_path = filedialog.asksaveasfilename(
        defaultextension=".xlsx",
        filetypes=[("Excel files", "*.xlsx")],
        initialfile=f"supabase_data_{current_month}_{current_year}_{timestamp}.xlsx"
    )
    if not save_path:
        return
    try:
        with pd.ExcelWriter(save_path, engine='openpyxl') as writer:
            pd.DataFrame({
                "المعلومة": ["الشهر", "تاريخ التصدير", "عدد الجداول", "عدد الـ Views"],
                "القيمة": [f"{current_month} {current_year}",
                           datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                           len(TABLES_AND_VIEWS["Tables"]),
                           len(TABLES_AND_VIEWS["Views"])]
            }).to_excel(writer, sheet_name="معلومات", index=False)

            for table_name in TABLES_AND_VIEWS["Tables"]:
                status_label.config(text=f"جاري تصدير: {table_name}...")
                root.update()
                data = fetch_all_data(table_name)
                df = pd.DataFrame(data) if data else pd.DataFrame({"ملاحظة": [f"لا توجد بيانات"]})
                df.to_excel(writer, sheet_name=f"جدول_{table_name}"[:31], index=False)

            for view_name in TABLES_AND_VIEWS["Views"]:
                status_label.config(text=f"جاري تصدير فيو: {view_name[:20]}...")
                root.update()
                data = fetch_all_data(view_name)
                df = pd.DataFrame(data) if data else pd.DataFrame({"ملاحظة": [f"لا توجد بيانات"]})
                df.to_excel(writer, sheet_name=f"فيو_{view_name}"[:31], index=False)

        status_label.config(text="اكتمل التصدير!")
        messagebox.showinfo("نجاح", f"✅ تم التصدير بنجاح\n{save_path}")
    except Exception as e:
        status_label.config(text="حدث خطأ!")
        messagebox.showerror("خطأ", f"فشل التصدير:\n{str(e)}")


def start_export_thread(export_function):
    win = tk.Toplevel(root)
    win.title("جاري التصدير")
    win.geometry("300x120")
    win.grab_set()
    tk.Label(win, text="⏳ جاري تصدير البيانات...", font=("Arial", 9)).pack(pady=15)
    prog = ttk.Progressbar(win, mode='indeterminate')
    prog.pack(fill='x', padx=30)
    prog.start()

    def export_wrapper():
        try:
            export_function()
        except Exception as e:
            messagebox.showerror("خطأ", f"حدث خطأ:\n{str(e)}")
        finally:
            if win.winfo_exists():
                win.destroy()

    threading.Thread(target=export_wrapper).start()


def clean_df(df):
    df.columns = df.columns.astype(str).str.strip().str.replace(r'\s+', ' ', regex=True)
    df = df.replace({np.nan: None, 'nan': None, 'NaN': None, 'NaT': None, '': None})
    return df


def format_dates(df, date_cols):
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime('%Y-%m-%d')
            df[col] = df[col].fillna('1900-01-01')
    return df


def process_clear_and_upload(table_name, data_list, pk_column, loading_window):
    try:
        supabase.table(table_name).delete().neq(pk_column, "---DEL---").execute()
        total_rows = len(data_list)
        for i in range(0, total_rows, 500):
            supabase.table(table_name).insert(data_list[i:i+500]).execute()
        loading_window.destroy()
        messagebox.showinfo("نجاح", f"✅ تم تحديث {table_name} بنجاح.\nإجمالي السجلات: {total_rows}")
    except Exception as e:
        if loading_window.winfo_exists():
            loading_window.destroy()
        messagebox.showerror("خطأ", f"فشل الرفع:\n{str(e)}")


# ✅ جديد: رفع بدون مسح - يُستخدم لأرشيف اللجان القديمة لأنه يتراكم شهر بعد شهر
def process_append_upload(table_name, data_list, loading_window):
    try:
        total_rows = len(data_list)
        for i in range(0, total_rows, 500):
            supabase.table(table_name).insert(data_list[i:i+500]).execute()
        loading_window.destroy()
        messagebox.showinfo("نجاح", f"✅ تم رفع {total_rows} سجل بنجاح إلى أرشيف اللجان القديمة.\n"
                                     f"لم يتم مسح أي بيانات سابقة - البيانات تتراكم شهريًا.")
    except Exception as e:
        if loading_window.winfo_exists():
            loading_window.destroy()
        messagebox.showerror("خطأ", f"فشل الرفع:\n{str(e)}")


def process_smart_insert(table_name, data_list, loading_window):
    success, dups = 0, 0
    try:
        for record in data_list:
            try:
                supabase.table(table_name).insert(record).execute()
                success += 1
            except Exception as e:
                if "duplicate" in str(e).lower():
                    dups += 1
        loading_window.destroy()
        messagebox.showinfo("تقرير الرفع", f"✅ اكتمل:\n- جديد: {success}\n- مكرر: {dups}")
    except Exception as e:
        if loading_window.winfo_exists():
            loading_window.destroy()
        messagebox.showerror("خطأ", str(e))


def process_export_view(view_name, loading_window):
    try:
        response = supabase.table(view_name).select("*").execute()
        if not response.data:
            loading_window.destroy()
            messagebox.showwarning("تنبيه", "التقرير فارغ حالياً.")
            return
        df = pd.DataFrame(response.data)
        loading_window.destroy()
        save_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")],
            initialfile=f"{view_name[:30]}.xlsx"
        )
        if save_path:
            df.to_excel(save_path, index=False, engine='openpyxl')
            messagebox.showinfo("نجاح", "✅ تم تصدير ملف الإكسيل بنجاح.")
    except Exception as e:
        if loading_window.winfo_exists():
            loading_window.destroy()
        messagebox.showerror("خطأ", f"تعذر جلب البيانات:\n{str(e)}")


def start_thread(target, args):
    win = tk.Toplevel(root)
    win.title("جاري العمل")
    win.geometry("300x120")
    win.grab_set()
    tk.Label(win, text="⏳ يرجى الانتظار...", font=("Arial", 9)).pack(pady=15)
    prog = ttk.Progressbar(win, mode='indeterminate')
    prog.pack(fill='x', padx=30)
    prog.start()
    threading.Thread(target=target, args=(*args, win)).start()


def up_loans():
    path = filedialog.askopenfilename(title="اختر ملف القروض")
    if path:
        df = clean_df(pd.read_excel(path, dtype=str))
        df = format_dates(df, ["تاريخ القرض", "تاريخ الميلاد"])
        start_thread(process_clear_and_upload, ("loans", df.to_dict(orient='records'), "الرقم القومى"))


def up_assessments():
    path = filedialog.askopenfilename(title="اختر ملف التقييمات")
    if path:
        df = clean_df(pd.read_excel(path, dtype=str))
        df = format_dates(df, ["تاريخ التقرير"])
        start_thread(process_clear_and_upload, ("assessments", df.to_dict(orient='records'), "رقم_البطاقة"))


def up_c7():
    path = filedialog.askopenfilename(title="قيد اللجنة 7")
    if path:
        df = clean_df(pd.read_excel(path, dtype=str))
        df = format_dates(df, ["تاريخ"])
        for c in ["قيمة التحويلة", "المصاريف الادارية"]:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
        start_thread(process_clear_and_upload, ("قيد_اللجنة_7", df.to_dict(orient='records'), "رقم البطاقة"))


def up_meza():
    path = filedialog.askopenfilename(title="بطاقات ميزة")
    if path:
        df = clean_df(pd.read_excel(path, dtype=str))
        start_thread(process_clear_and_upload, ("meza_cards", df.to_dict(orient='records'), "رقم الموظف"))


def up_bank():
    path = filedialog.askopenfilename(title="لجان اليوم")
    if path:
        df = clean_df(pd.read_excel(path, dtype=str))
        for c in ["المبلغ", "قيمة القرض", "المصاريف الادارية"]:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
        start_thread(process_smart_insert, ("bank_loans_data", df.to_dict(orient='records')))


# ============================================================
# ✅ جديد: رفع أرشيف اللجان القديمة (شهريًا، بدون مسح)
# ============================================================
def up_old_committees():
    path = filedialog.askopenfilename(
        title="اختر ملف اللجان القديمة (Excel)",
        filetypes=[("Excel files", "*.xlsx *.xls")]
    )
    if not path:
        return

    month_label = simpledialog.askstring(
        "اسم الشهر / الدفعة",
        "اكتب اسم هذه الدفعة من اللجان (مثال: يناير 2026):"
    )
    if not month_label or not month_label.strip():
        messagebox.showwarning("تنبيه", "لم يتم إدخال اسم الشهر. تم إلغاء عملية الرفع.")
        return
    month_label = month_label.strip()

    try:
        df = clean_df(pd.read_excel(path, dtype=str))
    except Exception as e:
        messagebox.showerror("خطأ", f"تعذر قراءة ملف الإكسيل:\n{str(e)}")
        return

    if df.empty:
        messagebox.showwarning("تنبيه", "الملف المختار لا يحتوي على أي بيانات.")
        return

    # إضافة عمود الشهر لكل سجل عشان نعرف كل دفعة جاية منين
    df["الشهر"] = month_label

    confirm = messagebox.askyesno(
        "تأكيد الرفع",
        f"سيتم رفع {len(df)} سجل تحت اسم '{month_label}' إلى أرشيف اللجان القديمة.\n\n"
        f"ملاحظة: هذا الرفع لا يمسح أي بيانات سابقة - البيانات تتراكم شهريًا.\n\n"
        f"هل تريد المتابعة؟"
    )
    if not confirm:
        return

    start_thread(process_append_upload, (OLD_COMMITTEES_TABLE, df.to_dict(orient='records')))


def do_export():
    v = view_combo.get()
    if v and not v.startswith("-"):
        start_thread(process_export_view, (v,))


# ============================================================
# --- بناء الواجهة ---
# ============================================================
root = tk.Tk()
root.title("نظام كاريitas - إدارة البيانات الموحدة")
root.geometry("650x1500")
root.configure(bg="#f8f9fa")

btn_opt = {"font": ("Arial", 10, "bold"), "width": 55, "height": 2, "fg": "white"}

tk.Label(root, text="نظام كاريitas - إدارة البيانات الموحدة",
         font=("Arial", 16, "bold"), bg="#f8f9fa", fg="#2c3e50", pady=15).pack()

# ─── رفع البيانات ───
tk.Label(root, text="⬆️ رفع وتحديث الجداول (Excel -> DB)",
         font=("Arial", 13, "bold"), bg="#f8f9fa", fg="#27ae60", pady=10).pack()

tk.Button(root, text="📊 تحديث جدول القروض (loans)",
          command=up_loans, bg="#27ae60", **btn_opt).pack(pady=5)
tk.Button(root, text="📋 تحديث جدول التقييمات (assessments)",
          command=up_assessments, bg="#2980b9", **btn_opt).pack(pady=5)
tk.Button(root, text="💰 تحديث قيد اللجنة 7 المحول",
          command=up_c7, bg="#8e44ad", **btn_opt).pack(pady=5)
tk.Button(root, text="💳 تحديث بطاقات ميزة (Meza)",
          command=up_meza, bg="#2c3e50", **btn_opt).pack(pady=5)
tk.Button(root, text="🏦 رفع لجان اليوم (إضافة ذكية)",
          command=up_bank, bg="#d35400", **btn_opt).pack(pady=5)

tk.Label(root, text="─" * 65, bg="#f8f9fa", fg="#bdc3c7").pack(pady=15)

# ─── ✅ أرشيف اللجان القديمة ───
tk.Label(root, text="🗄️ أرشيف اللجان القديمة (شهري - يتراكم ولا يُمسح)",
         font=("Arial", 13, "bold"), bg="#f8f9fa", fg="#16a085", pady=5).pack()
tk.Button(root, text="🗄️ رفع لجان قديمة (هيطلب منك اسم الشهر)",
          command=up_old_committees, bg="#16a085", **btn_opt).pack(pady=5)
tk.Label(root,
         text="كل شهر بتعمل ملف إكسيل وترفعه هنا، وهنسألك تكتب اسم الشهر (مثال: يناير 2026)\nعشان تقدر بعدين تشوف كل اللجان القديمة الخاصة بأي عميل مرتبة",
         font=("Arial", 9), bg="#f8f9fa", fg="#16a085", wraplength=600, justify="center").pack()

tk.Label(root, text="─" * 65, bg="#f8f9fa", fg="#bdc3c7").pack(pady=15)

# ─── مسح البيانات ───
tk.Label(root, text="🗑️ مسح البيانات من الجداول",
         font=("Arial", 13, "bold"), bg="#f8f9fa", fg="#c0392b").pack(pady=10)
tk.Button(root, text="⚠️ مسح جميع البيانات (بكلمة مرور) - ما عدا جدول المستخدمين",
          command=clear_all_tables,
          bg="#c0392b", fg="white", font=("Arial", 10, "bold"), width=55, height=2).pack(pady=5)
tk.Label(root,
         text="سيتم مسح: assessments, bank_loans_data, loans, meza_cards, operations, قيد_اللجنة_7",
         font=("Arial", 9), bg="#f8f9fa", fg="#e74c3c", wraplength=600).pack()
tk.Label(root, text="✅ جدول users وأرشيف اللجان القديمة لن يتم مسحهما",
         font=("Arial", 9, "bold"), bg="#f8f9fa", fg="#27ae60").pack()

tk.Label(root, text="─" * 65, bg="#f8f9fa", fg="#bdc3c7").pack(pady=15)

# ─── تصدير كامل ───
tk.Label(root, text="📥 تصدير البيانات من قاعدة البيانات",
         font=("Arial", 13, "bold"), bg="#f8f9fa", fg="#2980b9").pack(pady=10)

btn_export_frame = tk.Frame(root, bg="#f8f9fa")
btn_export_frame.pack(pady=10)

tk.Button(btn_export_frame,
          text="📊 تصدير الكل كملف Excel (بيانات الجداول والفيوز)",
          command=lambda: start_export_thread(export_all_data_to_excel_with_views),
          bg="#27ae60", fg="white", font=("Arial", 10, "bold"), height=2, width=50).pack(pady=8)

tk.Button(btn_export_frame,
          text="💾 تصدير SQL (إنشاء الجداول والفيوز مع البيانات)",
          command=lambda: start_export_thread(export_to_sql_with_views),
          bg="#34495e", fg="white", font=("Arial", 10, "bold"), height=2, width=50).pack(pady=8)

status_label = tk.Label(root, text="✅ النظام جاهز للعمل",
                         font=("Arial", 10), bg="#f8f9fa", fg="#7f8c8d")
status_label.pack(pady=15)

tk.Label(root, text="─" * 65, bg="#f8f9fa", fg="#bdc3c7").pack(pady=15)

# ─── استخراج تقرير واحد ───
tk.Label(root, text="⬇️ استخراج تقرير واحد (DB -> Excel)",
         font=("Arial", 13, "bold"), bg="#f8f9fa", fg="#8e44ad").pack(pady=10)

report_frame = tk.Frame(root, bg="#f8f9fa")
report_frame.pack(pady=8, padx=20)

tk.Button(report_frame,
          text="📥 تنزيل Excel",
          command=do_export,
          bg="#16a085", fg="white",
          font=("Arial", 10, "bold"),
          width=14, height=2).pack(side="right", padx=(8, 0))

view_combo = ttk.Combobox(report_frame, font=("Arial", 11), width=40, state="readonly")
view_combo['values'] = [
    "summary_bank_export_view",
    "bank_export_view",
    "operations_with_details",
    "البيانات كاملة المومرفوعة للتنفيز",
    "client_full_profile",
    "بيانات_عمليات_الرفع_الكاملة",
    VIEW_NAME_LAGNA
] + list(TABLES_AND_VIEWS["Tables"].keys())
view_combo.set("--- اختر التقرير أو الجدول ---")
view_combo.pack(side="right", ipady=4)

tk.Label(root,
         text="نشكركم على تعاونكم | إدارة النظم | نسخة محسنة 2025",
         font=("Arial", 9, "italic"), bg="#f8f9fa", fg="#95a5a6").pack(side="bottom", pady=20)

root.mainloop()
