"""
DocumentViewer - PDF Viewer Component

Handles PDF rendering with caching and async loading.

Threading Safety:
- Uses cancellation flags instead of QThread.terminate() for safe shutdown
- Old renders are ignored if page/zoom changed (prevents display glitches)
- Worker threads complete naturally without forced termination
- PyMuPDF and Qt state remain consistent even during rapid navigation

Performance:
- LRU cache (256MB default) for rendered pages
- Async rendering doesn't block UI
- Smart cache invalidation on zoom changes
"""

import os
from PyQt6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QWidget, QVBoxLayout
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject, QRectF
from PyQt6.QtGui import QPixmap, QImage, QPainter, QTransform
from PyQt6.QtPrintSupport import QPrinter
from collections import OrderedDict
import fitz  # PyMuPDF


class PdfRenderWorker(QThread):
    """
    Worker thread for rendering PDF pages asynchronously.
    
    Uses a cancellation flag instead of terminate() for safe shutdown.
    """
    finished = pyqtSignal(int, QPixmap)  # page_num, pixmap

    def __init__(self, doc, page_num, zoom, rotation=0):
        super().__init__()
        self.doc = doc
        self.page_num = page_num
        self.zoom = zoom
        self.rotation = rotation  # Rotation in degrees (0, 90, 180, 270)
        self._cancelled = False

    def cancel(self):
        """Request cancellation of this render operation."""
        self._cancelled = True

    def run(self):
        """Render the PDF page in a background thread."""
        try:
            if self._cancelled:
                return
            
            if not self.doc or self.page_num < 0 or self.page_num >= len(self.doc):
                return

            page = self.doc[self.page_num]
            
            # Calculate zoom + rotation matrix (non-destructive)
            mat = fitz.Matrix(self.zoom, self.zoom)
            if self.rotation:
                mat = mat.preRotate(self.rotation)
            
            # Check cancellation before expensive operation
            if self._cancelled:
                return
            
            # Render page to pixmap
            pix = page.get_pixmap(matrix=mat, alpha=False)
            
            # Check cancellation before Qt operations
            if self._cancelled:
                return
            
            # Convert to QImage (safe: copy buffer into QImage's memory)
            img = QImage(pix.width, pix.height, QImage.Format.Format_RGB888)
            img.bits()[:] = pix.samples  # Copy data to QImage's own buffer
            
            # Convert to QPixmap (now safe even if pix goes out of scope)
            pixmap = QPixmap.fromImage(img)
            
            # Final cancellation check before emitting
            if not self._cancelled:
                self.finished.emit(self.page_num, pixmap)
            
        except Exception as e:
            if not self._cancelled:
                print(f"Error rendering page {self.page_num}: {e}")
                import traceback
                traceback.print_exc()


class LRUCache:
    """Simple LRU cache for rendered pages."""
    
    def __init__(self, max_size_mb=256):
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.cache = OrderedDict()
        self.current_size = 0
    
    def get(self, key):
        if key in self.cache:
            # Move to end (most recently used)
            self.cache.move_to_end(key)
            return self.cache[key]
        return None
    
    def put(self, key, pixmap):
        # Remove if already exists
        if key in self.cache:
            old_pixmap = self.cache.pop(key)
            self.current_size -= self._pixmap_size(old_pixmap)
        
        # Add new item
        self.cache[key] = pixmap
        self.current_size += self._pixmap_size(pixmap)
        
        # Evict oldest items if over size limit
        while self.current_size > self.max_size_bytes and len(self.cache) > 1:
            oldest_key, oldest_pixmap = self.cache.popitem(last=False)
            self.current_size -= self._pixmap_size(oldest_pixmap)
    
    def clear(self):
        self.cache.clear()
        self.current_size = 0
    
    def _pixmap_size(self, pixmap):
        """Estimate pixmap size in bytes."""
        if pixmap and not pixmap.isNull():
            return pixmap.width() * pixmap.height() * 4  # RGBA
        return 0


