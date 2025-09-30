DROP TABLE IF EXISTS song_playlist;
DROP TABLE IF EXISTS song;
DROP TABLE IF EXISTS playlist;

CREATE TABLE song(
    -- In SQLite, a column with type INTEGER PRIMARY KEY is an alias for the ROWID (except in WITHOUT ROWID tables) which is always a 64-bit signed integer. 
    id integer primary key,
    filepath varchar(511) UNIQUE,
    title varchar(255),
    album varchar(255),
    artist varchar(255),
    album_artist varchar(255),
    track_number integer,
    length_seconds integer,
    genre varchar(255),
    codec varchar(15),
    album_date date,
    bitrate int,
    date_added TIMESTAMP default CURRENT_TIMESTAMP
);

CREATE TABLE playlist(
    id integer primary key,
    name varchar(64),
    date_created TIMESTAMP default CURRENT_TIMESTAMP,
    auto_export_path varchar(512),
    path_prefix varchar(255)
);

CREATE TABLE song_playlist(
    playlist_id integer,
    song_id integer,
    date_created TIMESTAMP default CURRENT_TIMESTAMP,
    primary key (playlist_id, song_id),
    foreign key (playlist_id) references playlist(id),
    foreign key (song_id) references song(id)
);
