import sqlite3

conn = sqlite3.connect(r'C:\FaxManagerData\Data\patients.db')
cur = conn.cursor()

# Check primary insurance
cur.execute('''
    SELECT primary_insurance, COUNT(*) 
    FROM patients 
    WHERE primary_insurance IN ('EPACES', 'EPACES MANUAL BILLIN DME', 'MEDICAID', 'MEDICAID FOR DME ITEMS')
    GROUP BY primary_insurance
''')
print('Primary Insurance:')
for row in cur.fetchall():
    print(f'  {row[0]}: {row[1]}')

# Check secondary insurance
cur.execute('''
    SELECT secondary_insurance, COUNT(*) 
    FROM patients 
    WHERE secondary_insurance IN ('EPACES', 'EPACES MANUAL BILLIN DME', 'MEDICAID', 'MEDICAID FOR DME ITEMS')
    GROUP BY secondary_insurance
''')
print('\nSecondary Insurance:')
for row in cur.fetchall():
    print(f'  {row[0]}: {row[1]}')

conn.close()
