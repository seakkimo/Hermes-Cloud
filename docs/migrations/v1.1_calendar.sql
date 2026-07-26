-- V1.1 Calendar table
-- Run this in Supabase SQL Editor

create table if not exists public.calendar (
  id          bigserial primary key,
  user_id     bigint not null,
  title       text not null,
  start_time  text not null,
  end_time    text,
  description text,
  created_at  timestamptz default now()
);

create index if not exists calendar_user_start on public.calendar (user_id, start_time);
