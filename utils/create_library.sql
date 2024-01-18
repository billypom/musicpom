DROP TABLE IF EXISTS library;

CREATE TABLE library(
    -- In SQLite, a column with type INTEGER PRIMARY KEY is an alias for the ROWID (except in WITHOUT ROWID tables) which is always a 64-bit signed integer. 
    id integer primary key,
    filepath varchar(511) UNIQUE,
    title varchar(255),
    album varchar(255),
    artist varchar(255),
    genre varchar(255),
    codec varchar(15),
    album_date date,
    bitrate int,
    date_added TIMESTAMP default CURRENT_TIMESTAMP
);