CREATE TABLE IF NOT EXISTS public.committees (
  id bigserial PRIMARY KEY,
  branch text NOT NULL,
  committee_date date NOT NULL,
  created_at timestamp with time zone DEFAULT now(),
  UNIQUE (branch, committee_date)
);

CREATE TABLE IF NOT EXISTS public.contracts (
  id bigserial PRIMARY KEY,
  operation_id bigint NOT NULL REFERENCES public.operations(id) ON DELETE CASCADE,
  branch text NOT NULL,
  branch_contract_number integer NOT NULL,
  contract_date date NOT NULL,
  committee_id bigint REFERENCES public.committees(id),
  project_id bigint NOT NULL REFERENCES public.projects(id),
  association_representative text,
  financing_purpose text,
  loan_amount numeric NOT NULL,
  interest_rate numeric NOT NULL,
  admin_fee_percent numeric NOT NULL,
  admin_fee_amount numeric NOT NULL,
  total_due numeric NOT NULL,
  installment_count integer NOT NULL,
  installment_amount numeric NOT NULL,
  first_installment_date date NOT NULL,
  created_by text,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  UNIQUE (branch, branch_contract_number),
  UNIQUE (operation_id)
);

CREATE TABLE IF NOT EXISTS public.contract_guarantors (
  id bigserial PRIMARY KEY,
  contract_id bigint NOT NULL REFERENCES public.contracts(id) ON DELETE CASCADE,
  guarantor_order integer NOT NULL DEFAULT 1,
  guarantor_name text NOT NULL,
  guarantor_national_id text NOT NULL,
  address text,
  phone text,
  issued_by text,
  issue_date text,
  work_address text,
  created_at timestamp with time zone DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_contracts_operation ON public.contracts (operation_id);
CREATE INDEX IF NOT EXISTS idx_contracts_branch ON public.contracts (branch);
CREATE INDEX IF NOT EXISTS idx_committees_branch_date ON public.committees (branch, committee_date);
CREATE INDEX IF NOT EXISTS idx_guarantors_contract ON public.contract_guarantors (contract_id);

ALTER TABLE public.committees ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.contracts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.contract_guarantors ENABLE ROW LEVEL SECURITY;

CREATE POLICY "السماح بالوصول للجان" ON public.committees FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "السماح بالوصول للعقود" ON public.contracts FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "السماح بالوصول لضامنين العقد" ON public.contract_guarantors FOR ALL USING (true) WITH CHECK (true);
