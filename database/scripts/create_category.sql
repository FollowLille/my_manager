CREATE TABLE IF NOT EXISTS category(
category_id int not null,
subcategory_id int not null,
category_name text not null,
subcategory_name text not null,
primary key (category_id, subcategory_id)
);

