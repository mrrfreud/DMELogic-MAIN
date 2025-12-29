import sqlite3

conn = sqlite3.connect(r'C:\FaxManagerData\Data\patients.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Check ABREU patients
cur.execute("""
    SELECT id, first_name, last_name, primary_insurance, policy_number, 
           secondary_insurance, secondary_insurance_id, group_number
    FROM patients 
    WHERE last_name = 'ABREU'
    ORDER BY first_name
    LIMIT 5
""")

rows = cur.fetchall()
print(f"\nFound {len(rows)} ABREU patients:\n")

for row in rows:
    print(f"ID: {row['id']}")
    print(f"  Name: {row['first_name']} {row['last_name']}")
    print(f"  Primary Insurance: {row['primary_insurance'] or 'None'}")
    print(f"  Policy Number: {row['policy_number'] or 'None'}")
    print(f"  Group Number: {row['group_number'] or 'None'}")
    print(f"  Secondary Insurance: {row['secondary_insurance'] or 'None'}")
    print(f"  Secondary ID: {row['secondary_insurance_id'] or 'None'}")
    print()

conn.close()
