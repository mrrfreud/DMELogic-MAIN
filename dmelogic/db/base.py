import os
import sqlite3
import shutil
from datetime import datetime
from typing import Optional, Dict, Any, List

from dmelogic.config import _default_db_folder  # from your extracted config.py
from dmelogic.settings import load_settings
from dmelogic.config import debug_log  # optional, for logging


def _load_db_folder_preferred() -> Optional[str]:
    """
    Best-effort: resolve the preferred DB folder.

    Priority:
      1) dmelogic.paths.db_dir() (respects installed data_path.txt)
      2) settings.json db_folder
      3) config._default_db_folder()
    """
    # 1) Centralized path resolver (handles installed data_path.txt)
    try:
        from dmelogic.paths import db_dir
        p = db_dir()
        os.makedirs(str(p), exist_ok=True)
        return str(p)
    except Exception as e:
        debug_log(f"DB: failed to read preferred db_dir(): {e}")

    # 2) Settings
    try:
        db_folder = _load_db_folder_from_settings()
        if db_folder:
            return db_folder
    except Exception:
        pass

    # 3) Default
    try:
        return _default_db_folder()
    except Exception:
        return None


def _load_db_folder_from_settings() -> Optional[str]:
    """Read db_folder from settings.json (if present)."""
    try:
        settings = load_settings()
        db_folder = settings.get("db_folder")
        if db_folder and isinstance(db_folder, str) and db_folder.strip():
            os.makedirs(db_folder, exist_ok=True)
            return db_folder
    except Exception as e:
        debug_log(f"DB: failed to read db_folder from settings: {e}")
    return None


def find_existing_db(filename: str, folder_path: Optional[str] = None) -> Optional[str]:
    """
    Search common locations for an existing database file and return the largest one.

    This mirrors your original logic:
      - App root (next to app.py)
      - Current folder_path (user's fax folder) if provided
      - db_folder from settings.json
      - Parent of folder_path (if provided)
      - Current working directory
    """
    try:
        paths: list[str] = []

        app_root = os.path.dirname(os.path.abspath(__file__))  # dmelogic/db
        app_root = os.path.dirname(app_root)                   # dmelogic/
        app_root = os.path.dirname(app_root)                   # project root

        base_folder = folder_path or app_root
        preferred_db_folder = _load_db_folder_preferred()
        db_folder = _load_db_folder_from_settings()

        paths.append(os.path.join(app_root, filename))
        paths.append(os.path.join(base_folder, filename))

        if preferred_db_folder:
            paths.append(os.path.join(preferred_db_folder, filename))

        if db_folder:
            paths.append(os.path.join(db_folder, filename))

        try:
            parent = os.path.dirname(base_folder)
            paths.append(os.path.join(parent, filename))
        except Exception:
            pass

        paths.append(os.path.join(os.getcwd(), filename))

        existing = [(p, os.path.getsize(p)) for p in paths if os.path.exists(p)]
        if existing:
            existing.sort(key=lambda t: t[1], reverse=True)
            return existing[0][0]
        return None
    except Exception as e:
        debug_log(f"DB: find_existing_db failed for {filename}: {e}")
        return None


