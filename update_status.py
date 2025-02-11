import sqlite3
import os

def update_status():
    db_path = os.path.join('monitor', 'January 28 - Session 6', 'scan_records.db')
    
    try:
        with sqlite3.connect(db_path) as db:
            cursor = db.cursor()
            
            # First check how many records need updating
            cursor.execute('SELECT COUNT(*) FROM scan_records WHERE status IS NULL OR status = "new"')
            count = cursor.fetchone()[0]
            print(f"Found {count} records that need status update")
            
            if count > 0:
                # Update all records to active
                cursor.execute('UPDATE scan_records SET status = "active" WHERE status IS NULL OR status = "new"')
                db.commit()
                print("Updated all records to active status")
            
            # Verify the update
            cursor.execute('SELECT status, COUNT(*) FROM scan_records GROUP BY status')
            for status, count in cursor.fetchall():
                print(f"Status '{status}': {count} records")
                
    except sqlite3.Error as e:
        print(f"Database error: {str(e)}")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == '__main__':
    update_status() 