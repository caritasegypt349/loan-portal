CREATE TABLE IF NOT EXISTS public.branches (
  id bigserial PRIMARY KEY,
  name text NOT NULL UNIQUE,
  created_at timestamp with time zone DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.projects (
  id bigserial PRIMARY KEY,
  name text NOT NULL,
  interest_rate numeric NOT NULL,
  admin_fee_percent numeric NOT NULL,
  is_active boolean NOT NULL DEFAULT true,
  min_amount numeric,
  max_amount numeric,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.project_accounting_directives (
  id bigserial PRIMARY KEY,
  project_id bigint NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
  branch_id bigint NOT NULL REFERENCES public.branches(id) ON DELETE CASCADE,
  accounting_code text NOT NULL,
  created_at timestamp with time zone DEFAULT now(),
  UNIQUE (project_id, branch_id)
);

CREATE INDEX IF NOT EXISTS idx_directives_project ON public.project_accounting_directives (project_id);
CREATE INDEX IF NOT EXISTS idx_directives_branch ON public.project_accounting_directives (branch_id);

ALTER TABLE public.branches ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.project_accounting_directives ENABLE ROW LEVEL SECURITY;

CREATE POLICY "السماح بالوصول للفروع" ON public.branches
FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "السماح بالوصول للمشاريع" ON public.projects
FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "السماح بالوصول للتوجيهات المحاسبية" ON public.project_accounting_directives
FOR ALL USING (true) WITH CHECK (true);
