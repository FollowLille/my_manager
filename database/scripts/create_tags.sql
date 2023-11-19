create table if not exists tags(
id integer primary key AUTOINCREMENT,
name text not null unique);