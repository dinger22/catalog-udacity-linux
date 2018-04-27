CREATE TABLE if not exists user (
    user_id INTeger primary key autoincrement,
    user_name VARCHAR(256) NULL,
    user_email VARCHAR(256) NULL
);

CREATE TABLE if not exists category (
    category_id INTeger primary key autoincrement,
    category_name VARCHAR(256) NULL
);

CREATE TABLE if not exists catalog_item (
    catalog_item_id INTeger primary key autoincrement,
    catalog_item_name VARCHAR(256) NULL,
    catalog_item_description VARCHAR(256) NULL,
    catalog_item_category_id INTeger,
    user_id integer NOT NULL,
        FOREIGN KEY (user_id) REFERENCES user(user_id)
);

DELETE FROM category;
DELETE FROM catalog_item;
INSERT into category (category_name) values ('category a');
insert into category (category_name) values ('category b');
insert into category (category_name) values ('category c');
insert into category (category_name) values ('category d');
insert into category (category_name) values ('category e');

