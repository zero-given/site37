import sqlite3
import os
import json
from datetime import datetime

db_path = os.path.join('monitor', 'January 28 - Session 6', 'scan_records.db')

def check_database():
    try:
        with sqlite3.connect(db_path) as db:
            cursor = db.cursor()
            
            # Get record count
            cursor.execute("SELECT COUNT(*) FROM scan_records")
            count = cursor.fetchone()
            print("\nRecord Count:")
            print("=" * 50)
            print(f"Total records: {count[0]}")
            
            # Get most recent record
            cursor.execute("""
                SELECT token_address, scan_timestamp, token_name, total_scans, honeypot_failures, last_error, status
                FROM scan_records 
                ORDER BY scan_timestamp DESC 
                LIMIT 5
            """)
            records = cursor.fetchall()
            
            if records:
                print("\nMost Recent Records:")
                print("=" * 50)
                for record in records:
                    print(f"\nToken: {record[0]}")
                    print(f"Timestamp: {record[1]}")
                    print(f"Name: {record[2]}")
                    print(f"Scans: {record[3]}")
                    print(f"Failures: {record[4]}")
                    print(f"Last Error: {record[5]}")
                    print(f"Status: {record[6]}")
                    print("-" * 50)
                    
                # Get time range
                cursor.execute("""
                    SELECT MIN(scan_timestamp), MAX(scan_timestamp)
                    FROM scan_records
                """)
                time_range = cursor.fetchone()
                if time_range[0] and time_range[1]:
                    print("\nTime Range:")
                    print("=" * 50)
                    print(f"First scan: {time_range[0]}")
                    print(f"Last scan: {time_range[1]}")
                
                # Get status counts
                cursor.execute("""
                    SELECT status, COUNT(*) 
                    FROM scan_records 
                    GROUP BY status
                """)
                status_counts = cursor.fetchall()
                if status_counts:
                    print("\nStatus Distribution:")
                    print("=" * 50)
                    for status, count in status_counts:
                        print(f"{status}: {count}")
            else:
                print("\nNo records found")
                
    except sqlite3.Error as e:
        print(f"\nDatabase error: {e}")
    except Exception as e:
        print(f"\nUnexpected error: {e}")

if __name__ == "__main__":
    check_database() 