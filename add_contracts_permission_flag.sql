ALTER TABLE public.users
  ADD COLUMN IF NOT EXISTS can_create_contracts boolean NOT NULL DEFAULT false;
