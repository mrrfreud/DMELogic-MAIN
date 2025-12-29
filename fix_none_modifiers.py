"""Fix 'None' string values in modifier columns."""
import sqlite3

conn = sqlite3.connect('C:/ProgramData/DMELogic/Data/orders.db')
cur = conn.cursor()

cur.execute("UPDATE order_items SET modifier1 = NULL WHERE modifier1 = 'None'")
cur.execute("UPDATE order_items SET modifier2 = NULL WHERE modifier2 = 'None'")
cur.execute("UPDATE order_items SET modifier3 = NULL WHERE modifier3 = 'None'")
cur.execute("UPDATE order_items SET modifier4 = NULL WHERE modifier4 = 'None'")

conn.commit()
print('Fixed rows:', conn.total_changes)
conn.close()
