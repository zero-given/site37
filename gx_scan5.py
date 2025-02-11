# monitor/GX_Scan3.py
import os
import sys
import json
import copy
import time
import asyncio
import sqlite3
import threading
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Tuple, List, Any

from web3 import Web3, HTTPProvider
from web3.exceptions import TransactionNotFound, ContractLogicError
from SPXfucked import TokenTracker
from tabulate import tabulate
from colorama import Fore, Style, init
from key_manager import InfuraKeyManager
from rich.console import Console
from rich.table import Table

from terminal_display import console, create_pair_table, create_security_table, log_message
from api_wrapper import api_wrapper
from api_tracker import api_tracker

# Initialize colorama
init(autoreset=True)

# ======================
# STATE MANAGEMENT
# ======================
class StateManager:
    def __init__(self, state_file='scanner_state.json'):
        self.state_file = Path(state_file)
        self.lock = threading.Lock()
        self.default_state = {
            'config': {
                'api_delays': {
                    'goplus_base': 5,
                    'goplus_retry': 25,
                    'honeypot_base': 5
                },
                'debug_settings': {
                    'GOPLUS_RAW_OUTPUT': True,
                    'GOPLUS_FORMATTED': True,
                    'GOPLUS_TABLE': True,
                    'HONEYPOT_RAW_OUTPUT': True,
                    'HONEYPOT_FORMATTED': True,
                    'HONEYPOT_TABLE': True,
                    'SHOW_HOLDER_INFO': True,
                    'SHOW_LP_INFO': True,
                    'SHOW_DEX_INFO': True
                },
                'kick_conditions': {
                    'MAX_AGE_HOURS': 1.0,
                    'MIN_LIQUIDITY': 10000.0,
                    'CHECK_INTERVAL': 300
                },
                'scanning': {
                    'rescan_interval': 300,
                    'max_rescan_count': 1000,
                    'honeypot_failure_limit': 5
                }
            },
            'runtime': {
                'start_time': datetime.now().isoformat(),
                'last_scan': None,
                'active_tokens': 0,
                'total_processed': 0,
                'api_stats': {
                    'goplus_calls': 0,
                    'honeypot_calls': 0
                }
            }
        }
        self.state = copy.deepcopy(self.default_state)
        self.load()

    def load(self):
        try:
            with self.lock:
                if self.state_file.exists():
                    with open(self.state_file, 'r') as f:
                        self.state = json.load(f)
                    log_message(f"Loaded state from {self.state_file}", "INFO")
        except Exception as e:
            log_message(f"State load error: {str(e)}", "ERROR")
            self.state = copy.deepcopy(self.default_state)

    def save(self):
        with self.lock:
            try:
                with open(self.state_file, 'w') as f:
                    json.dump(self.state, f, indent=2)
            except Exception as e:
                log_message(f"State save error: {str(e)}", "ERROR")

    def update_config(self, new_config: Dict[str, Any]):
        with self.lock:
            for section, values in new_config.items():
                if section in self.state['config']:
                    self.state['config'][section].update(values)
                else:
                    self.state['config'][section] = values
            self.save()

    def update_runtime(self, updates: Dict[str, Any]):
        with self.lock:
            self.state['runtime'].update(updates)
            self.save()

    def get_state(self) -> Dict[str, Any]:
        with self.lock:
            return copy.deepcopy(self.state)

# ======================
# DATABASE MANAGEMENT
# ======================
def initialize_database_structure(folder_name: str) -> None:
    """Initialize all required database structures"""
    try:
        db_path = Path(folder_name) / 'SCAN_RECORDS.db'
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Create main scan records table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scan_records (
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
            
            # Create indexes
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_scan_timestamp 
                ON scan_records(scan_timestamp)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_status 
                ON scan_records(status)
            ''')
            
            # Create honeypot archive table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS HONEYPOTS (
                    token_address TEXT PRIMARY KEY,
                    removal_timestamp TEXT NOT NULL,
                    original_scan_timestamp TEXT,
                    token_name TEXT,
                    token_symbol TEXT,
                    token_decimals INTEGER,
                    token_total_supply TEXT,
                    token_pair_address TEXT,
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
                    total_scans INTEGER,
                    honeypot_failures INTEGER,
                    last_error TEXT,
                    removal_reason TEXT
                )
            ''')
            
            conn.commit()
            
    except Exception as e:
        log_message(f"Database initialization failed: {str(e)}", "ERROR")
        raise

