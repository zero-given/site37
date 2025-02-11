import sqlite3
import os
import time
from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich.text import Text
from rich.layout import Layout

console = Console()

def get_latest_session():
    """Get the most recently modified session folder"""
    sessions = [d for d in os.listdir() if ' - Session ' in d]
    if not sessions:
        return None
    return max(sessions, key=lambda x: os.path.getmtime(x))

def format_age(creation_timestamp):
    """Format age from creation timestamp"""
    if not creation_timestamp or not str(creation_timestamp).isdigit():
        return "Unknown"
    
    try:
        creation_time = datetime.fromtimestamp(int(creation_timestamp))
        age = datetime.now() - creation_time
        
        if age.days > 0:
            return f"{age.days}d {age.seconds//3600}h"
        elif age.seconds >= 3600:
            return f"{age.seconds//3600}h {(age.seconds%3600)//60}m"
        else:
            return f"{age.seconds//60}m {age.seconds%60}s"
    except:
        return "Unknown"

def format_compact_token_row(token_data):
    """Format token data into a compact row format"""
    token_address = token_data[0]
    name = token_data[3] or "Unknown"
    symbol = token_data[4] or "Unknown"
    liquidity = float(token_data[12] or 0)
    buy_tax = float(token_data[9] or 0)
    sell_tax = float(token_data[10] or 0)
    holder_count = token_data[18] or 0
    is_honeypot = bool(token_data[19])
    creation_time = token_data[17] if token_data[17] else "Unknown"
    total_scans = int(token_data[26] or 1)  # total_scans is now at index 26 due to explicit column selection
    
    # Get ownership status (renounced check)
    owner_address = token_data[25] if len(token_data) > 25 else "Unknown"  # hp_owner_address
    is_renounced = owner_address.lower() == "0x000000000000000000000000000000000000dead"
    owner_status = "[green]✓ REN" if is_renounced else "[yellow]OWNED"
    
    # Format creation time and age
    listing_time = "Unknown"
    if creation_time and creation_time.isdigit():
        try:
            creation_dt = datetime.fromtimestamp(int(creation_time))
            listing_time = creation_dt.strftime("%H:%M:%S")
        except:
            listing_time = "Unknown"
    
    # Calculate age
    age = format_age(creation_time)
            
    # Format honeypot status with color
    honeypot_status = "[red]🚫" if is_honeypot else "[green]✅"
    
    # Format liquidity with color based on amount
    if liquidity >= 50000:
        liq_color = "green"
    elif liquidity >= 10000:
        liq_color = "yellow"
    else:
        liq_color = "red"
    liquidity_str = f"[{liq_color}]${liquidity:,.2f}[/]"
    
    # Format scan count with color
    if total_scans >= 10:
        scan_color = "red"
    elif total_scans >= 5:
        scan_color = "yellow"
    else:
        scan_color = "green"
    scan_str = f"[{scan_color}]{total_scans}[/]"
    
    return [
        listing_time,
        age,
        liquidity_str,
        f"{buy_tax:.1f}%/{sell_tax:.1f}%",
        str(holder_count),
        honeypot_status,
        owner_status,
        scan_str,
        symbol,
        name[:20] + "..." if len(name) > 20 else name,
        token_address
    ]

def create_token_table(tokens):
    """Create a table of recent tokens"""
    table = Table(
        show_header=True,
        header_style="bold magenta",
        border_style="cyan",
        title="[bold cyan]Recent Token Discoveries[/]"
    )
    
    # Add columns
    table.add_column("Listed", style="cyan", justify="center")
    table.add_column("Age", style="cyan", justify="right")
    table.add_column("Liquidity", justify="right")
    table.add_column("Buy/Sell Tax", justify="center")
    table.add_column("Holders", justify="right")
    table.add_column("HP", justify="center")
    table.add_column("Owner", justify="center")
    table.add_column("Scans", justify="center")
    table.add_column("Symbol", style="yellow")
    table.add_column("Name", style="bright_white")
    table.add_column("Address", style="dim")
    
    # Add rows
    for token in tokens:
        table.add_row(*format_compact_token_row(token))
    
    return table

def monitor_new_tokens():
    """Monitor database for new token entries with history view"""
    session_folder = get_latest_session()
    if not session_folder:
        console.print("[red]No session folders found!")
        return

    db_path = os.path.join(session_folder, 'scan_records.db')
    if not os.path.exists(db_path):
        console.print(f"[red]Database not found at {db_path}")
        return

    console.print(f"[cyan]Monitoring new tokens in session: [green]{session_folder}")
    
    # Keep track of processed tokens and recent tokens list
    processed_tokens = set()
    recent_tokens = []
    MAX_DISPLAY_TOKENS = 20  # Number of tokens to show in history
    
    # Initialize last check time to 30 minutes ago
    last_check_time = datetime.now() - timedelta(minutes=30)
    last_update = time.time()
    UPDATE_INTERVAL = 5  # Update every 5 seconds

    try:
        with Live(console=console, refresh_per_second=4) as live:
            while True:
                try:
                    current_time = time.time()
                    
                    # Always query the database for latest data
                    with sqlite3.connect(db_path) as db:
                        cursor = db.cursor()
                        
                        # Get latest tokens with fresh data
                        cursor.execute('''
                            SELECT 
                                token_address,
                                scan_timestamp,
                                pair_address,
                                token_name,
                                token_symbol,
                                token_decimals,
                                token_total_supply,
                                token_age_hours,
                                hp_simulation_success,
                                hp_buy_tax,
                                hp_sell_tax,
                                hp_transfer_tax,
                                hp_liquidity_amount,
                                hp_pair_reserves0,
                                hp_pair_reserves1,
                                hp_buy_gas_used,
                                hp_sell_gas_used,
                                hp_creation_time,
                                hp_holder_count,
                                hp_is_honeypot,
                                hp_honeypot_reason,
                                hp_is_open_source,
                                hp_is_proxy,
                                hp_is_mintable,
                                hp_can_be_minted,
                                hp_owner_address,
                                total_scans
                            FROM scan_records 
                            WHERE status = 'active'
                            ORDER BY hp_creation_time DESC, scan_timestamp DESC 
                            LIMIT ?
                        ''', (MAX_DISPLAY_TOKENS,))
                        
                        recent_tokens = cursor.fetchall()
                        
                        # Create and update the table
                        if recent_tokens:
                            table = create_token_table(recent_tokens)
                            
                            # Add stats footer with next update countdown
                            time_until_next = max(0, UPDATE_INTERVAL - (time.time() - last_update))
                            stats = f"\n[dim]Total Processed: {len(processed_tokens)} tokens | Last Update: {datetime.now().strftime('%H:%M:%S')} | Next Update in: {time_until_next:.1f}s[/]"
                            
                            # Update the live display
                            live.update(Panel.fit(
                                table,
                                title="[bold cyan]Token Monitor[/]",
                                subtitle=stats,
                                border_style="cyan"
                            ))
                    
                except sqlite3.Error as e:
                    console.print(f"[red]Database error: {str(e)}")
                
                # Short sleep to prevent high CPU usage while keeping display responsive
                time.sleep(0.25)
                
    except KeyboardInterrupt:
        console.print("\n[yellow]Monitoring stopped by user")
    except Exception as e:
        console.print(f"[red]Error: {str(e)}")

if __name__ == "__main__":
    try:
        monitor_new_tokens()
    except KeyboardInterrupt:
        console.print("\n[yellow]Exiting...") 