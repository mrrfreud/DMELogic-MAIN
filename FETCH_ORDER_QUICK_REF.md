# Quick Reference: Order Fetching

## Import Once

```python
from dmelogic.db import (
    fetch_order_with_items,
    build_state_portal_json_for_order,
    build_state_portal_csv_row_for_order,
)
```

## Basic Patterns

### 1. Fetch Order for Display
```python
order = fetch_order_with_items(order_id, folder_path=self.current_folder)
if not order:
    self.show_error("Order not found")
    return

# Use rich domain model
print(f"Patient: {order.patient_full_name}")
print(f"Status: {order.order_status.value}")
print(f"ICD Codes: {', '.join(order.icd_codes)}")

for item in order.items:
    print(f"{item.hcpcs_code}: {item.description} x{item.quantity}")
```

### 2. Export to State Portal (JSON)
```python
try:
    json_data = build_state_portal_json_for_order(
        order_id,
        folder_path=self.current_folder
    )
    
    # POST to API
    response = requests.post(API_URL, json=json_data)
    response.raise_for_status()
    
except ValueError as e:
    self.show_error(f"Order not found: {e}")
```

### 3. Batch CSV Export
```python
import csv

with open(output_file, 'w', newline='') as f:
    writer = csv.writer(f)
    
    for order_id in selected_order_ids:
        try:
            row = build_state_portal_csv_row_for_order(
                order_id,
                folder_path=self.current_folder
            )
            writer.writerow(row)
        except ValueError:
            continue  # Skip missing orders
```

## Replace Old Patterns

### ❌ OLD: Raw SQL Everywhere
```python
# DON'T DO THIS ANYMORE
conn = get_connection("orders.db")
cur = conn.cursor()
cur.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
order_row = cur.fetchone()

cur.execute("SELECT * FROM order_items WHERE order_id = ?", (order_id,))
items = cur.fetchall()

# Parse each field manually...
patient_name = f"{order_row['patient_last_name']}, {order_row['patient_first_name']}"
```

### ✅ NEW: Clean Repository Access
```python
# DO THIS INSTEAD
order = fetch_order_with_items(order_id, folder_path)
patient_name = order.patient_full_name  # Property!
items = order.items  # Already populated!
```

## Order Model Quick Reference

```python
order.id                              # int
order.patient_full_name               # str (property)
order.patient_dob_at_order_time       # date
order.prescriber_name_at_order_time   # str
order.prescriber_npi_at_order_time    # str
order.order_status                    # OrderStatus enum
order.order_status.value              # str (e.g., "Ready")
order.icd_codes                       # list[str] (property)
order.items                           # list[OrderItem]
order.has_diagnosis_codes             # bool (property)
order.order_total                     # Decimal (property)
```

## OrderItem Model Quick Reference

```python
item.id            # int
item.hcpcs_code    # str
item.description   # str
item.quantity      # int
item.refills       # int
item.days_supply   # int
item.cost_ea       # Decimal | None
item.total_cost    # Decimal | None
item.directions    # str | None
```

## Common Use Cases

### Display Order in Table
```python
def refresh_orders_table(self):
    for order_id in self.get_visible_order_ids():
        order = fetch_order_with_items(order_id, self.current_folder)
        if order:
            self.table.addRow([
                str(order.id),
                order.patient_full_name,
                order.order_status.value,
                str(len(order.items)),
                order.order_date.strftime("%m/%d/%Y") if order.order_date else "",
            ])
```

### Check Order Status
```python
order = fetch_order_with_items(order_id, folder_path)

if order.order_status == OrderStatus.READY:
    self.enable_delivery_button()
elif order.order_status == OrderStatus.DELIVERED:
    self.enable_billing_button()
```

### Calculate Order Total
```python
order = fetch_order_with_items(order_id, folder_path)

# Use computed property
total = order.order_total

# Or manually
total = sum(item.total_cost or Decimal("0") for item in order.items)
```

### Export Multiple Formats
```python
def export_order(self, order_id: int, format: str):
    if format == "json":
        data = build_state_portal_json_for_order(order_id, self.current_folder)
        with open(f"order_{order_id}.json", "w") as f:
            json.dump(data, f, indent=2)
    
    elif format == "csv":
        row = build_state_portal_csv_row_for_order(order_id, self.current_folder)
        with open(f"order_{order_id}.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(row)
```

## Within Transactions

```python
from dmelogic.db import UnitOfWork, fetch_order_with_items

with UnitOfWork("orders.db", folder_path=folder_path) as uow:
    # Fetch within transaction
    order = fetch_order_with_items(
        order_id,
        conn=uow.conn  # Reuse connection!
    )
    
    # Make changes
    order.order_status = OrderStatus.DELIVERED
    
    # Save changes
    uow.execute("UPDATE orders SET order_status = ? WHERE id = ?",
                (order.order_status.value, order.id))
    
    # Auto-commits if no exception
```

## Error Handling

```python
def safe_fetch_order(self, order_id: int) -> Optional[Order]:
    """Fetch order with error handling."""
    try:
        order = fetch_order_with_items(
            order_id,
            folder_path=self.current_folder
        )
        
        if not order:
            self.show_warning(f"Order {order_id} not found")
            return None
        
        return order
        
    except Exception as e:
        self.show_error(f"Error loading order: {e}")
        return None
```

## Performance Tips

### ✅ DO: Fetch once, use many times
```python
# Good - single fetch
order = fetch_order_with_items(order_id, folder_path)
self.update_ui(order)
self.log_audit(order)
self.check_authorization(order)
```

### ❌ DON'T: Fetch repeatedly
```python
# Bad - multiple fetches
self.update_ui(fetch_order_with_items(order_id, folder_path))
self.log_audit(fetch_order_with_items(order_id, folder_path))
self.check_authorization(fetch_order_with_items(order_id, folder_path))
```

### ✅ DO: Use within transactions for consistency
```python
with UnitOfWork("orders.db", folder_path=folder_path) as uow:
    order = fetch_order_with_items(order_id, conn=uow.conn)
    # All data consistent within transaction
```

## Migration Checklist

- [ ] Replace `SELECT * FROM orders WHERE id = ?` with `fetch_order_with_items()`
- [ ] Replace `SELECT * FROM order_items WHERE order_id = ?` with `order.items`
- [ ] Replace manual patient name parsing with `order.patient_full_name`
- [ ] Replace ICD code parsing with `order.icd_codes` property
- [ ] Replace state portal SQL with `build_state_portal_json_for_order()`
- [ ] Update exports to use service layer functions
- [ ] Add type hints using `Order` and `OrderItem` types

## Questions?

See `FETCH_ORDER_INTEGRATION.md` for full documentation or run `demo_domain_integration.py` for working examples.
