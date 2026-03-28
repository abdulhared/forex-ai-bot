CREATE TABLE IF NOT EXISTS signals (
    id             TEXT   PRIMARY KEY,
    pair           TEXT    NOT NULL, 
    action         TEXT    NOT NULL,
    confidence     REAL    NOT NULL,
    take_profit    REAL    NOT NULL,
    stop_loss      REAL    NOT NULL,
    lot_size       REAL    NOT NULL,
    model_version  TEXT    NOT NULL,
    timestamp      TEXT    NOT NULL DEFAULT (datetime('now'))
)