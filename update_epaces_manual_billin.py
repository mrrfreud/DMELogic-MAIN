"""
Update insurance names in patients database:
- "EPACES MANUAL BILLIN DME" → "EPACES"
"""
import sqlite3
import shutil
from pathlib import Path

DB_PATH = r'C:\FaxManagerData\Data\patients.db'

def backup_database():
    """Create backup before making changes."""
    backup_path = Path(DB_PATH).with_suffix('.db.backup3')
    shutil.copy2(DB_PATH, backup_path)
    print(f"✅ Backup created: {backup_path}")
    return backup_path

def preview_changes():
    """Show what will be changed."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    print("\n" + "="*70)
    print("PREVIEW: Records that will be updated")
    print("="*70)
    
    # Check primary insurance
    cur.execute("""
        SELECT id, first_name, last_name, primary_insurance, policy_number
        FROM patients 
        WHERE primary_insurance = 'EPACES MANUAL BILLIN DME'
        ORDER BY last_name, first_name
    """)
    primary_records = cur.fetchall()
    
    if primary_records:
        print(f"\n📋 PRIMARY INSURANCE ({len(primary_records)} patients):")
        for rec in primary_records:
            print(f"  ID {rec[0]:4} | {rec[2]}, {rec[1]:20} | {rec[3]:30} → EPACES | Policy: {rec[4] or 'None'}")
    
    # Check secondary insurance
    cur.execute("""
        SELECT id, first_name, last_name, secondary_insurance, secondary_insurance_id
        FROM patients 
        WHERE secondary_insurance = 'EPACES MANUAL BILLIN DME'
        ORDER BY last_name, first_name
    """)
    secondary_records = cur.fetchall()
    
    if secondary_records:
        print(f"\n📋 SECONDARY INSURANCE ({len(secondary_records)} patients):")
        for rec in secondary_records:
            print(f"  ID {rec[0]:4} | {rec[2]}, {rec[1]:20} | {rec[3]:30} → EPACES | Policy: {rec[4] or 'None'}")
    
    total = len(primary_records) + len(secondary_records)
    print(f"\n{'='*70}")
    print(f"TOTAL RECORDS TO UPDATE: {total}")
    print(f"{'='*70}\n")
    
    conn.close()
    return total

def apply_updates():
    """Apply the insurance name updates."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    print("\n🔄 Applying updates...")
    
    # Update primary insurance
    cur.execute("""
        UPDATE patients 
        SET primary_insurance = 'EPACES'
        WHERE primary_insurance = 'EPACES MANUAL BILLIN DME'
    """)
    primary_updated = cur.rowcount
    
    # Update secondary insurance
    cur.execute("""
        UPDATE patients 
        SET secondary_insurance = 'EPACES'
        WHERE secondary_insurance = 'EPACES MANUAL BILLIN DME'
    """)
    secondary_updated = cur.rowcount
    
    conn.commit()
    conn.close()
    
    print(f"✅ Updated {primary_updated} primary insurance records")
    print(f"✅ Updated {secondary_updated} secondary insurance records")
    print(f"✅ Total: {primary_updated + secondary_updated} records updated")

def verify_updates():
    """Verify the changes were applied."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    print("\n🔍 Verifying updates...")
    
    # Check if old names still exist
    cur.execute("""
        SELECT COUNT(*) FROM patients 
        WHERE primary_insurance = 'EPACES MANUAL BILLIN DME'
           OR secondary_insurance = 'EPACES MANUAL BILLIN DME'
    """)
    remaining = cur.fetchone()[0]
    
    if remaining == 0:
        print("✅ All old insurance names have been updated")
    else:
        print(f"⚠️  Warning: {remaining} records still have old names")
    
    # Count new EPACES entries
    cur.execute("SELECT COUNT(*) FROM patients WHERE primary_insurance = 'EPACES'")
    primary_epaces = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM patients WHERE secondary_insurance = 'EPACES'")
    secondary_epaces = cur.fetchone()[0]
    
    print(f"📊 Current EPACES counts:")
    print(f"   Primary: {primary_epaces} patients")
    print(f"   Secondary: {secondary_epaces} patients")
    
    conn.close()

if __name__ == "__main__":
    print("\n" + "="*70)
    print("INSURANCE NAME UPDATE UTILITY - EPACES MANUAL BILLIN DME")
    print("="*70)
    
    # Preview
    total = preview_changes()
    
    if total == 0:
        print("✅ No records need updating. All insurance names are already correct.")
    else:
        # Ask for confirmation
        response = input("\n⚠️  Proceed with updates? (yes/no): ").strip().lower()
        
        if response == 'yes':
            # Backup
            backup_path = backup_database()
            
            # Apply
            apply_updates()
            
            # Verify
            verify_updates()
            
            print("\n✅ Update complete!")
            print(f"   Backup saved at: {backup_path}")
        else:
            print("\n❌ Update cancelled. No changes made.")
