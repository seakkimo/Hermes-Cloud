-- V1.6 Todo table
-- Run this in Supabase SQL Editor

create table if not exists public.todos (
  id         bigserial primary key,
  user_id    bigint not null,
  title      text not null,
  done       boolean not null default false,
  created_at timestamptz default now()
);

create index if not exists todos_user_done on public.todos (user_id, done);
