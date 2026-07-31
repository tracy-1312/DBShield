DROP DATABASE IF EXISTS dbshield;
CREATE DATABASE dbshield
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;
USE dbshield;

CREATE TABLE users (
    user_id         INT AUTO_INCREMENT PRIMARY KEY,
    username        VARCHAR(50)  NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,
    full_name       VARCHAR(100) NOT NULL,
    email           VARCHAR(100) NOT NULL,
    role            VARCHAR(20)  NOT NULL,
    clearance_level INT          NOT NULL DEFAULT 1,
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_users_role
        CHECK (role IN ('admin', 'data_manager', 'viewer')),
    CONSTRAINT chk_users_clearance
        CHECK (clearance_level BETWEEN 1 AND 4)
);

CREATE INDEX idx_users_username ON users (username);


CREATE TABLE patient_records (
    record_id            INT AUTO_INCREMENT PRIMARY KEY,
    patient_id           VARCHAR(20)  NOT NULL UNIQUE,
    full_name            VARCHAR(100) NOT NULL,
    date_of_birth        DATE,
    category             VARCHAR(50),
    classification_level INT          NOT NULL DEFAULT 1,
    contact_number       VARCHAR(20),
    email                VARCHAR(100),
    medical_notes        TEXT,
    assigned_doctor      VARCHAR(100),
    last_modified        DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
                                      ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT chk_records_classification
        CHECK (classification_level BETWEEN 1 AND 4)
);

CREATE INDEX idx_records_patient_id     ON patient_records (patient_id);
CREATE INDEX idx_records_classification ON patient_records (classification_level);
CREATE INDEX idx_records_full_name      ON patient_records (full_name);


-- =====================================================================
-- TABLE: access_logs
-- Audit trail. Every view / search / edit / denied attempt is recorded.
-- record_id is nullable because a search is not tied to one record.
-- =====================================================================
CREATE TABLE access_logs (
    log_id     INT AUTO_INCREMENT PRIMARY KEY,
    user_id    INT         NOT NULL,
    record_id  INT         NULL,
    action     VARCHAR(20) NOT NULL,
    status     VARCHAR(20) NOT NULL,
    timestamp  DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_logs_user
        FOREIGN KEY (user_id)   REFERENCES users (user_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_logs_record
        FOREIGN KEY (record_id) REFERENCES patient_records (record_id)
        ON DELETE SET NULL,

    CONSTRAINT chk_logs_action
        CHECK (action IN ('view', 'search', 'edit', 'denied', 'login', 'logout')),
    CONSTRAINT chk_logs_status
        CHECK (status IN ('success', 'denied'))
);

CREATE INDEX idx_logs_user      ON access_logs (user_id);
CREATE INDEX idx_logs_timestamp ON access_logs (timestamp);

INSERT INTO users (username, password_hash, full_name, email, role, clearance_level) VALUES
('jsmith',   '$2b$12$RdOCxEwpUkCFOccvfr9ZLOyY2k4gGaZoksw1OH6fRFa52AhTJ7aXi', 'John Smith',    'jsmith@hospital.com',   'admin',        4),
('sjohnson', '$2b$12$A2dRdjfJ9cxfvWxacmBMpe9pPTqE8zecODVU76fSDLyN5DEcgYxnG', 'Sarah Johnson', 'sjohnson@hospital.com', 'data_manager', 2),
('mbrown',   '$2b$12$HmwJNjJgQwy/7Ge87PXTlOHLBUf90Ki.ESWNfCnrCUxf7Ke4zjMRS', 'Michael Brown', 'mbrown@hospital.com',   'data_manager', 3),
('edavis',   '$2b$12$A59OgHKGauBLrFkzH.P4/.9MTOoedpdS0Vj/f79kHRJLyfl3hJyaW', 'Emily Davis',   'edavis@hospital.com',   'data_manager', 1),
('rwilson',  '$2b$12$qT.eh0eztef06vL2XzzhLu2af.aXGI1145Sw6KRIoDvZ8xF3omEbu', 'Robert Wilson', 'rwilson@hospital.com',  'viewer',       3),
('kwong',    '$2b$12$dingL19Wc9Ia.3uEnjKkf.3hdLH9.cao.qVAt6Hcheux4Em2heFK.', 'Karen Wong',    'kwong@hospital.com',    'viewer',       1);

INSERT INTO patient_records
    (patient_id, full_name, date_of_birth, category, classification_level, contact_number, email, assigned_doctor) VALUES
('PT-00123', 'John Smith',      '1985-03-15', 'General',    2, '(555) 123-4567', 'jsmith@email.com',    'Dr. Carter'),
('PT-00456', 'Sarah Johnson',   '1992-07-22', 'Cardiology', 1, '(555) 234-5678', 'sjohnson@email.com',  'Dr. Smith'),
('PT-00789', 'Michael Brown',   '1978-11-30', 'Oncology',   3, '(555) 345-6789', 'mbrown@email.com',    'Dr. Williams'),
('PT-00234', 'Emily Davis',     '2001-05-18', 'Pediatrics', 1, '(555) 456-7890', 'edavis@email.com',    'Dr. Johnson'),
('PT-00567', 'Robert Wilson',   '1965-09-10', 'Neurology',  4, '(555) 567-8901', 'rwilson@email.com',   'Dr. Brown'),
('PT-00891', 'Linda Martinez',  '1990-02-14', 'General',    1, '(555) 678-9012', 'lmartinez@email.com', 'Dr. Carter'),
('PT-00902', 'David Chen',      '1972-08-05', 'Cardiology', 2, '(555) 789-0123', 'dchen@email.com',     'Dr. Smith'),
('PT-00913', 'Aisha Patel',     '1988-12-01', 'Oncology',   3, '(555) 890-1234', 'apatel@email.com',    'Dr. Williams'),
('PT-00924', 'Thomas Nguyen',   '1995-06-27', 'Pediatrics', 1, '(555) 901-2345', 'tnguyen@email.com',   'Dr. Johnson'),
('PT-00935', 'Grace O''Connor', '1960-04-19', 'Neurology',  4, '(555) 012-3456', 'goconnor@email.com',  'Dr. Brown');


INSERT INTO access_logs (user_id, record_id, action, status, timestamp) VALUES
(2, 1,    'view',   'success', '2026-07-29 09:14:00'),
(2, 2,    'edit',   'success', '2026-07-29 10:02:00'),
(2, NULL, 'search', 'success', '2026-07-30 08:45:00'),
(2, 3,    'denied', 'denied',  '2026-07-30 08:46:00'),
(3, 3,    'view',   'success', '2026-07-30 11:20:00'),
(6, 5,    'denied', 'denied',  '2026-07-31 09:05:00'),
(1, NULL, 'login',  'success', '2026-07-31 09:00:00');

SELECT 'users'           AS table_name, COUNT(*) AS rows_inserted FROM users
UNION ALL
SELECT 'patient_records', COUNT(*) FROM patient_records
UNION ALL
SELECT 'access_logs',     COUNT(*) FROM access_logs;
