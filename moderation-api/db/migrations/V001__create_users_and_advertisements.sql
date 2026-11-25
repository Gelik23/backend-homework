CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    is_verified BOOLEAN NOT NULL,
    violations_qty INTEGER NOT NULL CHECK (violations_qty >= 0)
);

CREATE TABLE advertisements (
    id SERIAL PRIMARY KEY,
    seller_id INTEGER NOT NULL REFERENCES users(id),
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    category INTEGER NOT NULL,
    images_qty INTEGER NOT NULL CHECK (images_qty >= 0)
);
