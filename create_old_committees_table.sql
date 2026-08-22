CREATE TABLE IF NOT EXISTS public."اللجان_القديمة" (
  id bigserial PRIMARY KEY,
  "الشهر" text NOT NULL,
  "م" text,
  "رقم بطاقة العميل" text,
  "كود العميل" text,
  "اسم العميل" text,
  "رقم الحساب" text,
  "الإحداثيات" text,
  "الاسم من I-Score" text,
  "المشروع" text,
  "رقم بطاقة الضامن" text,
  "اسم الضامن" text,
  "المبلغ المطلوب" text,
  "المبلغ المحول" text,
  "قيمة التمويل" text,
  "نظام التمويل" text,
  "المصاريف الإدارية" text,
  "الأخصائي" text,
  "تم التحويل" text,
  "المراجعة الداخلية" text,
  "ملاحظات المراجعة الداخلية" text,
  "مسؤول المتابعة" text,
  "تعليق مسؤول المتابعة" text,
  "الإدارة" text,
  "ملاحظات الإدارة" text,
  "رقم اللجنة" text,
  "عدد أيام التأخير" text,
  "عدد الأقساط" text,
  "المنطقة" text,
  "الفرع" text,
  "القائم بالزيارة" text,
  "القائم بالإدخال" text,
  "تاريخ الإدخال" text,
  "تاريخ القرض" text,
  "أخصائي القرض" text,
  "النشاط الثاني" text,
  "فرع العميل" text,
  "اسم العميل من التقييم" text,
  "نتيجة التقييم" text,
  "التقييم الرقمي" text,
  "تاريخ استعلام العميل" text,
  "تعليق استعلام العميل" text,
  "اسم الضامن من I-Score" text,
  "نتيجة تقييم الضامن" text,
  "تقييم رقمي الضامن" text,
  "تاريخ استعلام الضامن" text,
  "تعليق استعلام الضامن" text,
  uploaded_at timestamp with time zone DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_lagan_qadima_nid ON public."اللجان_القديمة" ("رقم بطاقة العميل");

CREATE INDEX IF NOT EXISTS idx_lagan_qadima_month ON public."اللجان_القديمة" ("الشهر");

ALTER TABLE public."اللجان_القديمة" ENABLE ROW LEVEL SECURITY;

CREATE POLICY "السماح بالوصول للجان القديمة" ON public."اللجان_القديمة"
FOR ALL USING (true) WITH CHECK (true);
