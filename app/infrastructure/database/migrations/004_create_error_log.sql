CREATE TABLE IF NOT EXISTS error_log (
    id            INTEGER    PRIMARY KEY,
    category      TEXT       NOT NULL,  
    message       TEXT       NOT NULL,
    context       TEXT       NOT NULL,
    logged_at     TEXT       NOT NULL DEFAULT (datetime('now'))
);