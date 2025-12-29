"""
Database Sync Utility
=====================
Copies databases from development to installed app location.

Run this after making changes in development to sync to the installed app.
"""

import os
import shutil
from pathlib import Path

# Development database location (actual location used by running app.py)
DEV_DB_PATH = r"C:\FaxManagerData\Data"

# Installed app database location (from installer)
INSTALLED_DB_PATH = r"C:\ProgramData\DMELogic\Data"

# Database files to sync
DB_FILES = [
    "patients.db",
    "orders.db",
    "prescribers.db",
    "inventory.db",
    "billing.db",
    "suppliers.db",
    "insurance_names.db",
    "insurance.db",
    "document_data.db",
]


def sync_dev_to_installed():
    """Copy databases from dev to installed app."""
    dev_path = Path(DEV_DB_PATH)
    installed_path = Path(INSTALLED_DB_PATH)
    
    if not dev_path.exists():
        print(f"❌ Development database path not found: {dev_path}")
        return False
    
    # Create installed path if it doesn't exist
    installed_path.mkdir(parents=True, exist_ok=True)
    
    print(f"📂 Syncing from: {dev_path}")
    print(f"📂 Syncing to:   {installed_path}")
    print()
    
    synced = 0
    for db_file in DB_FILES:
        source = dev_path / db_file
        dest = installed_path / db_file
        
        if source.exists():
            try:
                # Backup existing file if it exists
                if dest.exists():
                    backup = installed_path / f"{db_file}.backup"
                    shutil.copy2(dest, backup)
                    print(f"💾 Backed up: {db_file} -> {db_file}.backup")
                
                # Copy the file
                shutil.copy2(source, dest)
                print(f"✅ Synced: {db_file}")
                synced += 1
            except Exception as e:
                print(f"❌ Failed to sync {db_file}: {e}")
        else:
            print(f"⚠️  Skipped: {db_file} (not found in dev)")
    
    print()
    print(f"🎉 Sync complete! {synced}/{len(DB_FILES)} databases synced.")
    return True


def sync_installed_to_dev():
    """Copy databases from installed app to dev (reverse sync)."""
    dev_path = Path(DEV_DB_PATH)
    installed_path = Path(INSTALLED_DB_PATH)
    
    if not installed_path.exists():
        print(f"❌ Installed database path not found: {installed_path}")
        return False
    
    # Create dev path if it doesn't exist
    dev_path.mkdir(parents=True, exist_ok=True)
    
    print(f"📂 Syncing from: {installed_path}")
    print(f"📂 Syncing to:   {dev_path}")
    print()
    
    synced = 0
    for db_file in DB_FILES:
        source = installed_path / db_file
        dest = dev_path / db_file
        
        if source.exists():
            try:
                # Backup existing file if it exists
                if dest.exists():
                    backup = dev_path / f"{db_file}.backup"
                    shutil.copy2(dest, backup)
                    print(f"💾 Backed up: {db_file} -> {db_file}.backup")
                
                # Copy the file
                shutil.copy2(source, dest)
                print(f"✅ Synced: {db_file}")
                synced += 1
            except Exception as e:
                print(f"❌ Failed to sync {db_file}: {e}")
        else:
            print(f"⚠️  Skipped: {db_file} (not found in installed)")
    
    print()
    print(f"🎉 Sync complete! {synced}/{len(DB_FILES)} databases synced.")
    return True


def show_status():
    """Show current database locations and what exists."""
    dev_path = Path(DEV_DB_PATH)
    installed_path = Path(INSTALLED_DB_PATH)
    
    print("=" * 60)
    print("DATABASE STATUS")
    print("=" * 60)
    print()
    
    print(f"📂 Development Path: {dev_path}")
    print(f"   Exists: {'✅ Yes' if dev_path.exists() else '❌ No'}")
    if dev_path.exists():
        dev_dbs = [f for f in DB_FILES if (dev_path / f).exists()]
        print(f"   Databases: {len(dev_dbs)}/{len(DB_FILES)}")
        for db in dev_dbs:
            size = (dev_path / db).stat().st_size / 1024
            print(f"      • {db} ({size:.1f} KB)")
    print()
    
    print(f"📂 Installed Path: {installed_path}")
    print(f"   Exists: {'✅ Yes' if installed_path.exists() else '❌ No'}")
    if installed_path.exists():
        inst_dbs = [f for f in DB_FILES if (installed_path / f).exists()]
        print(f"   Databases: {len(inst_dbs)}/{len(DB_FILES)}")
        for db in inst_dbs:
            size = (installed_path / db).stat().st_size / 1024
            print(f"      • {db} ({size:.1f} KB)")
    print()


def main():
    """Interactive menu."""
    while True:
        print("=" * 60)
        print("DATABASE SYNC UTILITY")
        print("=" * 60)
        print()
        print("1. Show database status")
        print("2. Sync DEV → INSTALLED (copy dev databases to installed app)")
        print("3. Sync INSTALLED → DEV (copy installed databases to dev)")
        print("4. Exit")
        print()
        
        choice = input("Choose an option (1-4): ").strip()
        print()
        
        if choice == "1":
            show_status()
        elif choice == "2":
            confirm = input("⚠️  This will overwrite installed app databases. Continue? (yes/no): ").strip().lower()
            if confirm == "yes":
                sync_dev_to_installed()
            else:
                print("❌ Sync cancelled.")
        elif choice == "3":
            confirm = input("⚠️  This will overwrite dev databases. Continue? (yes/no): ").strip().lower()
            if confirm == "yes":
                sync_installed_to_dev()
            else:
                print("❌ Sync cancelled.")
        elif choice == "4":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please choose 1-4.")
        
        print()
        input("Press Enter to continue...")
        print("\n" * 2)


if __name__ == "__main__":
    main()
