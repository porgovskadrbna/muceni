-- migrate:up

CREATE TABLE users (
  first_name TEXT NOT NULL,
  last_name TEXT NOT NULL,
  grad_year INTEGER NOT NULL,

  email TEXT PRIMARY KEY,
  password TEXT NOT NULL
);

CREATE TABLE files (
  filename TEXT PRIMARY KEY,
  deleted BOOLEAN NOT NULL DEFAULT FALSE,

  grade INTEGER NOT NULL,
  subject TEXT NOT NULL,
  name TEXT NOT NULL,

  owner_email TEXT NOT NULL REFERENCES users(email) ON DELETE CASCADE
);

CREATE TABLE votes (
  filename TEXT NOT NULL REFERENCES files(filename) ON DELETE CASCADE,
  voter_email TEXT NOT NULL REFERENCES users(email) ON DELETE CASCADE,

  value INTEGER NOT NULL,

  PRIMARY KEY (filename, voter_email)
);

CREATE TABLE registrations (
  first_name TEXT NOT NULL,
  last_name TEXT NOT NULL,
  grad_year INTEGER NOT NULL,

  email TEXT NOT NULL,
  token TEXT NOT NULL PRIMARY KEY
);

-- migrate:down

DROP TABLE IF EXISTS votes;
DROP TABLE IF EXISTS files;
DROP TABLE IF EXISTS registrations;
DROP TABLE IF EXISTS users;
