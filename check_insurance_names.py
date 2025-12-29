import sqlite3

conn = sqlite3.connect(r'C:\FaxManagerData\Data\patients.db')
cur = conn.cursor()

# Get distinct primary insurance values
cur.execute('SELECT DISTINCT primary_insurance FROM patients WHERE primary_insurance IS NOT NULL')
primaries = [row[0] for row in cur.fetchall()]

print('PRIMARY INSURANCE VALUES:')
print('=' * 60)
for p in sorted(primaries):
    # Count how many patients have this
    cur.execute('SELECT COUNT(*) FROM patients WHERE primary_insurance = ?', (p,))
    count = cur.fetchone()[0]
    print(f'  {p:40} ({count} patients)')

# Get distinct secondary insurance values
cur.execute('SELECT DISTINCT secondary_insurance FROM patients WHERE secondary_insurance IS NOT NULL')
secondaries = [row[0] for row in cur.fetchall()]

print('\nSECONDARY INSURANCE VALUES:')
print('=' * 60)
for s in sorted(secondaries):
    cur.execute('SELECT COUNT(*) FROM patients WHERE secondary_insurance = ?', (s,))
    count = cur.fetchone()[0]
    print(f'  {s:40} ({count} patients)')

# Check for the specific ones you mentioned
print('\n\nTARGETED INSURANCE TO RENAME:')
print('=' * 60)
targets = ['MEDICAID FOR DME ITEMS', 'EPACES']
for target in targets:
    cur.execute('SELECT COUNT(*) FROM patients WHERE primary_insurance = ? OR secondary_insurance = ?', (target, target))
    count = cur.fetchone()[0]
    print(f'  {target:40} ({count} patients)')

conn.close()