def resolve_db_path(filename: str, folder_path: Optional[str] = None) -> str:
    """
    Resolve a stable path for a DB file, with the same strategy you had in resolve_db_path():
      - prefer settings['db_folder'] if set (and copy the largest existing DB there)
      - otherwise use the largest existing DB among common locations
      - if nothing exists, create in db_folder or in app root
    """
    try:
        app_root = os.path.dirname(os.path.abspath(__file__))
        app_root = os.path.dirname(app_root)  # dmelogic/
        app_root = os.path.dirname(app_root)  # project root

        existing = find_existing_db(filename, folder_path=folder_path)

        preferred_db_folder = _load_db_folder_preferred()
        if preferred_db_folder:
            try:
                os.makedirs(preferred_db_folder, exist_ok=True)
            except Exception:
                pass

            dest_path = os.path.join(preferred_db_folder, filename)
            try:
                if (
                    not os.path.exists(dest_path)
                    and existing
                    and os.path.abspath(existing) != os.path.abspath(dest_path)
                ):
                    try:
                        shutil.copy2(existing, dest_path)
                    except Exception:
                        # If copy fails, fall back to using the existing file in place
                        return existing
                elif (
                    os.path.exists(dest_path)
                    and existing
                    and os.path.abspath(existing) != os.path.abspath(dest_path)
                ):
                    # Installed builds often ship a small template DB into the
                    # destination folder. If the user already has a larger DB
                    # elsewhere, prefer that to avoid 'missing orders'.
                    try:
                        dest_size = os.path.getsize(dest_path)
                        src_size = os.path.getsize(existing)
                        # Only replace if the existing DB is clearly larger.
                        if src_size > (dest_size * 1.25) and src_size > 1024 * 1024:
                            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                            backup_path = f"{dest_path}.premerge_{ts}.bak"
                            try:
                                shutil.copy2(dest_path, backup_path)
                                debug_log(f"DB: backed up small dest DB to {backup_path}")
                            except Exception as e:
                                debug_log(f"DB: failed to backup dest DB {dest_path}: {e}")

                            try:
                                shutil.copy2(existing, dest_path)
                                debug_log(
                                    f"DB: replaced dest DB with larger existing DB: {existing} -> {dest_path}"
                                )
                            except Exception as e:
                                debug_log(f"DB: failed to copy existing DB into dest {dest_path}: {e}")
                                return existing
                    except Exception as e:
                        debug_log(f"DB: resolve_db_path size-compare failed for {filename}: {e}")
                return dest_path
            except Exception as e:
                debug_log(f"DB: resolve_db_path copy logic failed for {filename}: {e}")
                return existing or os.path.join(app_root, filename)

        # Fallback to settings db_folder if preferred folder couldn't be resolved
        db_folder = _load_db_folder_from_settings()
        if db_folder:
            try:
                os.makedirs(db_folder, exist_ok=True)
            except Exception:
                pass

            dest_path = os.path.join(db_folder, filename)
            try:
                if (
                    not os.path.exists(dest_path)
                    and existing
                    and os.path.abspath(existing) != os.path.abspath(dest_path)
                ):
                    try:
                        shutil.copy2(existing, dest_path)
                    except Exception:
                        return existing
                return dest_path
            except Exception as e:
                debug_log(f"DB: resolve_db_path copy logic failed for {filename}: {e}")
                return existing or os.path.join(app_root, filename)

        # No db_folder configured: use largest existing or app root as last resort
        return existing or os.path.join(app_root, filename)

    except Exception as e:
        debug_log(f"DB: resolve_db_path fatal for {filename}: {e}")
        # Fallback to folder_path on error
        try:
            base = folder_path or "."
            return os.path.join(base, filename)
        except Exception:
            return filename


def row_to_dict(row: Optional[sqlite3.Row]) -> Dict[str, Any]:
    """
    Safely convert a sqlite3.Row to a dict.
    
    sqlite3.Row objects don't have a .get() method, which can cause bugs
    when code treats them like dicts. This helper ensures safe conversion.
    
    Args:
        row: sqlite3.Row object or None
    
    Returns:
        dict: Dictionary with column names as keys, or empty dict if row is None
    
    Example:
        cursor.execute("SELECT * FROM patients WHERE id = ?", (1,))
        row = cursor.fetchone()
        patient_dict = row_to_dict(row)
        name = patient_dict.get('name', 'Unknown')  # Safe!
    """
    if row is None:
        return {}
    return dict(row)


def rows_to_dicts(rows: list[sqlite3.Row]) -> list[Dict[str, Any]]:
    """
    Convert a list of sqlite3.Row objects to list of dicts.
    
    Args:
        rows: List of sqlite3.Row objects
    
    Returns:
        list: List of dictionaries
    """
    return [dict(row) for row in rows]


