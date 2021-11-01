CREATE TABLE instrument(
  id integer primary key autoincrement,
  test_func_name TEXT NOT NULL,
  execution_time REAL NOT NULL,
  cprofile_data BLOB NOT NULL
);