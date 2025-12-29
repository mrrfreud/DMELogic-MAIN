# 📊 Inventory Reports & Analytics System

## Overview
Comprehensive reporting system for inventory management with 11 different report types organized into 3 categories: Inventory Control, Financial Analysis, and Performance Metrics.

## How to Access
1. Navigate to the **Inventory Management** tab
2. Click the **📊 Generate Reports** button in the toolbar
3. Select a report category and type
4. Click **🔍 Generate** to view the report

## Report Categories

### 📦 1. Inventory Control Reports
Help prevent stockouts and manage reordering.

#### Low Stock / Reorder Report
- **Purpose**: Shows all items where STOCK ≤ REORDER LEVEL
- **Key Columns**: ITEM ID, HCPCS CODE, DESCRIPTION, CATEGORY, STOCK, REORDER LEVEL, SOURCE
- **Highlights**: 
  - 🚨 Red background for items with 0 stock
  - ⚠️ Yellow background for items at or below reorder level
- **Use Case**: Daily monitoring to prevent stockouts

#### Out-of-Stock Report
- **Purpose**: Lists items that are completely depleted (STOCK = 0)
- **Key Columns**: ITEM ID, HCPCS CODE, DESCRIPTION, CATEGORY, REORDER LEVEL, SOURCE
- **Highlights**: All items shown in critical red
- **Use Case**: Immediate action required - cannot fulfill orders for these items

#### Reorder Summary by Vendor
- **Purpose**: Groups low-stock items by SOURCE (supplier) for efficient purchase orders
- **Key Columns**: SOURCE/VENDOR, ITEMS TO REORDER, TOTAL UNITS NEEDED, ITEMS LIST
- **Calculations**: 
  - Items to reorder: Count of items needing restocking per vendor
  - Total units needed: Sum of (reorder_level - current_stock)
- **Use Case**: Create consolidated purchase orders by supplier

#### Stock Level Overview
- **Purpose**: Snapshot of ALL stock levels with color-coded status
- **Key Columns**: ITEM ID, HCPCS CODE, DESCRIPTION, CATEGORY, STOCK, REORDER LEVEL, STATUS
- **Status Categories**:
  - 🚨 **OUT OF STOCK** (red): Stock = 0
  - ⚠️ **LOW STOCK** (yellow): Stock ≤ Reorder Level
  - 📦 **MODERATE** (blue): Stock ≤ Reorder Level × 1.5
  - ✅ **GOOD** (green): Stock > Reorder Level × 1.5
- **Use Case**: High-level inventory health dashboard

---

### 💰 2. Financial Analysis Reports
For cost analysis, billing comparisons, and profit tracking.

#### Inventory Value Report
- **Purpose**: Calculates total cost value of inventory on hand
- **Key Columns**: ITEM ID, HCPCS CODE, DESCRIPTION, CATEGORY, UNIT COST, STOCK QTY, TOTAL VALUE
- **Calculation**: COST × STOCK for each item
- **Summary**: Total inventory value, average item value
- **Use Case**: Track invested capital, balance sheet reporting

#### Potential Revenue Report
- **Purpose**: Calculates potential revenue if all current stock sold at full price
- **Key Columns**: ITEM ID, HCPCS CODE, DESCRIPTION, CATEGORY, BILL AMOUNT, STOCK QTY, POTENTIAL REVENUE, UNIT COST, POTENTIAL PROFIT
- **Calculations**:
  - Potential Revenue: BILL AMOUNT × STOCK
  - Potential Profit: (BILL AMOUNT - COST) × STOCK
  - Profit Margin: Profit / Revenue × 100
- **Use Case**: Understand maximum revenue potential and profit margins

#### Gross Margin by Item
- **Purpose**: Shows profitability and margin percentage for each item
- **Key Columns**: ITEM ID, HCPCS CODE, DESCRIPTION, CATEGORY, COST, BILL AMOUNT, GROSS PROFIT, MARGIN %, STOCK
- **Calculations**:
  - Gross Profit: BILL AMOUNT - COST
  - Margin %: (Profit / BILL AMOUNT) × 100
- **Color Coding**:
  - 🟢 Green: ≥50% margin (excellent)
  - 🔵 Blue: 30-49% margin (good)
  - 🟡 Yellow: 15-29% margin (moderate)
  - 🔴 Red: <15% margin (low profitability)
- **Use Case**: Identify most/least profitable items, pricing strategy

#### Category Profit Breakdown
- **Purpose**: Groups items by CATEGORY to show which product lines are most profitable
- **Key Columns**: CATEGORY, ITEM COUNT, TOTAL STOCK, AVG COST, AVG BILL, AVG PROFIT, AVG MARGIN %, TOTAL INVESTED, POTENTIAL REVENUE
- **Calculations**:
  - All averages calculated per category
  - Total Invested: Sum of (COST × STOCK) for category
  - Potential Revenue: Sum of (BILL AMOUNT × STOCK) for category
- **Use Case**: Strategic decisions on which categories to expand/reduce

---

### 📈 3. Performance Metrics Reports
Track supplier, brand, and product performance.

#### Top Suppliers by Stock Volume
- **Purpose**: Identifies suppliers with the most items and stock in inventory
- **Key Columns**: SUPPLIER/SOURCE, ITEM COUNT, TOTAL STOCK, TOTAL VALUE, AVG MARGIN %, CATEGORIES
- **Calculations**:
  - Total Stock: Sum of all units from this supplier
  - Total Value: Sum of (COST × STOCK) for supplier's items
  - Categories: List of all product categories from this supplier
