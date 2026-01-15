#!/usr/bin/env python3
"""
Check for active database connections and help clean them up.

This script helps diagnose and resolve database lock issues before
running the citations table rebuild.
"""

import sqlite3
import subprocess
import sys
from pathlib import Path
import argparse


def check_lsof(db_path: str) -> list:
    """
    Check for processes accessing the database using lsof.

    Args:
        db_path: Path to database file

    Returns:
        List of process info dictionaries
    """
    try:
        result = subprocess.run(
            ["lsof", db_path],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')[1:]  # Skip header
            processes = []
            for line in lines:
                parts = line.split()
                if len(parts) >= 2:
                    processes.append({
                        'command': parts[0],
                        'pid': parts[1],
                        'user': parts[2] if len(parts) > 2 else 'unknown'
                    })
            return processes
        return []

    except FileNotFoundError:
        print("⚠ lsof command not available")
        return []
    except Exception as e:
        print(f"⚠ Error running lsof: {e}")
        return []


def check_database_lock(db_path: str) -> bool:
    """
    Test if database is locked.

    Args:
        db_path: Path to database file

    Returns:
        True if accessible, False if locked
    """
    try:
        conn = sqlite3.connect(db_path, timeout=5.0)
        conn.execute("BEGIN IMMEDIATE")
        conn.execute("ROLLBACK")
        conn.close()
        return True
    except sqlite3.OperationalError as e:
        if "locked" in str(e).lower():
            return False
        raise


def check_wal_files(db_path: Path) -> dict:
    """
    Check for SQLite WAL and SHM files.

    Args:
        db_path: Path to database file

    Returns:
        Dictionary with file existence and sizes
    """
    wal_file = db_path.parent / f"{db_path.name}-wal"
    shm_file = db_path.parent / f"{db_path.name}-shm"

    return {
        'wal': {
            'exists': wal_file.exists(),
            'size': wal_file.stat().st_size if wal_file.exists() else 0
        },
        'shm': {
            'exists': shm_file.exists(),
            'size': shm_file.stat().st_size if shm_file.exists() else 0
        }
    }


def main():
    parser = argparse.ArgumentParser(
        description="Check database connections and help clean them up",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check database status
  python check_db_connections.py --db /path/to/crossref.db

  # Get detailed information
  python check_db_connections.py --db /path/to/crossref.db --verbose
        """
    )

    parser.add_argument(
        "--db",
        type=str,
        default="./data/crossref.db",
        help="Path to CrossRef database"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed information"
    )

    args = parser.parse_args()
    db_path = Path(args.db)

    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        return 1

    print("="*70)
    print("DATABASE CONNECTION CHECK")
    print("="*70)
    print(f"Database: {db_path}")
    print(f"Size: {db_path.stat().st_size / (1024**4):.2f} TB")
    print()

    # Check for lock
    print("🔍 Checking database lock status...")
    is_accessible = check_database_lock(str(db_path))

    if is_accessible:
        print("✅ Database is accessible (not locked)")
    else:
        print("❌ Database is LOCKED")
        print()
        print("This means another process is currently using the database.")

    print()

    # Check for processes using lsof
    print("🔍 Checking for processes accessing the database...")
    processes = check_lsof(str(db_path))

    if processes:
        print(f"⚠ Found {len(processes)} process(es) accessing the database:")
        for proc in processes:
            print(f"  - {proc['command']} (PID: {proc['pid']}, User: {proc['user']})")
        print()
        print("To close these processes:")
        for proc in processes:
            print(f"  kill {proc['pid']}  # Close {proc['command']}")
    else:
        print("✅ No processes found accessing the database")

    print()

    # Check for WAL files
    print("🔍 Checking for SQLite WAL/SHM files...")
    wal_info = check_wal_files(db_path)

    if wal_info['wal']['exists'] or wal_info['shm']['exists']:
        print("ℹ SQLite temporary files found:")
        if wal_info['wal']['exists']:
            print(f"  - WAL file: {wal_info['wal']['size'] / (1024**2):.2f} MB")
        if wal_info['shm']['exists']:
            print(f"  - SHM file: {wal_info['shm']['size'] / 1024:.2f} KB")
        print("  (These are normal for databases in WAL mode)")
    else:
        print("✅ No temporary files found")

    print()
    print("="*70)

    # Summary and recommendations
    if is_accessible and not processes:
        print("✅ DATABASE IS READY FOR REBUILD")
        print()
        print("You can now run the rebuild script:")
        print(f"  python scripts/database/rebuild_citations_table.py --db {db_path}")
    else:
        print("⚠ DATABASE IS NOT READY")
        print()
        print("Recommended actions:")
        if processes:
            print("  1. Close all processes listed above")
            print("  2. Check for SQLite browser tools or IDE database viewers")
            print("  3. Close all terminals with Python sessions")
        if not is_accessible:
            print("  1. Wait a moment and try again (transient lock)")
            print("  2. Check for stuck processes: ps aux | grep crossref")
            print("  3. Restart any long-running services using the database")

    print("="*70)

    return 0 if is_accessible else 1


if __name__ == "__main__":
    sys.exit(main())

# EOF
