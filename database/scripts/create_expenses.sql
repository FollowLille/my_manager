CREATE TABLE IF NOT EXISTS expenses(
user_id INTEGER NOT NULL,
category TEXT NOT NULL,
subcategory TEXT NOT NULL,
cur_sum FLOAT NOT NULL,
tags TEXT NOT NULL,
report_date date NOT NULL
)