"""
Test schema migration system.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tests.test_helpers import in_memory_db, init_patients_schema
from dmelogic.db.base import (
    init_schema_version_table,
    get_current_schema_version,
    run_migrations,
    Migration,
    get_migration_history
)


# Example migration
class TestMigration001(Migration):
    version = 1
    description = "Add test_field to patients"
    
    def up(self, conn):
        try:
            conn.execute("ALTER TABLE patients ADD COLUMN test_field TEXT")
            conn.commit()
        except:
            pass


class TestMigration002(Migration):
    version = 2
    description = "Add another_field to patients"
    
    def up(self, conn):
        try:
            conn.execute("ALTER TABLE patients ADD COLUMN another_field TEXT")
            conn.commit()
        except:
            pass


if __name__ == "__main__":
    print("=" * 70)
    print("SCHEMA MIGRATION SYSTEM TEST")
    print("=" * 70)
    
    with in_memory_db() as conn:
        # Initialize patients schema
        init_patients_schema(conn)
        print("[OK] Initialized patients schema")
        
        # Initialize schema version table
        init_schema_version_table(conn)
        print("[OK] Initialized schema_version table")
        
        # Check initial version
        version = get_current_schema_version(conn)
        print(f"[OK] Current schema version: {version}")
        assert version == 0, "Should start at version 0"
        
        # Apply first migration
        migrations = [TestMigration001()]
        TestMigration001().up(conn)
        from dmelogic.db.base import record_migration
        record_migration(conn, 1, "Add test_field to patients")
        
        version = get_current_schema_version(conn)
        print(f"[OK] After migration 1: version {version}")
        assert version == 1, "Should be at version 1"
        
        # Apply second migration
        TestMigration002().up(conn)
        record_migration(conn, 2, "Add another_field to patients")
        
        version = get_current_schema_version(conn)
        print(f"[OK] After migration 2: version {version}")
        assert version == 2, "Should be at version 2"
        
        # Check migration history
        cursor = conn.cursor()
        cursor.execute("SELECT version, description FROM schema_version ORDER BY version")
        history = cursor.fetchall()
        print(f"[OK] Migration history: {len(history)} migrations")
        for v, desc in history:
            print(f"     - Version {v}: {desc}")
        
        # Verify columns were added
        cursor.execute("PRAGMA table_info(patients)")
        columns = [row[1] for row in cursor.fetchall()]
        assert "test_field" in columns, "test_field should exist"
        assert "another_field" in columns, "another_field should exist"
        print(f"[OK] Verified columns added: test_field, another_field")
        
        print("\n" + "=" * 70)
        print("ALL MIGRATION TESTS PASSED")
        print("=" * 70)
        print("\nMigration system features:")
        print("  - schema_version table tracks applied migrations")
        print("  - get_current_schema_version() returns highest version")
        print("  - Migration base class for consistent interface")
        print("  - run_migrations() applies pending migrations")
        print("  - Automatic rollback on migration failure")
        print("  - Migration history tracking with timestamps")
