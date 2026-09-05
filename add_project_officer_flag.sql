ALTER TABLE public.users
  ADD COLUMN IF NOT EXISTS is_project_officer boolean NOT NULL DEFAULT false;

UPDATE public.users
SET is_project_officer = true
WHERE id IN ('bobnal', 'ingy', 'malak-shalaby', 'medomedo', 'moheb', 'sameh', 'shrshr');
