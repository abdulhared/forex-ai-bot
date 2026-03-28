CREATE TABLE IF NOT EXISTS performance_daily ( 
    date             TEXT       PRIMARY KEY,
    total_trades     INTEGER    NOT NULL,
    wins             INTEGER    NOT NULL, 
    losses           INTEGER    NOT NULL,
    gross_pnl        REAL       NOT NULL,
    win_rate         REAL       NOT NULL,
    opening_balance  REAL       NOT NULL
);