class DocumentViewer(QWidget):
    """PDF viewer widget with rendering and navigation."""
    
    # Define signals
    pageChanged = pyqtSignal(int)  # Emits current page number
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pdf_doc = None
        self.current_page = 0
        self.total_pages = 0
        self.zoom_level = 1.0
        self.rotation = 0  # Current rotation in degrees (0, 90, 180, 270)
        self.cache = LRUCache(max_size_mb=256)
        self.render_worker = None
        self._pending_render = None  # Track pending render request
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Initialize the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Graphics view for displaying PDF
        self.view = QGraphicsView()
        self.scene = QGraphicsScene()
        self.view.setScene(self.scene)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.view.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.view.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.view.setBackgroundBrush(Qt.GlobalColor.darkGray)
        
        layout.addWidget(self.view)
        self.setLayout(layout)
        
        # Pixmap item for displaying the page
        self.pixmap_item = QGraphicsPixmapItem()
        self.scene.addItem(self.pixmap_item)
    
    def load_pdf(self, file_path):
        """Load a PDF file."""
        try:
            # Close previous document
            self.close_doc()
            
            # Open new document
            self.pdf_doc = fitz.open(file_path)
            self.total_pages = len(self.pdf_doc)
            self.current_page = 0
            
            # Render first page
            if self.total_pages > 0:
                self._render_current_page()
                self.pageChanged.emit(self.current_page)
                return True
            
            return False
            
        except Exception as e:
            print(f"Error loading PDF: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def close_doc(self):
        """Close the current PDF document and cleanup resources."""
        # Cancel any ongoing render gracefully
        if self.render_worker and self.render_worker.isRunning():
            self.render_worker.cancel()
            # Give it a moment to finish, but don't block indefinitely
            self.render_worker.wait(500)  # Wait max 500ms
        
        if self.pdf_doc:
            try:
                self.pdf_doc.close()
            except:
                pass
            self.pdf_doc = None
        
        self.current_page = 0
        self.total_pages = 0
        self._pending_render = None
        self.cache.clear()
        self.scene.clear()
        self.pixmap_item = QGraphicsPixmapItem()
        self.scene.addItem(self.pixmap_item)
    
    def go_to_page(self, page_num):
        """Navigate to a specific page."""
        if not self.pdf_doc:
            return
        
        page_num = max(0, min(page_num, self.total_pages - 1))
        if page_num != self.current_page:
            self.current_page = page_num
            self._render_current_page()
            self.pageChanged.emit(self.current_page)
    
    def next_page(self):
        """Go to the next page."""
        if self.current_page < self.total_pages - 1:
            self.go_to_page(self.current_page + 1)
    
    def previous_page(self):
        """Go to the previous page."""
        if self.current_page > 0:
            self.go_to_page(self.current_page - 1)
    
    def zoom_in(self):
        """Zoom in."""
        self.set_zoom(self.zoom_level * 1.25)
    
    def zoom_out(self):
        """Zoom out."""
        self.set_zoom(self.zoom_level / 1.25)
    
    def set_zoom(self, zoom):
        """Set zoom level."""
        self.zoom_level = max(0.1, min(zoom, 5.0))
        self.cache.clear()  # Clear cache when zoom changes
        self._render_current_page()
    
    def fit_width(self):
        """Fit page to width."""
        if not self.pdf_doc or self.total_pages == 0:
            return
        
        page = self.pdf_doc[self.current_page]
        page_rect = page.rect
        view_width = self.view.viewport().width() - 20  # Some margin
        
        if page_rect.width > 0:
            zoom = view_width / page_rect.width
            self.set_zoom(zoom)
    
    def rotate(self, angle):
        """Rotate the current view (non-destructive, doesn't modify PDF)."""
        if not self.pdf_doc or self.total_pages == 0:
            return
        
        # Update rotation state (normalize to 0-360)
        self.rotation = (self.rotation + angle) % 360
        self.cache.clear()  # Clear cache since rotation changed
        self._render_current_page()
    
    def _render_current_page(self):
        """
        Render the current page safely.
        
        Instead of terminating the worker (which is unsafe), we:
        1. Cancel the existing worker gracefully
        2. Track pending renders to avoid flooding
        3. Ignore results from old renders in _on_page_rendered
        """
        if not self.pdf_doc or self.total_pages == 0:
            return
        
        # Check cache first (cache key includes rotation)
        cache_key = (self.current_page, self.zoom_level, self.rotation)
        cached_pixmap = self.cache.get(cache_key)
        
        if cached_pixmap:
            self.pixmap_item.setPixmap(cached_pixmap)
            self.scene.setSceneRect(QRectF(cached_pixmap.rect()))
            return
        
        # If there's already a worker running, cancel it gracefully
        if self.render_worker and self.render_worker.isRunning():
            # Set cancellation flag (safe, no terminate)
            self.render_worker.cancel()
            # Don't wait() here - let it finish naturally
            # The _on_page_rendered will ignore stale results
        
        # Track this render request (including rotation)
        self._pending_render = (self.current_page, self.zoom_level, self.rotation)
        
        # Start async render (pass rotation)
        self.render_worker = PdfRenderWorker(self.pdf_doc, self.current_page, self.zoom_level, self.rotation)
        self.render_worker.finished.connect(self._on_page_rendered)
        self.render_worker.start()
    
    def _on_page_rendered(self, page_num, pixmap):
        """
        Handle rendered page.
        
        Ignores results from cancelled/stale renders.
        """
        # Ignore if this is not the currently requested render
        if self._pending_render != (page_num, self.zoom_level, self.rotation):
            return
        
        # Ignore if page changed since request
        if page_num != self.current_page:
            return
        
        if pixmap and not pixmap.isNull():
            # Cache the pixmap (include rotation in key)
            cache_key = (page_num, self.zoom_level, self.rotation)
            self.cache.put(cache_key, pixmap)
            
            # Display it
            self.pixmap_item.setPixmap(pixmap)
            self.scene.setSceneRect(QRectF(pixmap.rect()))
        
        # Clear pending render
        self._pending_render = None
    
    def print_document(self, printer):
        """Print the current PDF document with proper scaling and centering."""
        if not self.pdf_doc:
            return
        
        painter = QPainter(printer)
        
        try:
            for page_num in range(self.total_pages):
                if page_num > 0:
                    printer.newPage()
                
                # Render page at printer resolution
                page = self.pdf_doc[page_num]
                page_rect = page.rect
                
                # Get printer page size and resolution
                printer_rect = printer.pageRect(QPrinter.Unit.DevicePixel)
                dpi = printer.resolution()  # dots per inch
                
                # Calculate scale to fit printer page (maintain aspect ratio)
                scale_x = printer_rect.width() / page_rect.width
                scale_y = printer_rect.height() / page_rect.height
                scale = min(scale_x, scale_y) * 0.95  # 95% to leave margin
                
                # Render page with proper scaling
                mat = fitz.Matrix(scale, scale)
                pix = page.get_pixmap(matrix=mat, alpha=False)
                
                # Convert to QImage (safe: copy buffer)
                img = QImage(pix.width, pix.height, QImage.Format.Format_RGB888)
                img.bits()[:] = pix.samples  # Copy data to QImage's own buffer
                
                # Calculate centering offset
                x_offset = (printer_rect.width() - img.width()) / 2
                y_offset = (printer_rect.height() - img.height()) / 2
                
                # Draw centered image
                painter.drawImage(x_offset, y_offset, img)
                
        finally:
            painter.end()
