import os
import sys
import subprocess
from io import BytesIO

# Check if we're using standalone WeasyPrint executable
def use_weasyprint_standalone():
    """Check if the standalone weasyprint.exe is available"""
    # First, check if we're running in the packaged app
    if getattr(sys, 'frozen', False) or 'ELECTRON_RUN_AS_NODE' in os.environ:
        # Look for weasyprint executable in various locations
        possible_paths = [
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bin', 'weasyprint.exe'),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', 'bin', 'weasyprint.exe'),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'resources', 'bin', 'weasyprint.exe'),
        ]
        for path in possible_paths:
            if os.path.exists(path):
                return path
    
    # Also check in standard locations for development environment
    dev_possible_paths = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dependencies', 'bin', 'weasyprint.exe'),
        os.path.join(os.getcwd(), 'dependencies', 'bin', 'weasyprint.exe'),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dist', 'win-unpacked', 'resources', 'bin', 'weasyprint.exe'),
    ]
    for path in dev_possible_paths:
        if os.path.exists(path):
            print(f"Found weasyprint.exe at: {path}")
            return path
            
    return None

# Create a class to mimic WeasyPrint's HTML class functionality
class HTMLWrapper:
    def __init__(self, string=None, filename=None):
        self.source = string
        self.filename = filename
        self.weasyprint_exe = use_weasyprint_standalone()

    def write_pdf(self, target=None):
        """Generate PDF using the standalone executable"""
        if not self.weasyprint_exe:
            raise RuntimeError("Standalone WeasyPrint executable not found")

        # Create temporary files for input and output if needed
        if self.source:
            # If source is provided as a string, save it to a temporary file
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix='.html', mode='w', encoding='utf-8') as f:
                f.write(self.source)
                input_file = f.name
        else:
            # Use provided filename
            input_file = self.filename

        # Handle the target
        if target is None:
            # If no target is provided, return the PDF as a BytesIO object
            output_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf').name
            use_temp_output = True
        elif isinstance(target, BytesIO):
            # If target is a BytesIO, use a temporary file and then read it back
            output_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf').name
            use_temp_output = True
        else:
            # Otherwise, use the target as is
            output_file = target
            use_temp_output = False

        try:
            # Run weasyprint command
            cmd = [self.weasyprint_exe, input_file, output_file]
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # If we need to return the PDF as bytes or write to a BytesIO
            if use_temp_output:
                with open(output_file, 'rb') as f:
                    pdf_data = f.read()

                if target is None:
                    # Return as a new BytesIO
                    result = BytesIO(pdf_data)
                    return result
                elif isinstance(target, BytesIO):
                    # Write to the provided BytesIO
                    target.write(pdf_data)
                    target.seek(0)
        finally:
            # Clean up temporary files
            if self.source and 'input_file' in locals():
                try:
                    os.unlink(input_file)
                except:
                    pass
            if use_temp_output and 'output_file' in locals():
                try:
                    os.unlink(output_file)
                except:
                    pass

# Implement CSS class to maintain API compatibility
class CSSWrapper:
    def __init__(self, string=None, filename=None):
        self.source = string
        self.filename = filename

# Try to import the real WeasyPrint, but fall back to our wrappers
try:
    # First attempt to use the Weasyprint executable
    weasyprint_exe = use_weasyprint_standalone()
    if weasyprint_exe:
        print(f"Using standalone WeasyPrint executable: {weasyprint_exe}")
        HTML = HTMLWrapper
        CSS = CSSWrapper
    else:
        # If no executable is found, try importing the Python module
        from weasyprint import HTML, CSS
        print("Using Python WeasyPrint module")
except ImportError:
    # If import fails, use our wrappers that call the executable
    print("WeasyPrint Python module not available, using executable fallback")
    HTML = HTMLWrapper
    CSS = CSSWrapper