def get_connection(filename: str, folder_path: Optional[str] = None) -> sqlite3.Connection:
    """
    Open a sqlite3 connection for the given DB filename using resolve_db_path.
    This is the main entry point UI code should use from now on.
    
    Sets important PRAGMAs for:
    - foreign_keys: Enforce referential integrity
    - journal_mode=WAL: Write-Ahead Logging for better concurrency (multi-window safety)
    - synchronous=NORMAL: Balance between safety and performance
    """
    db_path = resolve_db_path(filename, folder_path=folder_path)
    conn = sqlite3.connect(db_path)
    
    # Enable foreign key constraints for data integrity
    conn.execute("PRAGMA foreign_keys = ON;")
    
    # Use WAL mode for better concurrency - allows multiple readers while writing
    # This is crucial for multi-window operation where multiple dialogs may access DB
    conn.execute("PRAGMA journal_mode = WAL;")
    
    # NORMAL synchronous mode: fsync only at critical moments (checkpoint)
    # Balances performance and safety - much faster than FULL, still safe
    conn.execute("PRAGMA synchronous = NORMAL;")
    
    return conn


class UnitOfWork:
    """
    Lightweight unit-of-work for coordinating multiple sqlite DBs.

    - Lazily opens connections keyed by filename.
    - Reuses connections within the lifetime of the UoW.
    - Allows a single commit()/rollback() decision at the end.
    - NOTE: sqlite cannot guarantee *true* atomicity across multiple .db files.
            This is a coordination helper, not a distributed transaction.
    
    Usage:
        with UnitOfWork(folder_path) as uow:
            orders_conn = uow.connection("orders.db")
            inv_conn = uow.connection("inventory.db")
            # ... do work with both connections ...
            # On success: auto-commits both
            # On exception: auto-rolls back both
    """

    def __init__(self, folder_path: Optional[str] = None):
        self.folder_path = folder_path
        self._conns: Dict[str, sqlite3.Connection] = {}
        self._committed = False
        self._closed = False

    def connection(self, filename: str) -> sqlite3.Connection:
        """
        Get or create a connection for a given DB filename.
        Use this instead of get_connection() inside UoW-aware code.
        """
        if self._closed:
            raise RuntimeError("UnitOfWork is already closed")

        if filename not in self._conns:
            db_path = resolve_db_path(filename, folder_path=self.folder_path)
            conn = sqlite3.connect(db_path)
            # Apply same PRAGMAs as get_connection for consistency
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.execute("PRAGMA journal_mode = WAL;")
            conn.execute("PRAGMA synchronous = NORMAL;")
            self._conns[filename] = conn

        return self._conns[filename]

    def commit(self):
        """Commit all open connections."""
        if self._closed:
            return
        for conn in self._conns.values():
            try:
                conn.commit()
            except Exception as e:
                debug_log(f"UoW commit error: {e}")
                # best-effort; caller may decide to rollback
        self._committed = True

    def rollback(self):
        """Rollback all open connections."""
        if self._closed:
            return
        for conn in self._conns.values():
            try:
                conn.rollback()
            except Exception as e:
                debug_log(f"UoW rollback error: {e}")

    def close(self):
        """Close all connections."""
        if self._closed:
            return
        for conn in self._conns.values():
            try:
                conn.close()
            except Exception as e:
                debug_log(f"UoW close error: {e}")
        self._conns.clear()
        self._closed = True

    # Context manager protocol
    def __enter__(self) -> "UnitOfWork":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # On exception -> rollback, else commit if not already done
        try:
            if exc_type is not None:
                self.rollback()
            elif not self._committed:
                self.commit()
        finally:
            self.close()
        # Do not suppress exceptions
        return False


# ============================================================================
# Schema Migration System
# ============================================================================

def init_schema_version_table(conn: sqlite3.Connection) -> None:
    """
    Initialize the schema_version table if it doesn't exist.
    
    This table tracks which migrations have been applied.
    """
    conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER PRIMARY KEY,
            description TEXT NOT NULL,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()


def get_current_schema_version(conn: sqlite3.Connection) -> int:
    """
    Get the current schema version (highest version applied).
    
    Returns 0 if no migrations have been applied yet.
    """
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(version) FROM schema_version")
        row = cursor.fetchone()
        return row[0] if row and row[0] is not None else 0
    except sqlite3.OperationalError:
        # Table doesn't exist yet
        return 0


