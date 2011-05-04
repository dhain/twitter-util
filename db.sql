create table tweet (
    tweet_id integer primary key,
    timestamp timestamp not null,
    name text not null,
    screen_name text not null,
    text text not null,
    stream_file text not null,
    stream_offset integer not null,
    stream_length integer not null
);
create index tweet_screen_name_idx on tweet (screen_name);
