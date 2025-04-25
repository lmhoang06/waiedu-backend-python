-- PostgreSQL Database setup for WAIEDU application

-- Drop existing types if they exist (optional, useful for rerunning script)
DROP TYPE IF EXISTS user_gender CASCADE;
DROP TYPE IF EXISTS user_role CASCADE;

-- Create ENUM types first
CREATE TYPE user_gender AS ENUM ('male', 'female', 'other');
CREATE TYPE user_role AS ENUM ('student', 'teacher', 'parent');

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    birth_date DATE,
    gender user_gender, -- Use the created ENUM type
    role user_role NOT NULL DEFAULT 'student', -- Use the created ENUM type
    grade VARCHAR(20),
    school VARCHAR(255),
    teaching_subject VARCHAR(255),
    child_grade VARCHAR(20),
    is_verified BOOLEAN DEFAULT FALSE,
    verification_token VARCHAR(255),
    reset_token VARCHAR(255),
    reset_token_expiry TIMESTAMP WITHOUT TIME ZONE, -- PostgreSQL equivalent for DATETIME
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP -- See trigger below for update behavior
);

-- Trigger function to update the updated_at column automatically
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
   NEW.updated_at = CURRENT_TIMESTAMP;
   RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to execute the function before any update on the users table
-- Drop trigger first if it exists (optional, for rerunning)
DROP TRIGGER IF EXISTS users_updated_at_modtime ON users;
-- Create the trigger
CREATE TRIGGER users_updated_at_modtime
BEFORE UPDATE ON users
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();


-- Pre-defined subjects table
CREATE TABLE IF NOT EXISTS subjects (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

-- User_subjects table (for many-to-many relationship)
CREATE TABLE IF NOT EXISTS user_subjects (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL, -- Use INTEGER to match SERIAL type of users.id
    subject_id VARCHAR(50) NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE, -- Added FK for subject_id consistency
    CONSTRAINT user_subject_unique UNIQUE (user_id, subject_id) -- PostgreSQL UNIQUE constraint syntax
);

-- Insert default subjects using PostgreSQL's ON CONFLICT clause for UPSERT
INSERT INTO subjects (id, name) VALUES
('physics', 'Vật Lý'),
('chemistry', 'Hóa Học'),
('biology', 'Sinh Học'),
('math', 'Toán Học'),
('literature', 'Văn Học'),
('english', 'Tiếng Anh'),
('history', 'Lịch Sử'),
('geography', 'Địa Lý')
ON CONFLICT (id) DO UPDATE SET -- Specify the conflict target (the primary key 'id')
  name = EXCLUDED.name; -- Update name if the id already exists