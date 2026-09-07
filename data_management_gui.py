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

# ✅ جدول تقارير الزيارات (يُمسح مع باقي الجداول التشغيلية)
VISIT_REPORTS_TABLE = "visit_reports"

# --- تعريف الجداول والـ Views ---
# ✅ 2026-09: تمت إضافة الجداول الجديدة (branches, projects, project_accounting_directives,
#    edit_requests, kyc_reports) بعد مطابقتها مع القاعدة الحقيقية
TABLES_AND_VIEWS = {
    "Tables": {
        "assessments": "جدول التقييمات",
        "bank_loans_data": "جدول بيانات قروض البنك",
        "loans": "جدول القروض",
        "meza_cards": "جدول بطاقات ميزة",
        "operations": "جدول العمليات",
        "users": "جدول المستخدمين",
        "قيد_اللجنة_7": "جدول قيد اللجنة 7",
        OLD_COMMITTEES_TABLE: "جدول أرشيف اللجان القديمة",
        VISIT_REPORTS_TABLE: "جدول تقارير الزيارات",
        "branches": "جدول الفروع",
        "projects": "جدول المشاريع",
        "project_accounting_directives": "جدول التوجيهات المحاسبية للمشاريع",
        "edit_requests": "جدول طلبات التعديل",
        "kyc_reports": "جدول تقارير اعرف عميلك (KYC)"
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
# ✅ 2026-09: التعريفات دي اتسحبت مباشرة من قاعدة البيانات الحقيقية (pg_get_viewdef)
#    بعد ما اتأكدنا إن النسخة القديمة هنا كانت قديمة جدًا ومختلفة عن الواقع
VIEW_DEFINITIONS = {
    "bank_export_view": """
CREATE OR REPLACE VIEW bank_export_view AS
SELECT NULL::text AS "كود الفرع",
    NULL::text AS "رقم الحساب",
    a1."الاسم" AS "أسم العميل",
    o."المبلغ المطلوب" AS "المبلغ",
    o."رقم البطاقة العميل" AS "رقم الموظف",
    '5078'::text AS "كود البنك (ثابت)",
    o."الفرع",
    o."رقم اللجنة",
    m."رقم الحساب/البطاقه"
FROM operations_with_details o
LEFT JOIN assessments a1 ON o."رقم البطاقة العميل" = a1."رقم_البطاقة"
LEFT JOIN meza_cards m ON o."رقم البطاقة العميل" = m."رقم الموظف"::text
""",
    "client_full_profile": """
CREATE OR REPLACE VIEW client_full_profile AS
SELECT l."الرقم القومى",
    l."مسلسل القرض",
    l."اسم العميل عربى",
    l."نظام القرض",
    l."مبلغ القرض",
    l."عدد الاقساط",
    l."حالة القرض",
    l."تاريخ القرض",
    l."المبلغ المدفوع",
    l."اخصائى القرض",
    l."ملاحظات",
    l."كود العميل",
    l."برنامج الاقراض",
    l."النشاط الثانى",
    l."النشاط الثالث",
    l."المنطقة",
    l."الفرع الحالى للعميل",
    l."الاخصائى",
    l."الباقى من القسط",
    l."المصاريف الادارية للقرض",
    l."تاريخ الميلاد",
    a."رقم_البطاقة",
    a."الاسم",
    a."تاريخ التقرير",
    a."رقم الشيت + الصفحة",
    a."نتيجة التقييم",
    a."سبب 2",
    a."السم المرسل من الاى سكور",
    a."رقم الحساب",
    a.aa,
    a."التقييم الرقمى",
    a."احداثيات الموقع"
FROM loans l
FULL JOIN assessments a ON l."الرقم القومى" = a."رقم_البطاقة"
""",
    "operations_with_details": """
CREATE OR REPLACE VIEW operations_with_details AS
SELECT o.id,
    o."رقم البطاقة العميل",
    o."رقم بطاقة الضامن",
    o."عدد ايام التاخير",
    o."المشروع",
    o."المبلغ المطلوب",
    o."عدد الاقساط",
    o."اسم الاخصائى",
    o."المنطقه",
    o."الفرع",
    o."رقم اللجنة",
    o."القائم بالزياره",
    o."اسم القائم بالادخال",
    o."المراجعة الداخلية",
    o."ملاحظات المراجعة الداخلية",
    o."مسؤول المتابعة",
    o."تعليق مسؤول المتابعة",
    o."الادارة",
    o."ملاحظات الادارة",
    o."تم التحويل",
    o.created_at,
    o.created_by,
    l."اسم العميل عربى" AS "اسم_العميل",
    l."تاريخ القرض" AS "تاريخ_القرض",
    l."اخصائى القرض" AS "اخصائى_القرض",
    l."كود العميل" AS "كود_العميل",
    l."النشاط الثانى" AS "النشاط_الثانى",
    l."الفرع الحالى للعميل" AS "فرع_العميل_من_القروض",
    a1."الاسم" AS "اسم_العميل_من_التقييم",
    a1."السم المرسل من الاى سكور" AS "الاسم_من_الاي_سكور",
    a1."نتيجة التقييم" AS "نتيجة_التقييم",
    a1."التقييم الرقمى" AS "التقييم_الرقمى",
    a1."احداثيات الموقع",
    a1."تاريخ التقرير" AS "تاريخ_استعلام_العميل",
    a1."رقم الحساب" AS "رقم_الحساب_من_التقييم",
    a1."سبب 2" AS "تعليق_استعلام_العميل",
    a2."الاسم" AS "اسم_الضامن",
    a2."السم المرسل من الاى سكور" AS "اسم_الضامن_من_الاي_سكور",
    a2."نتيجة التقييم" AS "نتيجة_تقييم_الضامن",
    a2."التقييم الرقمى" AS "تقييم_رقمى_الضامن",
    a2."تاريخ التقرير" AS "تاريخ_استعلام_الضامن",
    a2."سبب 2" AS "تعليق_استعلام_الضامن",
    bld."اسم العميل" AS "اسم_العميل_من_بيانات_القروض",
    COALESCE(bld."المبلغ", 0::numeric) AS "المبلغ_البنكي",
    COALESCE(bld."قيمة القرض", 0::numeric) AS "قيمة_القرض_البنكي",
    bld."اسم المشروع" AS "اسم_المشروع_البنكي",
    COALESCE(bld."المصاريف الادارية", 0::numeric) AS "المصاريف_الادارية_البنكية",
    o."موافقة مسئول المشروع",
    o."ملاحظات مسئول المشروع"
FROM operations o
LEFT JOIN loans l ON o."رقم البطاقة العميل" = l."الرقم القومى"
LEFT JOIN assessments a1 ON o."رقم البطاقة العميل" = a1."رقم_البطاقة"
LEFT JOIN assessments a2 ON o."رقم بطاقة الضامن" = a2."رقم_البطاقة"
LEFT JOIN bank_loans_data bld ON o."رقم البطاقة العميل" = bld."رقم البطاقة"
""",
    "summary_bank_export_view": """
CREATE OR REPLACE VIEW summary_bank_export_view AS
SELECT o."الفرع" AS "فرع_العملية_الأصلية",
    count(bld."رقم البطاقة") AS "إجمالي_عدد_الحالات",
    sum(bld."قيمة القرض") AS "إجمالي_المبالغ_المرفوعة",
    sum(CASE WHEN o."تم التحويل" = true THEN 1 ELSE 0 END) AS "عدد_تم_التحويل",
    sum(CASE WHEN o."تم التحويل" = true THEN bld."قيمة القرض" ELSE 0::numeric END) AS "قيمة_ما_تم_تحويله",
    sum(CASE WHEN o."تم التحويل" = false OR o."تم التحويل" IS NULL THEN 1 ELSE 0 END) AS "عدد_المتبقي",
    sum(CASE WHEN o."تم التحويل" = false OR o."تم التحويل" IS NULL THEN bld."قيمة القرض" ELSE 0::numeric END) AS "قيمة_المتبقي"
FROM bank_loans_data bld
JOIN operations_with_details o ON bld."رقم البطاقة" = o."رقم البطاقة العميل"
GROUP BY o."الفرع"
""",
    "البيانات كاملة المومرفوعة للتنفيز": """
CREATE OR REPLACE VIEW "البيانات كاملة المومرفوعة للتنفيز" AS
SELECT bld."رقم البطاقة",
    bld."كود الفرع" AS "كود_فرع_الرفع_البنكي",
    bld."رقم الحساب" AS "رقم_الحساب_البنكي",
    bld."اسم العميل" AS "اسم_العميل_البنكي",
    bld."المبلغ" AS "المبلغ_المرفوع_البنكي",
    bld."كود البنك ثابت",
    bld."قيمة القرض" AS "قيمة_القرض_المرفوعة_البنكية",
    bld."اسم المشروع" AS "اسم_المشروع_المرفوع_البنكي",
    bld."المصاريف الادارية" AS "المصاريف_الإدارية_المرفوعة",
    o."رقم بطاقة الضامن",
    o."المشروع" AS "مشروع_العملية_التشغيلية",
    o."المبلغ المطلوب" AS "المبلغ_المطلوب_في_العملية_الأصلية",
    o."عدد الاقساط",
    o."اسم الاخصائى",
    o."المنطقه",
    o."الفرع" AS "فرع_العملية_الأصلية",
    o."رقم اللجنة",
    o."المراجعة الداخلية",
    o."ملاحظات المراجعة الداخلية",
    o."مسؤول المتابعة",
    o."تعليق مسؤول المتابعة",
    o."الادارة",
    o."ملاحظات الادارة",
    o."تم التحويل",
    o.created_at AS "تاريخ_إنشاء_العملية",
    o.created_by AS "منشئ_العملية",
    o."اخصائى_القرض",
    o."كود_العميل",
    o."النشاط_الثانى",
    o."فرع_العميل_من_القروض",
    o."اسم_العميل_من_التقييم",
    o."الاسم_من_الاي_سكور",
    o."نتيجة_التقييم",
    o."التقييم_الرقمى",
    o."احداثيات الموقع",
    o."تاريخ_استعلام_العميل",
    o."تعليق_استعلام_العميل",
    o."اسم_الضامن",
    o."اسم_الضامن_من_الاي_سكور",
    o."نتيجة_تقييم_الضامن",
    o."تقييم_رقمى_الضامن",
    o."تاريخ_استعلام_الضامن",
    o."تعليق_استعلام_الضامن"
FROM bank_loans_data bld
JOIN operations_with_details o ON bld."رقم البطاقة" = o."رقم البطاقة العميل"
""",
    "بيانات_عمليات_الرفع_الكاملة": """
CREATE OR REPLACE VIEW "بيانات_عمليات_الرفع_الكاملة" AS
SELECT "رقم البطاقة العميل",
    "رقم بطاقة الضامن",
    "عدد ايام التاخير",
    "المشروع",
    "المبلغ المطلوب",
    "عدد الاقساط",
    "اسم الاخصائى",
    "المنطقه",
    "رقم اللجنة",
    TRIM(LEADING 'فرع ' FROM "الفرع") AS "الفرع",
    "القائم بالزياره",
    "اسم القائم بالادخال"
FROM operations
""",
    VIEW_NAME_LAGNA: """
CREATE OR REPLACE VIEW "بيانات اللجنة المعلقة (لم يتم تحوي" AS
SELECT bld."رقم الحساب" AS "رقم_الحساب",
    bld."كود البنك ثابت" AS "كود_البنك_ثابت",
    bld."رقم الحساب" AS "رقم_الحساب_مكرر",
    bld."اسم العميل" AS "اسم_العميل",
    bld."المبلغ" AS "المبلغ_المرفوع",
    bld."رقم البطاقة" AS "رقم_البطاقة",
    bld."قيمة القرض" AS "قيمة_القرض",
    bld."المصاريف الادارية" AS "المصاريف_الادارية",
    bld."قيمة القرض" - bld."المصاريف الادارية" AS "القيمة_النهائية",
    bld."المبلغ" - o."المبلغ المطلوب" AS "الفرق_بين_المبلغين",
    o."المبلغ المطلوب" AS "المبلغ_المطلوب_الأصلي",
    o."ملاحظات الادارة" AS "ملاحظات_الادارة",
    o."احداثيات الموقع" AS "احداثيات_الموقع",
    o."مسؤول المتابعة" AS "مسؤول_المتابعة",
    o."تعليق مسؤول المتابعة" AS "تعليق_مسؤول_المتابعة",
    o."المراجعة الداخلية" AS "المراجعة_الداخلية",
    o."ملاحظات المراجعة الداخلية" AS "ملاحظات_المراجعة_الداخلية",
    o."رقم اللجنة" AS "رقم_اللجنة_المعين",
    o."تم التحويل" AS "حالة_التحويل",
    o."اسم_العميل_من_التقييم" AS "اسم_التقييم",
    o."تاريخ_استعلام_العميل" AS "تاريخ_التقرير",
    o."رقم_الحساب_من_التقييم" AS "رقم_حساب_التقييم",
    o."نتيجة_التقييم",
    o."تعليق_استعلام_العميل" AS "سبب_التقييم_2",
    o."الاسم_من_الاي_سكور" AS "الاسم_المرسل_من_الآي_سكور",
    o."التقييم_الرقمى" AS "التقييم_الرقمى_للعميل",
    CURRENT_DATE - o."تاريخ_استعلام_العميل" AS "فرق_تاريخ_الاستعلام_عميل",
    CASE WHEN (CURRENT_DATE - o."تاريخ_استعلام_العميل") > 28 THEN '⚠️ منتهي (أكثر من 28 يوم)' ELSE '✅ صالح' END AS "حالة_تاريخ_العميل",
    o."اسم_الضامن",
    o."اسم_الضامن_من_الاي_سكور" AS "اسم_الضامن_اي_سكور",
    o."نتيجة_تقييم_الضامن",
    o."تقييم_رقمى_الضامن",
    o."تاريخ_استعلام_الضامن",
    o."تعليق_استعلام_الضامن",
    CURRENT_DATE - o."تاريخ_استعلام_الضامن" AS "فرق_تاريخ_الاستعلام_ضامن",
    CASE WHEN (CURRENT_DATE - o."تاريخ_استعلام_الضامن") > 50 THEN '⚠️ منتهي (أكثر من 50 يوم)' ELSE '✅ صالح' END AS "حالة_تاريخ_الضامن"
FROM bank_loans_data bld
JOIN operations_with_details o ON bld."رقم البطاقة" = o."رقم البطاقة العميل"
WHERE o."رقم اللجنة" IS NOT NULL AND o."تم التحويل" IS FALSE
"""
}

# --- الجداول اللي بتتحدد بشكل افتراضي (Pre-checked) في شاشة اختيار المسح ---
# ملاحظة: users و اللجان_القديمة (أرشيف) محميين دايمًا ومش بيظهروا في الاختيار خالص
DEFAULT_CHECKED_FOR_CLEAR = [
    "assessments",
    "bank_loans_data",
    "loans",
    "meza_cards",
    "operations",
    "قيد_اللجنة_7",
    VISIT_REPORTS_TABLE
]

# الجداول اللي ممنوع تتمسح خالص ومش بتظهر في شاشة الاختيار
PROTECTED_TABLES = {"users", OLD_COMMITTEES_TABLE}


def get_current_month_name():
    months_ar = {
        1: "يناير", 2: "فبراير", 3: "مارس", 4: "أبريل",
        5: "مايو", 6: "يونيو", 7: "يوليو", 8: "أغسطس",
        9: "سبتمبر", 10: "أكتوبر", 11: "نوفمبر", 12: "ديسمبر"
    }
    return months_ar[datetime.now().month]


# ============================================================
# ✅ مسح البيانات - شاشة اختيار بالـ Checkbox بدل القائمة الثابتة
# ============================================================
def clear_all_tables():
    selectable_tables = [t for t in TABLES_AND_VIEWS["Tables"].keys() if t not in PROTECTED_TABLES]

    win = tk.Toplevel(root)
    win.title("اختيار الجداول اللي هتتمسح")
    win.geometry("440x560")
    win.grab_set()

    tk.Label(win, text="⚠️ اختاري الجداول اللي عايزة تمسحيها:",
             font=("Arial", 11, "bold"), fg="#c0392b").pack(pady=(12, 2))
    tk.Label(win, text="(جدول users وأرشيف اللجان_القديمة محميين دايمًا ومش هيظهروا هنا)",
             font=("Arial", 8), fg="#7f8c8d", wraplength=400, justify="center").pack(pady=(0, 8))

    # منطقة قابلة للتمرير للـ Checkboxes
    outer = tk.Frame(win)
    outer.pack(fill="both", expand=True, padx=15)
    canvas_cb = tk.Canvas(outer, highlightthickness=0)
    scroll_cb = ttk.Scrollbar(outer, orient="vertical", command=canvas_cb.yview)
    check_frame = tk.Frame(canvas_cb)
    check_frame.bind("<Configure>", lambda e: canvas_cb.configure(scrollregion=canvas_cb.bbox("all")))
    canvas_cb.create_window((0, 0), window=check_frame, anchor="nw")
    canvas_cb.configure(yscrollcommand=scroll_cb.set)
    canvas_cb.pack(side="left", fill="both", expand=True)
    scroll_cb.pack(side="right", fill="y")

    vars_map = {}
    for t in selectable_tables:
        var = tk.BooleanVar(value=(t in DEFAULT_CHECKED_FOR_CLEAR))
        desc = TABLES_AND_VIEWS["Tables"].get(t, t)
        cb = tk.Checkbutton(check_frame, text=f"{t}   ({desc})", variable=var, anchor="w", justify="left")
        cb.pack(fill="x", anchor="w", pady=2)
        vars_map[t] = var

    # أزرار تحديد الكل / إلغاء التحديد
    btns_frame = tk.Frame(win)
    btns_frame.pack(fill="x", pady=8, padx=15)

    def select_all():
        for v in vars_map.values():
            v.set(True)

    def deselect_all():
        for v in vars_map.values():
            v.set(False)

    tk.Button(btns_frame, text="✅ تحديد الكل", command=select_all,
              bg="#27ae60", fg="white", font=("Arial", 9, "bold")).pack(side="left", expand=True, fill="x", padx=2)
    tk.Button(btns_frame, text="❌ إلغاء تحديد الكل", command=deselect_all,
              bg="#7f8c8d", fg="white", font=("Arial", 9, "bold")).pack(side="left", expand=True, fill="x", padx=2)

    def proceed():
        chosen = [t for t, v in vars_map.items() if v.get()]
        if not chosen:
            messagebox.showwarning("تنبيه", "لازم تختاري جدول واحد على الأقل.")
            return
        win.destroy()
        confirm_and_clear(chosen)

    tk.Button(win, text="متابعة →", command=proceed,
              bg="#2980b9", fg="white", font=("Arial", 10, "bold")).pack(pady=10, fill="x", padx=15)


def confirm_and_clear(chosen_tables):
    password = simpledialog.askstring(
        "تأكيد مسح البيانات",
        "⚠️ تحذير: هيتم مسح البيانات من الجداول دي:\n\n" +
        "\n".join(f"- {t}" for t in chosen_tables) +
        "\n\nأدخل كلمة المرور للمتابعة (123):",
        show='*'
    )
    if password != "123":
        messagebox.showerror("خطأ", "❌ كلمة المرور غير صحيحة!\nتم إلغاء عملية المسح.")
        return

    confirm = messagebox.askyesno(
        "تأكيد نهائي",
        f"⚠️ تحذير نهائي: أنت على وشك مسح جميع البيانات من {len(chosen_tables)} جدول!\n\n"
        "هذا الإجراء لا يمكن التراجع عنه.\n\nهل أنت متأكد 100%؟"
    )
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
            for table_name in chosen_tables:
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


# ✅ رفع بدون مسح - يُستخدم لأرشيف اللجان القديمة لأنه يتراكم شهر بعد شهر
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
# رفع أرشيف اللجان القديمة (شهريًا، بدون مسح)
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
# --- بناء الواجهة (مُعاد تنظيمها في أعمدة جنب بعض + Scroll) ---
# ============================================================
root = tk.Tk()
root.title("نظام كاريitas - إدارة البيانات الموحدة")
root.geometry("1300x820")
root.minsize(1000, 600)
root.configure(bg="#f8f9fa")

# --- عنوان علوي ثابت ---
tk.Label(root, text="نظام كاريitas - إدارة البيانات الموحدة",
         font=("Arial", 16, "bold"), bg="#f8f9fa", fg="#2c3e50", pady=12).pack(fill="x")

# --- منطقة قابلة للتمرير (Scroll) كحماية إضافية على أي شاشة ---
outer_frame = tk.Frame(root, bg="#f8f9fa")
outer_frame.pack(fill="both", expand=True)

canvas = tk.Canvas(outer_frame, bg="#f8f9fa", highlightthickness=0)
v_scroll = ttk.Scrollbar(outer_frame, orient="vertical", command=canvas.yview)
h_scroll = ttk.Scrollbar(outer_frame, orient="horizontal", command=canvas.xview)
canvas.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

v_scroll.pack(side="right", fill="y")
h_scroll.pack(side="bottom", fill="x")
canvas.pack(side="left", fill="both", expand=True)

content = tk.Frame(canvas, bg="#f8f9fa")
content_id = canvas.create_window((0, 0), window=content, anchor="nw")


def _on_content_configure(event):
    canvas.configure(scrollregion=canvas.bbox("all"))


def _on_canvas_configure(event):
    canvas.itemconfig(content_id, width=event.width)


content.bind("<Configure>", _on_content_configure)
canvas.bind("<Configure>", _on_canvas_configure)


def _on_mousewheel(event):
    canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


canvas.bind_all("<MouseWheel>", _on_mousewheel)

# --- إطار الأعمدة: عمودين جنب بعض ---
columns_frame = tk.Frame(content, bg="#f8f9fa")
columns_frame.pack(fill="both", expand=True, padx=15, pady=10)
columns_frame.grid_columnconfigure(0, weight=1, uniform="col")
columns_frame.grid_columnconfigure(1, weight=1, uniform="col")

left_col = tk.Frame(columns_frame, bg="#f8f9fa")
left_col.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

right_col = tk.Frame(columns_frame, bg="#f8f9fa")
right_col.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

btn_opt = {"font": ("Arial", 10, "bold"), "fg": "white"}


def make_section(parent, title, color):
    """يبني LabelFrame منظم لكل قسم بدل التكديس الطولي المفتوح"""
    section = tk.LabelFrame(parent, text=title, font=("Arial", 12, "bold"),
                             bg="#f8f9fa", fg=color, labelanchor="n",
                             bd=2, relief="groove", padx=10, pady=10)
    section.pack(fill="x", pady=(0, 15))
    return section


# ══════════════════ العمود الأيسر ══════════════════

# ─── قسم: رفع وتحديث الجداول ───
sec_upload = make_section(left_col, "⬆️ رفع وتحديث الجداول (Excel -> DB)", "#27ae60")

tk.Button(sec_upload, text="📊 تحديث جدول القروض (loans)",
          command=up_loans, bg="#27ae60", **btn_opt).pack(fill="x", pady=4)
tk.Button(sec_upload, text="📋 تحديث جدول التقييمات (assessments)",
          command=up_assessments, bg="#2980b9", **btn_opt).pack(fill="x", pady=4)
tk.Button(sec_upload, text="💰 تحديث قيد اللجنة 7 المحول",
          command=up_c7, bg="#8e44ad", **btn_opt).pack(fill="x", pady=4)
tk.Button(sec_upload, text="💳 تحديث بطاقات ميزة (Meza)",
          command=up_meza, bg="#2c3e50", **btn_opt).pack(fill="x", pady=4)
tk.Button(sec_upload, text="🏦 رفع لجان اليوم (إضافة ذكية)",
          command=up_bank, bg="#d35400", **btn_opt).pack(fill="x", pady=4)

# ─── قسم: أرشيف اللجان القديمة ───
sec_archive = make_section(left_col, "🗄️ أرشيف اللجان القديمة (شهري - يتراكم ولا يُمسح)", "#16a085")

tk.Button(sec_archive, text="🗄️ رفع لجان قديمة (هيطلب منك اسم الشهر)",
          command=up_old_committees, bg="#16a085", **btn_opt).pack(fill="x", pady=4)
tk.Label(sec_archive,
         text="كل شهر بتعمل ملف إكسيل وترفعه هنا، وهنسألك تكتب اسم الشهر (مثال: يناير 2026)\n"
              "عشان تقدر بعدين تشوف كل اللجان القديمة الخاصة بأي عميل مرتبة",
         font=("Arial", 9), bg="#f8f9fa", fg="#16a085", wraplength=450, justify="center").pack(pady=(6, 0))

# ══════════════════ العمود الأيمن ══════════════════

# ─── قسم: مسح البيانات ───
sec_clear = make_section(right_col, "🗑️ مسح البيانات من الجداول", "#c0392b")

tk.Button(sec_clear, text="⚠️ مسح بيانات (اختاري الجداول بنفسك)",
          command=clear_all_tables,
          bg="#c0392b", fg="white", font=("Arial", 10, "bold")).pack(fill="x", pady=4)
tk.Label(sec_clear,
         text="هيفتحلك شاشة فيها كل الجداول بـ Checkbox، تقدري تحددي أو تلغي التحديد لأي جدول،\n"
              "أو تستخدمي زرار \"تحديد الكل\" وبعدين تشيلي اللي مش عايزاه.",
         font=("Arial", 9), bg="#f8f9fa", fg="#e74c3c", wraplength=450, justify="center").pack(pady=(6, 0))
tk.Label(sec_clear, text="✅ جدول users وأرشيف اللجان القديمة محميين ومش بيظهروا في الاختيار",
         font=("Arial", 9, "bold"), bg="#f8f9fa", fg="#27ae60").pack()

# ─── قسم: تصدير كامل ───
sec_export = make_section(right_col, "📥 تصدير البيانات من قاعدة البيانات", "#2980b9")

tk.Button(sec_export, text="📊 تصدير الكل كملف Excel (بيانات الجداول والفيوز)",
          command=lambda: start_export_thread(export_all_data_to_excel_with_views),
          bg="#27ae60", fg="white", font=("Arial", 10, "bold")).pack(fill="x", pady=4)
tk.Button(sec_export, text="💾 تصدير SQL (إنشاء الجداول والفيوز مع البيانات)",
          command=lambda: start_export_thread(export_to_sql_with_views),
          bg="#34495e", fg="white", font=("Arial", 10, "bold")).pack(fill="x", pady=4)

status_label = tk.Label(sec_export, text="✅ النظام جاهز للعمل",
                         font=("Arial", 10), bg="#f8f9fa", fg="#7f8c8d")
status_label.pack(pady=(8, 0))

# ─── قسم: استخراج تقرير واحد ───
sec_report = make_section(right_col, "⬇️ استخراج تقرير واحد (DB -> Excel)", "#8e44ad")

report_row = tk.Frame(sec_report, bg="#f8f9fa")
report_row.pack(fill="x")

view_combo = ttk.Combobox(report_row, font=("Arial", 11), state="readonly")
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
view_combo.pack(side="left", fill="x", expand=True, ipady=4)

tk.Button(report_row, text="📥 تنزيل Excel",
          command=do_export,
          bg="#16a085", fg="white",
          font=("Arial", 10, "bold")).pack(side="right", padx=(8, 0))

# --- تذييل ثابت ---
tk.Label(root, text="مساعد رفع الملفات و تنزيل ( Excel ) | إدارة النظم | نسخة محسنة 2026",
         font=("Arial", 9, "italic"), bg="#f8f9fa", fg="#95a5a6").pack(side="bottom", pady=10)

root.mainloop()
