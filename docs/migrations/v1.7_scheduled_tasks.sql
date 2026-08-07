-- V1.7 Scheduled Tasks table
-- Run this in Supabase SQL Editor

create table if not exists public.scheduled_tasks (
  id          bigserial primary key,
  name        text not null unique,
  cron_label  text not null,           -- human-readable, e.g. "07:30 UTC+8"
  prompt      text not null,           -- prompt sent to Agent
  enabled     boolean not null default true,
  created_at  timestamptz default now()
);

-- Seed default tasks
insert into public.scheduled_tasks (name, cron_label, prompt, enabled) values
(
  'weather',
  '07:30 UTC+8',
  '請用繁體中文查詢並報告今日台灣（台北）的天氣預報，包含溫度、降雨機率、體感溫度和穿衣建議。',
  true
),
(
  'todo_reminder',
  '07:30 UTC+8',
  '請列出我目前所有待辦事項（pending todos），用繁體中文整理成早安提醒格式。',
  true
),
(
  'morning_brief',
  '08:00 UTC+8',
  '請用繁體中文整合今日早報：1) 最新 AI 與科技新聞摘要 2) 最新 AI/Robotics 論文重點。請簡潔有力。',
  true
),
(
  'daily_fact',
  '19:00 UTC+8',
  '請用繁體中文告訴我一則今天的特別知識、有趣科學事實、生活常識或歷史小故事。要有趣、實用、讓人印象深刻。',
  true
)
on conflict (name) do nothing;
