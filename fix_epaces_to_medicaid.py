import sqlite3
import shutil

# Backup first
shutil.copy(
    r'C:\FaxManagerData\Data\patients.db',
    r'C:\FaxManagerData\Data\patients.db.backup5'
)
print("✅ Backup created: patients.db.backup5")

# Connect and update
conn = sqlite3.connect(r'C:\FaxManagerData\Data\patients.db')
cur = conn.cursor()

# Update primary insurance
cur.execute("UPDATE patients SET primary_insurance = 'MEDICAID' WHERE primary_insurance = 'EPACES'")
primary_count = cur.rowcount

# Update secondary insurance
cur.execute("UPDATE patients SET secondary_insurance = 'MEDICAID' WHERE secondary_insurance = 'EPACES'")
secondary_count = cur.rowcount

conn.commit()

print(f"✅ Updated {primary_count} primary + {secondary_count} secondary = {primary_count + secondary_count} total records")
print("✅ All 'EPACES' entries changed to 'MEDICAID'")

# Verify
cur.execute("SELECT COUNT(*) FROM patients WHERE primary_insurance = 'EPACES' OR secondary_insurance = 'EPACES'")
remaining = cur.fetchone()[0]
print(f"✅ Remaining EPACES entries: {remaining}")

conn.close()
