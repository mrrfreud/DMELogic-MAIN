# Files to Upload to ChatGPT for DMELogic Analysis

## Core Application Structure (Start Here)
- `ARCHITECTURE.md` - Overall system architecture and design
- `app.py` - Main application entry point
- `app_usb.py` - USB installer entry point with first-run wizard
- `dmelogic/ui/main_window.py` - Main window and UI layout

## Domain Models (Business Logic)
- `dmelogic/domain/patient.py` - Patient domain model
- `dmelogic/domain/order.py` - Order domain model
- `dmelogic/domain/billing.py` - Billing and HCPCS codes
- `dmelogic/domain/inventory.py` - Inventory management
- `dmelogic/domain/prescriber.py` - Prescriber/doctor information
- `dmelogic/domain/insurance.py` - Insurance details

## Database & Data Access Layer
- `dmelogic/db/base.py` - Database configuration and connection
- `dmelogic/repositories/patient_repository.py` - Patient data access
- `dmelogic/repositories/order_repository.py` - Order data access
- `dmelogic/repositories/billing_repository.py` - Billing data access

## Key UI Components
- `dmelogic/ui/dialogs/order_editor_dialog.py` - Order editing interface
- `dmelogic/ui/dialogs/patient_dialog.py` - Patient editing interface
- `dmelogic/ui/theme_manager.py` - Theme and styling management
- `dmelogic/ui/dialogs/login_dialog.py` - Authentication

## Services Layer
- `dmelogic/services/order_service.py` - Order business logic
- `dmelogic/services/billing_service.py` - Billing operations
- `dmelogic/services/backup_service.py` - Database backup/restore

## Documentation (Highly Recommended)
- `DOMAIN_MODEL_COMPLETE.md` - Domain model details and relationships
- `ORDER_EDITOR_COMPLETE.md` - Order editor architecture
- `BILLING_MODIFIERS_COMPLETE.md` - Billing and modifier system
- `REFILL_SYSTEM_COMPLETE.md` - Refill tracking system
- `RENTAL_MODIFIERS_COMPLETE.md` - Rental modifier logic

## Configuration Files
- `requirements.txt` - Python dependencies
- `DMELogic.spec` - PyInstaller packaging configuration
- `installer_script.iss` - Inno Setup installer configuration
- `installer_usb.iss` - USB installer configuration

## Optional (For Specific Feature Analysis)
### Reporting
- `dmelogic/ui/reports/` - Report generation modules
- `REPORTS_DOCUMENTATION.md` - Report system documentation

### PDF & Document Processing
- `dmelogic/services/pdf_service.py` - PDF generation
- `dmelogic/ui/components/pdf_viewer.py` - PDF viewing widget

### Authentication & Security
- `dmelogic/auth/session.py` - Session management
- `dmelogic/auth/permissions.py` - Role-based permissions

### Utilities
- `dmelogic/utils/` - Utility functions
- `dmelogic/migrations/` - Database migration scripts

## Suggested Upload Strategy

### Minimal Set (Quick Overview)
1. `ARCHITECTURE.md`
2. `app.py`
3. `dmelogic/ui/main_window.py`
4. `dmelogic/domain/order.py`
5. `requirements.txt`

### Comprehensive Set (Full Understanding)
1. All files from "Core Application Structure"
2. All files from "Domain Models"
3. All files from "Documentation"
4. Key files from "Database & Data Access Layer"
5. Configuration files

### Feature-Specific Analysis
- **Order Management**: Order domain, order repository, order service, order editor dialog
- **Billing System**: Billing domain, billing repository, HCFA generation, modifier docs
- **UI/UX**: Main window, theme manager, key dialogs, UI components
- **Database**: Database base, repositories, migration scripts
- **Deployment**: PyInstaller spec, Inno Setup scripts, build scripts
