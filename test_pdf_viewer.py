"""
Test script demonstrating safe PDF rendering cancellation.

Tests the improved PdfRenderWorker with cancellation flags instead of terminate().
"""

import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel, QHBoxLayout
from PyQt6.QtCore import QTimer
from ui.document_viewer import DocumentViewer
import os


class TestWindow(QMainWindow):
    """Test window for PDF viewer with rapid page navigation."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF Viewer - Safe Cancellation Test")
        self.setGeometry(100, 100, 1000, 800)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Info label
        self.info_label = QLabel("Testing safe cancellation - rapid page changes should not crash")
        layout.addWidget(self.info_label)
        
        # PDF viewer
        self.viewer = DocumentViewer()
        layout.addWidget(self.viewer)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        prev_btn = QPushButton("Previous")
        prev_btn.clicked.connect(self.viewer.previous_page)
        button_layout.addWidget(prev_btn)
        
        next_btn = QPushButton("Next")
        next_btn.clicked.connect(self.viewer.next_page)
        button_layout.addWidget(next_btn)
        
        stress_btn = QPushButton("Stress Test (Rapid Navigation)")
        stress_btn.clicked.connect(self.stress_test)
        button_layout.addWidget(stress_btn)
        
        zoom_in_btn = QPushButton("Zoom In")
        zoom_in_btn.clicked.connect(self.viewer.zoom_in)
        button_layout.addWidget(zoom_in_btn)
        
        zoom_out_btn = QPushButton("Zoom Out")
        zoom_out_btn.clicked.connect(self.viewer.zoom_out)
        button_layout.addWidget(zoom_out_btn)
        
        layout.addLayout(button_layout)
        
        # Page info
        self.page_label = QLabel("No document loaded")
        layout.addWidget(self.page_label)
        
        self.viewer.pageChanged.connect(self.update_page_label)
        
        # Timer for stress test
        self.stress_timer = QTimer()
        self.stress_timer.timeout.connect(self._stress_iteration)
        self.stress_count = 0
    
    def update_page_label(self, page_num):
        """Update page label."""
        self.page_label.setText(
            f"Page {page_num + 1} of {self.viewer.total_pages} "
            f"(Zoom: {self.viewer.zoom_level:.1f}x)"
        )
    
    def stress_test(self):
        """
        Stress test: rapidly change pages to test cancellation.
        
        This would crash with terminate() but should work fine with cancel().
        """
        self.info_label.setText("Running stress test - rapid page navigation...")
        self.stress_count = 0
        self.stress_timer.start(50)  # Change page every 50ms
    
    def _stress_iteration(self):
        """One iteration of stress test."""
        if self.stress_count < 20:  # Do 20 rapid changes
            # Alternate between different pages
            page = self.stress_count % self.viewer.total_pages
            self.viewer.go_to_page(page)
            self.stress_count += 1
        else:
            self.stress_timer.stop()
            self.info_label.setText(
                "✓ Stress test complete - no crashes! "
                "Safe cancellation working correctly."
            )


def main():
    """Run the test."""
    app = QApplication(sys.argv)
    
    window = TestWindow()
    window.show()
    
    # Try to find a PDF to load (look in common locations)
    test_pdfs = [
        r"C:\FaxManagerData\FaxManagerData\Faxes OCR'd\2024\12\test.pdf",
        r"C:\Users\Public\Documents\sample.pdf",
        "sample.pdf",
    ]
    
    pdf_loaded = False
    for pdf_path in test_pdfs:
        if os.path.exists(pdf_path):
            if window.viewer.load_pdf(pdf_path):
                window.info_label.setText(f"Loaded: {os.path.basename(pdf_path)}")
                pdf_loaded = True
                break
    
    if not pdf_loaded:
        window.info_label.setText(
            "No test PDF found. Add a PDF and call viewer.load_pdf(path) "
            "to test cancellation."
        )
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
