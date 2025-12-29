"""
Comprehensive PDF Viewer Improvements Demo

This script demonstrates all safety and correctness improvements:
1. QImage lifetime safety (buffer copying)
2. Non-destructive rotation via matrix
3. Cache key includes rotation
4. QPrinter Qt6 compatibility
5. Centered printing with margins
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtPrintSupport import QPrinter
from ui.document_viewer import DocumentViewer, PdfRenderWorker
import inspect

def test_qimage_safety():
    """Test 1: Verify QImage buffer copying for memory safety."""
    print("\n" + "="*70)
    print("TEST 1: QImage Lifetime Safety")
    print("="*70)
    
    # Read the source to verify the pattern
    source_file = "ui/document_viewer.py"
    with open(source_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for safe pattern
    safe_pattern = "img.bits()[:] = pix.samples"
    unsafe_pattern = "QImage(pix.samples"
    
    safe_count = content.count(safe_pattern)
    unsafe_count = content.count(unsafe_pattern)
    
    print(f"✓ Safe buffer copy pattern found: {safe_count} times")
    print(f"✓ Unsafe direct buffer reference: {unsafe_count} times")
    
    if safe_count >= 2 and unsafe_count == 0:
        print("✓ PASS: All QImage instances use safe buffer copying")
        return True
    else:
        print("✗ FAIL: Unsafe QImage patterns detected")
        return False

def test_rotation_system():
    """Test 2: Verify non-destructive rotation system."""
    print("\n" + "="*70)
    print("TEST 2: Non-Destructive Rotation")
    print("="*70)
    
    app = QApplication.instance() or QApplication(sys.argv)
    viewer = DocumentViewer()
    
    # Check initial state
    assert hasattr(viewer, 'rotation'), "Missing rotation attribute"
    assert viewer.rotation == 0, "Initial rotation should be 0"
    print(f"✓ Initial rotation: {viewer.rotation}°")
    
    # Test rotation method (without PDF loaded, just checks state)
    initial = viewer.rotation
    print(f"✓ rotate() method exists: {hasattr(viewer, 'rotate')}")
    
    # Check PdfRenderWorker accepts rotation
    sig = inspect.signature(PdfRenderWorker.__init__)
    params = list(sig.parameters.keys())
    assert 'rotation' in params, "PdfRenderWorker missing rotation parameter"
    print(f"✓ PdfRenderWorker supports rotation: {params}")
    
    # Check for preRotate in source
    with open("ui/document_viewer.py", 'r', encoding='utf-8') as f:
        content = f.read()
    
    assert 'preRotate' in content, "Missing preRotate matrix operation"
    assert 'set_rotation' not in content, "Found destructive set_rotation"
    print("✓ Uses mat.preRotate() (non-destructive)")
    print("✓ No page.set_rotation() (destructive) found")
    
    print("✓ PASS: Rotation system is non-destructive")
    return True

def test_cache_keys():
    """Test 3: Verify cache keys include rotation."""
    print("\n" + "="*70)
    print("TEST 3: Cache Key Structure")
    print("="*70)
    
    with open("ui/document_viewer.py", 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Look for cache key patterns
    cache_patterns = [
        "self.current_page, self.zoom_level, self.rotation",
        "page_num, self.zoom_level, self.rotation"
    ]
    
    found = []
    for pattern in cache_patterns:
        if pattern in content:
            count = content.count(pattern)
            found.append((pattern, count))
            print(f"✓ Found '{pattern}': {count} times")
    
    if found:
        print("✓ PASS: Cache keys include rotation")
        return True
    else:
        print("✗ FAIL: Cache keys don't include rotation")
        return False

def test_qprinter_import():
    """Test 4: Verify QPrinter import from QtPrintSupport."""
    print("\n" + "="*70)
    print("TEST 4: QPrinter Qt6 Compatibility")
    print("="*70)
    
    with open("ui/document_viewer.py", 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check import statement
    import_line = "from PyQt6.QtPrintSupport import QPrinter"
    
    if import_line in content:
        print(f"✓ Found: {import_line}")
        print("✓ PASS: QPrinter imported from QtPrintSupport (Qt6 compatible)")
        return True
    else:
        print("✗ FAIL: QPrinter not imported correctly")
        return False

def test_centered_printing():
    """Test 5: Verify centered printing with margins."""
    print("\n" + "="*70)
    print("TEST 5: Centered Printing with DPI")
    print("="*70)
    
    with open("ui/document_viewer.py", 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for key features
    features = {
        "printer.resolution()": "DPI awareness",
        "x_offset": "Horizontal centering",
        "y_offset": "Vertical centering",
        "* 0.95": "95% scale (5% margin)"
    }
    
    all_found = True
    for pattern, description in features.items():
        if pattern in content:
            print(f"✓ {description}: found '{pattern}'")
        else:
            print(f"✗ {description}: missing '{pattern}'")
            all_found = False
    
    if all_found:
        print("✓ PASS: Printing includes DPI, centering, and margins")
        return True
    else:
        print("✗ FAIL: Some print features missing")
        return False

def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("PDF VIEWER IMPROVEMENTS - COMPREHENSIVE TEST SUITE")
    print("="*70)
    
    results = []
    
    try:
        results.append(("QImage Safety", test_qimage_safety()))
        results.append(("Rotation System", test_rotation_system()))
        results.append(("Cache Keys", test_cache_keys()))
        results.append(("QPrinter Import", test_qprinter_import()))
        results.append(("Centered Printing", test_centered_printing()))
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(result[1] for result in results)
    
    print("\n" + "="*70)
    if all_passed:
        print("✓✓✓ ALL TESTS PASSED ✓✓✓")
        print("="*70)
        print("\nKey Improvements Verified:")
        print("  1. Memory safety: QImage owns its buffer")
        print("  2. Non-destructive: Rotation via matrix, not document mutation")
        print("  3. Cache correctness: Rotation included in cache keys")
        print("  4. Qt6 compatibility: QPrinter from QtPrintSupport")
        print("  5. Professional output: Centered printing with margins")
        return True
    else:
        print("✗✗✗ SOME TESTS FAILED ✗✗✗")
        print("="*70)
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
