# Fax Manager Pro

Professional PDF document management system with OCR search capabilities.

## Features

- **PDF Viewing & Management**: Browse and view PDF documents with zoom, rotation, and navigation
- **OCR Text Search**: Full-text search through scanned documents using Tesseract OCR
- **Instant Search**: Fast document search with real-time highlighting
- **Document Metadata**: Store and manage document information (names, dates, notes)
- **Advanced Filtering**: Filter documents by fax numbers and date ranges
- **Auto-Backup**: Automatic backup and restore functionality
- **Dark Theme**: Modern dark interface with customizable accent colors

## System Requirements

- Windows 10 or higher
- Tesseract OCR (automatically detected from common installation paths)
- Minimum 4GB RAM
- 100MB free disk space

## Installation

1. Download and run `FaxManagerPro-Setup-1.0.0.exe`
2. Follow the installation wizard
3. Launch Fax Manager Pro from the Start Menu or Desktop

## First Time Setup

1. **Set Document Folder**: Use File → Browse Folder to select your PDF documents folder
2. **Build OCR Index**: Go to Search → Build OCR Index to enable text search
3. **Configure Settings**: Access Settings → Preferences for customization options

## Usage

### Basic Operations
- **Open Documents**: Select files from the left panel to view PDFs
- **Search Content**: Use the search box to find text within documents
- **Add Metadata**: Fill in document information in the right panel
- **Navigate Pages**: Use toolbar buttons or keyboard shortcuts

### OCR Search
- **Build Index**: Search → Build OCR Index (one-time setup)
- **Search Text**: Type search terms in the search box
- **View Results**: Click search results to open matching documents
- **Filter Results**: Use fax number and date filters to narrow results

### Keyboard Shortcuts
- `Ctrl+F`: Open search
- `Ctrl+O`: Browse folder
- `F5`: Refresh file list
- `Ctrl++`: Zoom in
- `Ctrl+-`: Zoom out
- `Ctrl+0`: Fit width
- `Page Up/Down`: Navigate pages

## Troubleshooting

### OCR Not Working
- Install Tesseract OCR from: https://github.com/tesseract-ocr/tesseract
- Ensure Tesseract is in your system PATH
- Restart the application after installing Tesseract

### Search Not Finding Results
- Build the OCR index first: Search → Build OCR Index
- Wait for indexing to complete (progress shown in status bar)
- Try different search terms or check document content

### Performance Issues
- Close other applications to free memory
- Process fewer documents at once during indexing
- Consider upgrading system RAM for large document collections

## Support

For technical support or feature requests, please contact:
- Email: support@yourcompany.com
- Website: https://yourwebsite.com/support

## License

Copyright © 2025 Your Company Name. All rights reserved.

This software is provided "as-is" without warranty of any kind.