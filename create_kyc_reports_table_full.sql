DROP TABLE IF EXISTS public.kyc_reports;

CREATE TABLE public.kyc_reports (
  id bigserial PRIMARY KEY,
  operation_id bigint,
  code text,
  name text,
  national_id text,
  "birthDate" text,
  "issuedBy" text,
  "issueDate" text,
  date text,
  "homePhone" text,
  phone text,
  "workPhone" text,
  address text,
  area text,
  job text,
  "workAddress" text,
  activity text,
  beneficiary text,
  "beneficiaryRelation" text,
  "accountType" text,
  "otherBanks" text,
  "mainIncome" text,
  "otherIncome" text,
  purpose text,
  loan text,
  "emergencyName" text,
  "emergencyRelation" text,
  "emergencyPhone" text,
  risk text,
  gps text,
  notes text,
  "workNature" text,
  checks jsonb,
  completion_percent integer,
  created_by text,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now()
);

CREATE INDEX idx_kyc_reports_operation_id ON public.kyc_reports (operation_id);
CREATE INDEX idx_kyc_reports_national_id ON public.kyc_reports (national_id);

ALTER TABLE public.kyc_reports ENABLE ROW LEVEL SECURITY;

CREATE POLICY "السماح بالوصول لتقارير اعرف عميلك" ON public.kyc_reports
FOR ALL USING (true) WITH CHECK (true);
