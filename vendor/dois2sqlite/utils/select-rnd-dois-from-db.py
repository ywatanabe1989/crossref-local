import sqlite3
import sys
import random

def fetch_random_dois(db_path, number_of_records):
    # Connect to the SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Query to count the total number of records in the 'works' table
        cursor.execute("SELECT COUNT(*) FROM works")
        total_records = cursor.fetchone()[0]
        
        # Ensure the requested number of records does not exceed the total available
        number_of_records = min(number_of_records, total_records)
        
        # Generate a random sample of rowids to select specific rows
        random_ids = random.sample(range(1, total_records + 1), number_of_records)
        
        # Fetch the DOI of the randomly selected records
        placeholders = ','.join('?' for _ in random_ids)  # Placeholder for SQL query
        query = f"SELECT doi FROM works WHERE rowid IN ({placeholders})"
        #query = f"SELECT doi FROM works ORDER BY RANDOM() LIMIT {number_of_records}"  # Alternative query using ORDER BY RANDOM() (may be slower for large tables);
        cursor.execute(query, random_ids)
        
        return [doi[0] for doi in cursor.fetchall()]
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        # Close the database connection
        conn.close()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: script.py <db_path> <number_of_records>")
        sys.exit(1)

    db_path = sys.argv[1]
    number_of_records = int(sys.argv[2])
    
    random_list = fetch_random_dois(db_path, number_of_records)
    for doi in random_list:
        print(doi)
    
