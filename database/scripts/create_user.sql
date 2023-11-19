CREATE TABLE IF NOT EXISTS users (
user_id INTEGER PRIMARY KEY,
name text not null,
vision text not null default 'mine');