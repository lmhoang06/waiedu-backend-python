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

-- Trigger function to update the updated_at column for user
CREATE OR REPLACE FUNCTION update_updated_at_column_for_user_from_user_subject()
RETURNS TRIGGER AS $$
BEGIN
    -- Handle INSERT/UPDATE
    IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN
        UPDATE users
        SET updated_at = CURRENT_TIMESTAMP
        WHERE id = NEW.user_id;
    -- Handle DELETE
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE users
        SET updated_at = CURRENT_TIMESTAMP
        WHERE id = OLD.user_id;
    END IF;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Trigger for user_subjects table to update the updated_at column in users
DROP TRIGGER IF EXISTS trg_user_subjects_update ON user_subjects;

CREATE TRIGGER trg_user_subjects_update
AFTER INSERT OR UPDATE OR DELETE ON user_subjects
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column_for_user_from_user_subject();


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

-- Helper function to check if a user has a specific role
CREATE OR REPLACE FUNCTION check_user_role(p_user_id INTEGER, p_expected_role user_role)
RETURNS BOOLEAN AS $$
DECLARE
    v_user_role user_role;
BEGIN
    SELECT role INTO v_user_role FROM users WHERE id = p_user_id;
    RETURN v_user_role = p_expected_role;
END;
$$ LANGUAGE plpgsql STABLE; -- STABLE because it doesn't modify the DB and returns same result for same inputs within a transaction

-- Drop the table if it exists to apply changes
DROP TABLE IF EXISTS parent_child_links CASCADE;

-- Table to explicitly link Parent users to their Child (Student) users
-- Allows multiple parents per child
CREATE TABLE parent_child_links (
    parent_user_id INTEGER NOT NULL,
    child_user_id INTEGER NOT NULL,
    -- Composite primary key ensures the SAME parent isn't linked to the SAME child multiple times
    PRIMARY KEY (parent_user_id, child_user_id),
    FOREIGN KEY (parent_user_id) REFERENCES users(id) ON DELETE CASCADE, -- Link to the parent user
    FOREIGN KEY (child_user_id) REFERENCES users(id) ON DELETE CASCADE,  -- Link to the child user

    -- CHECK constraints using the helper function to enforce roles
    CONSTRAINT check_parent_role CHECK (check_user_role(parent_user_id, 'parent')),
    CONSTRAINT check_child_role CHECK (check_user_role(child_user_id, 'student'))
);

-- Index for faster lookup of children for a parent
CREATE INDEX idx_parent_child_links_parent_id ON parent_child_links(parent_user_id);
-- Index for faster lookup of parents for a child (useful now with multiple parents)
CREATE INDEX idx_parent_child_links_child_id ON parent_child_links(child_user_id);

-- Recreate or Alter Courses table for BIGINT price and currency code

-- Drop existing table if necessary to redefine columns/constraints (or use ALTER TABLE)
DROP TABLE IF EXISTS courses CASCADE;

-- Recreate Courses table with BIGINT price and currency code
CREATE TABLE courses (
    id SERIAL PRIMARY KEY,
    teacher_user_id INTEGER, -- Link to the user who is the teacher
    title VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    description TEXT,
    image_url VARCHAR(255),
    price BIGINT NOT NULL DEFAULT 0, -- Store VND amount as whole number
    currency_code VARCHAR(3) NOT NULL DEFAULT 'VND', -- Specify currency
    subject_id VARCHAR(50),
    is_published BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP, -- Needs trigger

    FOREIGN KEY (teacher_user_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE SET NULL,

    -- CHECK constraint ensuring teacher_user_id is NULL or points to a 'teacher' role user
    CONSTRAINT check_course_teacher_role CHECK (teacher_user_id IS NULL OR check_user_role(teacher_user_id, 'teacher')),
    -- CHECK constraint for positive price
    CONSTRAINT check_course_price_positive CHECK (price >= 0),
    -- CHECK constraint for currency code (if only VND is supported initially)
    CONSTRAINT check_course_currency_code CHECK (currency_code = 'VND')
);

-- Index for faster lookup of courses by teacher
CREATE INDEX idx_courses_teacher_user_id ON courses(teacher_user_id);
-- Index for faster lookup by subject
CREATE INDEX idx_courses_subject_id ON courses(subject_id);

-- Trigger for updated_at on courses (assuming your function 'update_updated_at_column' exists)
DROP TRIGGER IF EXISTS courses_updated_at_modtime ON courses;
CREATE TRIGGER courses_updated_at_modtime
BEFORE UPDATE ON courses
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- Recreate or Alter Student Enrollments table to capture price at enrollment

-- Drop existing table if necessary to redefine columns/constraints (or use ALTER TABLE)
DROP TABLE IF EXISTS student_enrollments CASCADE;

-- Recreate Student Enrollments table with price capture
CREATE TABLE student_enrollments (
    id SERIAL PRIMARY KEY,          -- Dedicated primary key
    student_user_id INTEGER,       -- Nullable due to ON DELETE SET NULL
    course_id INTEGER NOT NULL,    -- Link to the course
    enrollment_date TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP WITHOUT TIME ZONE,
    progress SMALLINT DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
    completed_date TIMESTAMP WITHOUT TIME ZONE,

    -- Price and Currency capture at the time of enrollment
    price_at_enrollment BIGINT NOT NULL DEFAULT 0,         -- Store the exact price paid (VND)
    currency_at_enrollment VARCHAR(3) NOT NULL DEFAULT 'VND', -- Store the currency code ('VND')

    -- Foreign key modified to SET NULL on user deletion
    FOREIGN KEY (student_user_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,

    -- CHECK constraint ensuring student_user_id is NULL or points to a 'student' role user
    CONSTRAINT check_enrollment_student_role CHECK (student_user_id IS NULL OR check_user_role(student_user_id, 'student')),
    -- CHECK constraint for positive enrollment price
    CONSTRAINT check_enrollment_price_positive CHECK (price_at_enrollment >= 0),
    -- CHECK constraint for enrollment currency code
    CONSTRAINT check_enrollment_currency_code CHECK (currency_at_enrollment = 'VND'),

    -- Unique constraint to prevent the same active student from enrolling multiple times
    CONSTRAINT unique_student_course_enrollment UNIQUE (student_user_id, course_id)
);

-- Indexes for faster queries
CREATE INDEX idx_student_enrollments_student_id ON student_enrollments(student_user_id);
CREATE INDEX idx_student_enrollments_course_id ON student_enrollments(course_id);