- **Use Case**: Evaluate supplier relationships, identify diversification opportunities

#### Top Brands by Sales Margin
- **Purpose**: Ranks brands based on profit potential and margins
- **Key Columns**: BRAND, ITEM COUNT, TOTAL STOCK, AVG PROFIT/UNIT, AVG MARGIN %, TOTAL PROFIT POTENTIAL
- **Calculations**:
  - Avg Profit/Unit: Average of (BILL AMOUNT - COST) per brand
  - Total Profit Potential: Sum of ((BILL AMOUNT - COST) × STOCK)
- **Sorted By**: Average margin % (highest to lowest)
- **Use Case**: Focus marketing and stocking on high-margin brands

#### Slow-Moving Items Report
- **Purpose**: Lists items that haven't been used recently or never used
- **Key Columns**: ITEM ID, HCPCS CODE, DESCRIPTION, CATEGORY, STOCK, UNIT COST, TIED-UP VALUE, USAGE STATUS
- **Data Source**: Uses `last_used_date` from inventory tracking
- **Calculations**:
  - Tied-Up Value: COST × STOCK (capital locked in slow items)
  - Usage Status: "Never used" or "Last used: [date]"
- **Sorting**: Never-used items first, then oldest last_used_date
- **Highlights**: Yellow background for never-used items
- **Use Case**: Free up capital by discounting/returning slow-moving inventory

---

## Export Options

### 💾 Export to CSV
- Creates a comma-separated values file
- Includes all column headers and data
- Filename format: `{Report_Name}_{YYYYMMDD_HHMMSS}.csv`
- Compatible with Excel, Google Sheets, and all spreadsheet software

### 📊 Export to Excel
- Creates a formatted Excel workbook (.xlsx)
- Features:
  - Bold white headers on blue background
  - Auto-sized columns (15 units wide)
  - Data formatting preserved
- **Requirements**: `openpyxl` library
  - Install with: `pip install openpyxl`
- Filename format: `{Report_Name}_{YYYYMMDD_HHMMSS}.xlsx`

---

## Summary Statistics
Each report displays context-specific summary information:
- **Counts**: Total items, items in each status category
- **Financial Totals**: Total values, revenues, profits, margins
- **Actionable Insights**: Recommended next steps based on report data

---

## Color Coding System

### Status Colors
- 🔴 **Red (#f8d7da)**: Critical/Out of stock/Low margin (<15%)
- 🟡 **Yellow (#fff3cd)**: Warning/Low stock/Moderate margin (15-29%)
- 🔵 **Blue (#d1ecf1)**: Moderate stock/Good margin (30-49%)
- 🟢 **Green (#d4edda)**: Good stock/Excellent margin (≥50%)

---

## Database Queries

All reports query the `inventory` table with these key fields:
- `item_id`, `hcpcs_code`, `description`, `category`
- `cost`, `retail_price` (for financial calculations)
- `brand`, `supplier` (for grouping)
- `stock_quantity`, `reorder_level` (for stock management)
- `last_used_date`, `last_restocked_date` (for tracking)

---

## Use Cases by Role

### **Inventory Manager**
- Daily: Low Stock Report, Out-of-Stock Report
- Weekly: Stock Level Overview, Reorder Summary by Vendor
- Monthly: Slow-Moving Items Report

### **Financial Controller**
- Monthly: Inventory Value Report, Potential Revenue Report
- Quarterly: Gross Margin by Item, Category Profit Breakdown

### **Purchasing Manager**
- Weekly: Reorder Summary by Vendor, Top Suppliers Report
- Monthly: Slow-Moving Items (for returns/discounts)

### **Sales Manager**
- Monthly: Top Brands by Sales Margin, Category Profit Breakdown
- Quarterly: Gross Margin by Item (pricing strategy)

---

## Best Practices

1. **Daily Monitoring**: Check Low Stock Report each morning to prevent stockouts
2. **Weekly Ordering**: Use Reorder by Vendor report to consolidate purchase orders
3. **Monthly Analysis**: Review financial reports to optimize pricing and inventory mix
4. **Quarterly Cleanup**: Use Slow-Moving Items report to free up capital
5. **Export for Records**: Save monthly reports to Excel for historical tracking

---

## Technical Details

### Performance
- All queries optimized with proper indexing
- Reports generate in under 1 second for databases with <10,000 items
- Color coding applied at display time (no database overhead)

### Data Accuracy
- Real-time data from inventory database
- Stock calculations use current values
- Financial calculations use actual cost and retail price fields

### Integration
- Seamlessly integrated into main application
- No separate database or data export required
- Works with existing inventory tracking system

---

## Troubleshooting

### "No data to display"
- Check that inventory items exist in database
- Verify items have appropriate values (stock, cost, prices)
- Some reports filter by criteria (e.g., Low Stock only shows items needing reorder)

### Excel export fails
- Install openpyxl: `pip install openpyxl`
- Use CSV export as alternative

### Calculations seem incorrect
- Verify cost and retail_price are entered correctly for items
- Check that stock_quantity and reorder_level are set
- Null values treated as 0 in calculations

---

## Future Enhancements (Possible)
- Date range filters for historical analysis
- Scheduled report generation and email delivery
- Custom report builder with field selection
- Chart visualizations (bar, pie, line graphs)
- Comparison reports (this month vs last month)

---

*For support or questions, refer to the main application documentation.*
