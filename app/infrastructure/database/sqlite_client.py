import sqlite3
import os

class SQLiteClient:
    def __init__(self, db_path="data/forex_bot.db"):
        # store db_path for later use
        self.db_path = db_path

        # call _run_migrations() at the end
        self._run_migrations()

    def _run_migrations(self):
        # create a data directory if it doesn't exist
        os.makedirs("data", exist_ok=True)

        # connect to the database
        with sqlite3.connect(self.db_path) as conn:
            # get all migration files in order
            migration_dir = "app/infrastructure/database/migrations/"

            # check if migration directory exists
            if not os.path.exists(migration_dir):
                return
            
            # get all .sql files and sort them numerically
            migration_files = sorted([
                f for f in os.listdir(migration_dir)
                if f.endswith('.sql')
            ])

            # run each migration file
            for filename in migration_files:
                filepath = os.path.join(migration_dir, filename)

                # read the SQL content
                with open(filepath, 'r') as f:
                    sql = f.read()

                # execute the SQL(handles multiple statements)
                conn.cursor().executescript(sql)
            conn.commit()
    
    def create_trade(self, trade_data):
        with sqlite3.connect(self.db_path) as conn:
            # get a cursor
            cursor = conn.cursor()

            # execute INSERT with ? placeholders
            cursor.execute("""
                INSERT INTO trades (id, pair, action, lot_size, entry_price, stop_loss, take_profit, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                trade_data['id'],
                trade_data['pair'],
                trade_data['action'],
                trade_data['lot_size'],
                trade_data['entry_price'],
                trade_data['stop_loss'],
                trade_data['take_profit'],
                "open" # status - though database has default, we explicitly set it 
            ))

            # commit is automatic when using context manager,
            # but explicit commit is fine too
            conn.commit()
    
    def update_trade(self, trade_id, close_price):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute(""" 
                UPDATE trades
                SET status = 'closed',
                    close_price = ?,
                    closed_at = datetime('now')
                WHERE id = ?
            """, (close_price, trade_id))
            conn.commit()

        
    def log_signal(self, signal_data):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO signals (id, pair, action, confidence, stop_loss, take_profit, lot_size, model_version)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                signal_data['id'],
                signal_data['pair'],
                signal_data['action'],
                signal_data['confidence'],
                signal_data['stop_loss'],
                signal_data['take_profit'],
                signal_data['lot_size'],
                signal_data['model_version']
            ))

            conn.commit()

    def get_performance(self, date):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(""" 
                SELECT * FROM performance_daily WHERE date = ?
            """, (date,))

            row = cursor.fetchone()
            
            if row is None:
                return None
            
            return dict(row)

    def log_error(self, category, message, context):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute(""" 
                INSERT INTO error_log (category, message, context)
                VALUES (?, ?, ?) 
            """, (
                category,
                message,
                context
            ))

            conn.commit()
    
    def get_all_trades(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM trades
                ORDER BY opened_at DESC 
            """)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_all_signals(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM signals
                ORDER BY timestamp DESC
            """)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]