# ======================
# TOKEN CHECKER CLASS
# ======================
class TokenChecker:
    def __init__(self, tracker: TokenTracker, folder_name: str, state_manager: StateManager):
        self.tracker = tracker
        self.folder_name = folder_name
        self.state_manager = state_manager
        self.web3 = Web3(HTTPProvider(self.tracker.config.node_rpc))
        self.logger = tracker.logger
        self.config = tracker.config
        self.goplus_cache = {}
        self.cache_duration = 300
        self.ensure_database_ready()

    def ensure_database_ready(self):
        """Ensure database structure exists"""
        try:
            db_path = Path(self.folder_name) / 'scan_records.db'
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS token_tables (
                        table_name TEXT PRIMARY KEY,
                        token_address TEXT NOT NULL,
                        token_name TEXT,
                        created_at TEXT NOT NULL
                    )
                ''')
                conn.commit()
        except Exception as e:
            log_message(f"Database verification failed: {str(e)}", "ERROR")
            raise

    async def process_token(self, token_address: str, pair_address: str):
        """Main token processing logic"""
        state = self.state_manager.get_state()
        try:
            # Get current configuration
            api_delays = state['config']['api_delays']
            debug_settings = state['config']['debug_settings']
            
            # Add artificial delay based on config
            await asyncio.sleep(api_delays['goplus_base'])
            
            # Process GoPlus data
            goplus_data = await self.get_goplus_data(token_address)
            
            # Process Honeypot data
            honeypot_data = await self.get_honeypot_data(token_address)
            
            # Update database
            self.update_database(token_address, pair_address, goplus_data, honeypot_data)
            
            # Update runtime stats
            self.state_manager.update_runtime({
                'total_processed': self.state_manager.get_state()['runtime']['total_processed'] + 1
            })
            
        except Exception as e:
            log_message(f"Token processing failed: {str(e)}", "ERROR")
            self.update_error_state(token_address, str(e))

    async def get_goplus_data(self, token_address: str) -> Dict:
        """Retrieve GoPlus security data"""
        state = self.state_manager.get_state()
        try:
            # Use configured delays
            await asyncio.sleep(state['config']['api_delays']['goplus_base'])
            
            # Check cache first
            if token_address in self.goplus_cache:
                cached_data = self.goplus_cache[token_address]
                if time.time() - cached_data['timestamp'] < self.cache_duration:
                    return cached_data['data']
            
            # API call
            url = f"https://api.gopluslabs.io/api/v1/token_security/1?contract_addresses={token_address}"
            async with api_wrapper.get(url) as response:
                if response.status != 200:
                    raise Exception(f"GoPlus API error: {response.status}")
                
                data = await response.json()
                self.goplus_cache[token_address] = {
                    'data': data,
                    'timestamp': time.time()
                }
                
                # Update API stats
                self.state_manager.update_runtime({
                    'api_stats': {
                        'goplus_calls': state['runtime']['api_stats']['goplus_calls'] + 1
                    }
                })
                
                return data
            
        except Exception as e:
            log_message(f"GoPlus API error: {str(e)}", "ERROR")
            await asyncio.sleep(state['config']['api_delays']['goplus_retry'])
            raise

    async def get_honeypot_data(self, token_address: str) -> Dict:
        """Retrieve Honeypot checker data"""
        state = self.state_manager.get_state()
        try:
            await asyncio.sleep(state['config']['api_delays']['honeypot_base'])
            
            url = f"https://api.honeypot.is/v2/IsHoneypot?address={token_address}"
            async with api_wrapper.get(url) as response:
                if response.status != 200:
                    raise Exception(f"Honeypot API error: {response.status}")
                
                data = await response.json()
                
                # Update API stats
                self.state_manager.update_runtime({
                    'api_stats': {
                        'honeypot_calls': state['runtime']['api_stats']['honeypot_calls'] + 1
                    }
                })
                
                return data
                
        except Exception as e:
            log_message(f"Honeypot API error: {str(e)}", "ERROR")
            raise

    def update_database(self, token_address: str, pair_address: str, 
                      goplus_data: Dict, honeypot_data: Dict) -> None:
        """Update database with new scan results"""
        try:
            db_path = Path(self.folder_name) / 'scan_records.db'
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Prepare data for insertion
                current_time = datetime.now().isoformat()
                token_age = self.calculate_token_age(honeypot_data)
                
                # Insert or update record
                cursor.execute('''
                    INSERT OR REPLACE INTO scan_records (
                        token_address, scan_timestamp, pair_address, 
                        token_name, token_symbol, token_decimals,
                        token_total_supply, token_age_hours,
                        gp_is_open_source, gp_is_proxy, gp_is_mintable,
                        hp_is_honeypot, hp_honeypot_reason,
                        status, total_scans
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    token_address,
                    current_time,
                    pair_address,
                    goplus_data.get('token_name', ''),
                    goplus_data.get('token_symbol', ''),
                    goplus_data.get('decimals', 0),
                    goplus_data.get('total_supply', '0'),
                    token_age,
                    goplus_data.get('is_open_source', 0),
                    goplus_data.get('is_proxy', 0),
                    goplus_data.get('is_mintable', 0),
                    honeypot_data.get('isHoneypot', 0),
                    honeypot_data.get('honeypotResult', ''),
                    'active',
                    1
                ))
                
                conn.commit()
                
        except Exception as e:
            log_message(f"Database update failed: {str(e)}", "ERROR")
            raise

    def calculate_token_age(self, honeypot_data: Dict) -> float:
        """Calculate token age in hours from creation time"""
        creation_time = honeypot_data.get('creationTime')
        if not creation_time:
            return 0.0
            
        try:
            create_dt = datetime.fromtimestamp(creation_time)
            delta = datetime.now() - create_dt
            return delta.total_seconds() / 3600
        except:
            return 0.0

    def update_error_state(self, token_address: str, error_msg: str) -> None:
        """Update database with error information"""
        try:
            db_path = Path(self.folder_name) / 'scan_records.db'
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE scan_records 
                    SET last_error = ?, honeypot_failures = honeypot_failures + 1 
                    WHERE token_address = ?
                ''', (error_msg, token_address))
                
                conn.commit()
                
        except Exception as e:
            log_message(f"Error state update failed: {str(e)}", "ERROR")

    async def process_rescan_tokens(self) -> None:
        """Process tokens needing rescan"""
        state = self.state_manager.get_state()
        try:
            db_path = Path(self.folder_name) / 'scan_records.db'
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Get tokens due for rescan
                cursor.execute('''
                    SELECT token_address, pair_address 
                    FROM scan_records 
                    WHERE status = 'active'
                    ORDER BY scan_timestamp ASC
                    LIMIT ?
                ''', (state['config']['scanning']['max_rescan_count'],))
                
                tokens = cursor.fetchall()
                
                for token_address, pair_address in tokens:
                    await self.process_token(token_address, pair_address)
                    await asyncio.sleep(state['config']['api_delays']['goplus_base'])
                    
        except Exception as e:
            log_message(f"Rescan processing failed: {str(e)}", "ERROR")

# ======================
# MAIN APPLICATION CLASS
# ======================
class TokenTrackerMain:
    def __init__(self, config_path: str, folder_name: str):
        self.folder_name = Path(folder_name)
        self.config_path = config_path
        self.state_manager = StateManager(self.folder_name / 'scanner_state.json')
        self.command_pipe = self.folder_name / 'command_pipe'
        self.response_pipe = self.folder_name / 'response_pipe'
        self.setup_ipc()
        
        self.tracker = TokenTracker(config_path)
        self.checker = TokenChecker(self.tracker, str(self.folder_name), self.state_manager)
        self.running = True
        self.spinner_idx = 0
        self.spinner_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        self.process_semaphore = asyncio.Semaphore(1)
        
        initialize_database_structure(str(self.folder_name))

    def setup_ipc(self):
        """Initialize named pipes for inter-process communication"""
        try:
            if self.command_pipe.exists():
                os.remove(self.command_pipe)
            if self.response_pipe.exists():
                os.remove(self.response_pipe)
                
            os.mkfifo(self.command_pipe)
            os.mkfifo(self.response_pipe)
            log_message("IPC pipes created successfully", "DEBUG")
        except Exception as e:
            log_message(f"IPC setup failed: {str(e)}", "ERROR")
            raise

    async def ipc_listener(self):
        """Listen for commands through named pipes"""
        while self.running:
            try:
                with open(self.command_pipe, 'r') as pipe:
                    command = pipe.read().strip()
                    response = await self.handle_command(command)
                    
                    with open(self.response_pipe, 'w') as resp_pipe:
                        resp_pipe.write(response)
                        
            except Exception as e:
                await asyncio.sleep(1)

    async def handle_command(self, command: str) -> str:
        """Process incoming commands"""
        try:
            parts = command.split(' ', 1)
            action = parts[0]
            payload = json.loads(parts[1]) if len(parts) > 1 else None
            
            if action == 'GET_STATE':
                return json.dumps(self.state_manager.get_state())
                
            elif action == 'UPDATE_CONFIG':
                self.state_manager.update_config(payload)
                return json.dumps({'status': 'success'})
                
            elif action == 'SHUTDOWN':
                self.stop()
                return json.dumps({'status': 'shutting_down'})
                
            return json.dumps({'status': 'error', 'message': 'Invalid command'})
            
        except Exception as e:
            return json.dumps({'status': 'error', 'message': str(e)})

    async def main_loop(self):
        """Main execution loop with state integration"""
        asyncio.create_task(self.ipc_listener())
        last_rescan = datetime.now()
        
        try:
            while self.running:
                current_time = datetime.now()
                state = self.state_manager.get_state()
                
                # Update runtime state
                self.state_manager.update_runtime({
                    'last_loop': current_time.isoformat(),
                    'active_tokens': self.get_active_token_count()
                })
                
                # Process rescans
                rescan_interval = state['config']['scanning']['rescan_interval']
                if (current_time - last_rescan).total_seconds() >= rescan_interval:
                    await self.checker.process_rescan_tokens()
                    last_rescan = current_time
                    self.state_manager.update_runtime({
                        'last_rescan': last_rescan.isoformat()
                    })
                
                # Main processing logic
                await asyncio.sleep(1)
                
        except Exception as e:
            log_message(f"Main loop error: {str(e)}", "ERROR")
            self.stop()

    def get_active_token_count(self) -> int:
        """Get count of active tokens from database"""
        try:
            db_path = self.folder_name / 'scan_records.db'
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM scan_records WHERE status = "active"')
                return cursor.fetchone()[0]
        except Exception as e:
            log_message(f"Active token count error: {str(e)}", "ERROR")
            return 0

    def stop(self):
        """Clean shutdown procedure"""
        self.running = False
        try:
            os.remove(self.command_pipe)
            os.remove(self.response_pipe)
        except Exception as e:
            pass
        log_message("Application stopped cleanly", "INFO")

# ======================
# MAIN EXECUTION
# ======================
if __name__ == "__main__":
    print("=== Token Scanner ===")
    
    try:
        # Windows event loop policy
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            
        # Session selection logic
        sessions = sorted(Path('.').glob('* - Session *'), key=os.path.getmtime, reverse=True)
        if not sessions:
            session_folder = Path(f"{datetime.now().strftime('%B %d')} - Session 1")
            session_folder.mkdir()
        else:
            print("Existing sessions:")
            for i, session in enumerate(sessions, 1):
                print(f"{i}. {session.name}")
            choice = int(input("Select session: ")) - 1
            session_folder = sessions[choice]
            
        # Initialize and run
        main = TokenTrackerMain("config.json", session_folder)
        asyncio.run(main.main_loop())
        
    except KeyboardInterrupt:
        print("\nShutting down...")
        main.stop()
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        main.stop()