def record_migration(conn: sqlite3.Connection, version: int, description: str) -> None:
    """
    Record that a migration has been applied.
    
    Args:
        conn: Database connection
        version: Migration version number
        description: Migration description
    """
    conn.execute(
        "INSERT INTO schema_version (version, description) VALUES (?, ?)",
        (version, description)
    )
    conn.commit()


class Migration:
    """
    Base class for database migrations.
    
    Subclass this and implement the up() method.
    
    Example:
        class Migration001_AddPatientEmail(Migration):
            version = 1
            description = "Add email column to patients table"
            
            def up(self, conn: sqlite3.Connection) -> None:
                conn.execute("ALTER TABLE patients ADD COLUMN email TEXT")
    """
    
    version: int = 0
    description: str = ""
    
    def up(self, conn: sqlite3.Connection) -> None:
        """
        Apply the migration.
        
        Args:
            conn: Database connection
        """
        raise NotImplementedError("Migration must implement up()")
    
    def down(self, conn: sqlite3.Connection) -> None:
        """
        Rollback the migration (optional, not all migrations are reversible).
        
        Args:
            conn: Database connection
        """
        raise NotImplementedError("Migration rollback not implemented")


def run_migrations(
    db_filename: str,
    migrations: list[Migration],
    folder_path: Optional[str] = None
) -> int:
    """
    Run pending migrations for a database.
    
    Args:
        db_filename: Database filename (e.g., "patients.db")
        migrations: List of Migration instances, sorted by version
        folder_path: Optional database folder path
        
    Returns:
        int: Number of migrations applied
        
    Example:
        migrations = [
            Migration001_AddPatientEmail(),
            Migration002_AddPatientPhone(),
        ]
        count = run_migrations("patients.db", migrations)
        print(f"Applied {count} migrations")
    """
    conn = get_connection(db_filename, folder_path=folder_path)
    
    try:
        # Log DB file location (helps diagnose wrong-DB issues in installed builds)
        try:
            db_list = conn.execute("PRAGMA database_list").fetchall()
            if db_list:
                # rows: (seq, name, file)
                debug_log(f"DB {db_filename}: Using file: {db_list[0][2]}")
        except Exception:
            pass

        # Initialize schema version table
        init_schema_version_table(conn)
        
        # Get current version
        current_version = get_current_schema_version(conn)
        debug_log(f"DB {db_filename}: Current schema version: {current_version}")
        
        # Sort migrations by version
        migrations_sorted = sorted(migrations, key=lambda m: m.version)
        
        # Apply pending migrations
        applied_count = 0
        for migration in migrations_sorted:
            if migration.version <= current_version:
                # Already applied
                continue
            
            debug_log(f"DB {db_filename}: Applying migration {migration.version}: {migration.description}")
            
            try:
                # Run migration
                migration.up(conn)
                
                # Record migration
                record_migration(conn, migration.version, migration.description)
                
                applied_count += 1
                debug_log(f"DB {db_filename}: Migration {migration.version} applied successfully")
                
            except Exception as e:
                debug_log(f"DB {db_filename}: Migration {migration.version} FAILED: {e}")
                conn.rollback()
                raise RuntimeError(
                    f"Migration {migration.version} failed: {e}\n"
                    f"Database is at version {current_version}. "
                    f"Please fix the migration and try again."
                ) from e
        
        if applied_count == 0:
            debug_log(f"DB {db_filename}: No pending migrations")
        else:
            debug_log(f"DB {db_filename}: Applied {applied_count} migrations successfully")
        
        return applied_count
        
    finally:
        conn.close()


def get_migration_history(
    db_filename: str,
    folder_path: Optional[str] = None
) -> list[tuple[int, str, str]]:
    """
    Get migration history for a database.
    
    Args:
        db_filename: Database filename
        folder_path: Optional database folder path
        
    Returns:
        List of (version, description, applied_at) tuples
    """
    conn = get_connection(db_filename, folder_path=folder_path)
    
    try:
        init_schema_version_table(conn)
        
        cursor = conn.cursor()
        cursor.execute("""
            SELECT version, description, applied_at
            FROM schema_version
            ORDER BY version ASC
        """)
        
        return cursor.fetchall()
        
    finally:
        conn.close()


