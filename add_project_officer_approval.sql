ALTER TABLE public.operations
  ADD COLUMN IF NOT EXISTS "موافقة مسئول المشروع" text NOT NULL DEFAULT 'لم تتم المراجعة',
  ADD COLUMN IF NOT EXISTS "ملاحظات مسئول المشروع" text;
