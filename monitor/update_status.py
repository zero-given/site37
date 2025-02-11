import sqlite3
import os
from datetime import datetime

def migrate_status():
    """Migrate and validate token status in the database"""
    # Get the most recent session folder
    monitor_dir = 'monitor'
    sessions = [d for d in os.listdir(monitor_dir) if os.path.isdir(os.path.join(monitor_dir, d)) and ' - Session ' in d]
    if not sessions:
        print("No session folders found")
        return
    
    latest_session = max(sessions)
    db_path = os.path.join(monitor_dir, latest_session, 'scan_records.db')
    
    print(f"Using database: {db_path}")
    
    try:
        with sqlite3.connect(db_path) as db:
            cursor = db.cursor()
            
            # Add status constraints if they don't exist
            cursor.execute('''
                SELECT sql FROM sqlite_master 
                WHERE type='table' AND name='scan_records'
            ''')
            table_def = cursor.fetchone()[0]
            
            if 'CHECK (status IN' not in table_def:
                print("Adding status constraints...")
                # Create temporary table with constraints
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS scan_records_new (
                        token_address TEXT PRIMARY KEY,
                        scan_timestamp TEXT NOT NULL,
                        pair_address TEXT,
                        token_name TEXT,
                        token_symbol TEXT,
                        token_decimals INTEGER,
                        token_total_supply TEXT,
                        token_age_hours REAL,
                        hp_simulation_success INTEGER,
                        hp_buy_tax REAL,
                        hp_sell_tax REAL,
                        hp_transfer_tax REAL,
                        hp_liquidity_amount REAL,
                        hp_pair_reserves0 TEXT,
                        hp_pair_reserves1 TEXT,
                        hp_buy_gas_used INTEGER,
                        hp_sell_gas_used INTEGER,
                        hp_creation_time TEXT,
                        hp_holder_count INTEGER,
                        hp_is_honeypot INTEGER,
                        hp_honeypot_reason TEXT,
                        hp_is_open_source INTEGER,
                        hp_is_proxy INTEGER,
                        hp_is_mintable INTEGER,
                        hp_can_be_minted INTEGER,
                        hp_owner_address TEXT,
                        hp_creator_address TEXT,
                        hp_deployer_address TEXT,
                        hp_has_proxy_calls INTEGER,
                        hp_pair_liquidity REAL,
                        hp_pair_liquidity_token0 REAL,
                        hp_pair_liquidity_token1 REAL,
                        hp_pair_token0_symbol TEXT,
                        hp_pair_token1_symbol TEXT,
                        hp_flags TEXT,
                        gp_is_open_source INTEGER,
                        gp_is_proxy INTEGER,
                        gp_is_mintable INTEGER,
                        gp_owner_address TEXT,
                        gp_creator_address TEXT,
                        gp_can_take_back_ownership INTEGER,
                        gp_owner_change_balance INTEGER,
                        gp_hidden_owner INTEGER,
                        gp_selfdestruct INTEGER,
                        gp_external_call INTEGER,
                        gp_buy_tax REAL,
                        gp_sell_tax REAL,
                        gp_is_anti_whale INTEGER,
                        gp_anti_whale_modifiable INTEGER,
                        gp_cannot_buy INTEGER,
                        gp_cannot_sell_all INTEGER,
                        gp_slippage_modifiable INTEGER,
                        gp_personal_slippage_modifiable INTEGER,
                        gp_trading_cooldown INTEGER,
                        gp_is_blacklisted INTEGER,
                        gp_is_whitelisted INTEGER,
                        gp_is_in_dex INTEGER,
                        gp_transfer_pausable INTEGER,
                        gp_can_be_minted INTEGER,
                        gp_total_supply TEXT,
                        gp_holder_count INTEGER,
                        gp_owner_percent REAL,
                        gp_owner_balance TEXT,
                        gp_creator_percent REAL,
                        gp_creator_balance TEXT,
                        gp_lp_holder_count INTEGER,
                        gp_lp_total_supply TEXT,
                        gp_is_true_token INTEGER,
                        gp_is_airdrop_scam INTEGER,
                        gp_trust_list TEXT,
                        gp_other_potential_risks TEXT,
                        gp_note TEXT,
                        gp_honeypot_with_same_creator INTEGER,
                        gp_fake_token INTEGER,
                        gp_holders TEXT,
                        gp_lp_holders TEXT,
                        gp_dex_info TEXT,
                        total_scans INTEGER DEFAULT 1,
                        honeypot_failures INTEGER DEFAULT 0,
                        last_error TEXT,
                        status TEXT NOT NULL DEFAULT 'new' CHECK (status IN ('new', 'active', 'removed', 'honeypot')),
                        liq10 REAL,
                        liq20 REAL,
                        liq30 REAL,
                        liq40 REAL,
                        liq50 REAL,
                        liq60 REAL,
                        liq70 REAL,
                        liq80 REAL,
                        liq90 REAL,
                        liq100 REAL,
                        liq110 REAL,
                        liq120 REAL,
                        liq130 REAL,
                        liq140 REAL,
                        liq150 REAL,
                        liq160 REAL,
                        liq170 REAL,
                        liq180 REAL,
                        liq190 REAL,
                        liq200 REAL
                    )
                ''')
                
                # Copy data with status validation
                print("Migrating data with status validation...")
                cursor.execute('''
                    INSERT INTO scan_records_new 
                    SELECT 
                        *,
                        CASE 
                            WHEN status IS NULL OR status = 'new' THEN 'active'
                            WHEN status NOT IN ('new', 'active', 'removed', 'honeypot') THEN 'active'
                            ELSE status 
                        END as status
                    FROM scan_records
                ''')
                
                # Drop old table and rename new one
                cursor.execute('DROP TABLE scan_records')
                cursor.execute('ALTER TABLE scan_records_new RENAME TO scan_records')
                
                # Recreate indexes
                print("Recreating indexes...")
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_scan_timestamp ON scan_records(scan_timestamp)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_token_age ON scan_records(token_age_hours DESC)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_status ON scan_records(status)')
                
                db.commit()
                print("Status constraints added successfully")
            
            # Update any remaining invalid statuses
            print("\nChecking for records that need status updates...")
            cursor.execute('''
                SELECT COUNT(*) 
                FROM scan_records 
                WHERE status IS NULL 
                OR status NOT IN ('new', 'active', 'removed', 'honeypot')
            ''')
            invalid_count = cursor.fetchone()[0]
            
            if invalid_count > 0:
                print(f"Found {invalid_count} records with invalid status")
                cursor.execute('''
                    UPDATE scan_records 
                    SET status = 'active' 
                    WHERE status IS NULL 
                    OR status NOT IN ('new', 'active', 'removed', 'honeypot')
                ''')
                db.commit()
                print("Updated invalid status records to 'active'")
            
            # Print final status distribution
            cursor.execute('''
                SELECT status, COUNT(*) 
                FROM scan_records 
                GROUP BY status
            ''')
            print("\nFinal Status Distribution:")
            print("=" * 50)
            for status, count in cursor.fetchall():
                print(f"Status '{status}': {count} records")
                
    except sqlite3.Error as e:
        print(f"Database error: {str(e)}")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    migrate_status() 