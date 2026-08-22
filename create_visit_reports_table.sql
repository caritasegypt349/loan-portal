CREATE TABLE IF NOT EXISTS public.visit_reports (
  id bigserial PRIMARY KEY,
  operation_id bigint,
  code text,
  name text,
  branch text,
  national_id text,
  phone text,
  visit_date date,
  visitor_name text,
  activity text,
  case_type text,
  specialist_name text,
  status text,
  specialist_reaction text,
  visit_notes text,
  guarantor_name text,
  guarantor_national_id text,
  financing_amount numeric,
  rejection_reason text,
  created_by text,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_visit_reports_national_id ON public.visit_reports (national_id);
CREATE INDEX IF NOT EXISTS idx_visit_reports_status ON public.visit_reports (status);
CREATE INDEX IF NOT EXISTS idx_visit_reports_visit_date ON public.visit_reports (visit_date);

ALTER TABLE public.visit_reports ENABLE ROW LEVEL SECURITY;

CREATE POLICY "السماح بالوصول لتقارير الزيارة" ON public.visit_reports
FOR ALL USING (true) WITH CHECK (true);
