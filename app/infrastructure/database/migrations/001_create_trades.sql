CREATE TABLE IF NOT EXISTS trades (
    id             TEXT   PRIMARY KEY,
    pair           TEXT    NOT NULL, 
    action         TEXT    NOT NULL,
    lot_size       REAL    NOT NULL,
    entry_price    REAL    NOT NULL,
    stop_loss      REAL    NOT NULL,
    take_profit    REAL    NOT NULL,
    status         TEXT    NOT NULL DEFAULT 'open',
    opened_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    close_price    REAL, 
    closed_at      TEXT
);