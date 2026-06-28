-- Dugout Turf Arena MySQL schema (reference)
-- The FastAPI app creates these automatically via SQLAlchemy (see seed.py),
-- but here is the equivalent raw SQL if you prefer to run it by hand.

CREATE DATABASE IF NOT EXISTS turfbooking;
USE turfbooking;

CREATE TABLE IF NOT EXISTS grounds (
    id          VARCHAR(40)  PRIMARY KEY,
    name        VARCHAR(120) NOT NULL,
    type        VARCHAR(20)  DEFAULT 'open',
    price_n     INT          DEFAULT 0,
    sports      JSON,
    size        VARCHAR(160) DEFAULT '',
    image       VARCHAR(400) DEFAULT '',
    open_hour   INT          DEFAULT 0,
    close_hour  INT          DEFAULT 24,
    removable   BOOLEAN      DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS bookings (
    id          VARCHAR(40)  PRIMARY KEY,
    ground      VARCHAR(40)  NOT NULL,
    customer    VARCHAR(160) NOT NULL,
    phone       VARCHAR(40)  DEFAULT '',
    email       VARCHAR(160) DEFAULT '',
    date_iso    VARCHAR(10)  NOT NULL,
    hours       JSON,
    pay         VARCHAR(20)  DEFAULT 'online',
    status      VARCHAR(20)  DEFAULT 'pending',
    proof       LONGTEXT,
    amount_n    INT          DEFAULT 0,
    demo        BOOLEAN      DEFAULT FALSE,
    created_at  BIGINT,
    INDEX idx_status (status),
    INDEX idx_ground_date (ground, date_iso),
    FOREIGN KEY (ground) REFERENCES grounds(id)
);

CREATE TABLE IF NOT EXISTS blocks (
    id        VARCHAR(80) PRIMARY KEY,   -- 'ground|date|hour'
    ground    VARCHAR(40) NOT NULL,
    date_iso  VARCHAR(10) NOT NULL,
    hour      INT         NOT NULL
);

-- The two real grounds
INSERT IGNORE INTO grounds (id, name, type, price_n, size, removable) VALUES
('open', 'Open Arena', 'open', 2000, 'Open-air · Full-size turf', FALSE),
('box',  'Box Arena',  'box',  1000, 'Covered · Roof netting',    FALSE);
