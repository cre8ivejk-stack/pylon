"""Regenerate sample data with enhanced scenarios."""

from pathlib import Path
from src.sample_data import generate_sample_data
import sys

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

if __name__ == "__main__":
    data_dir = Path("data")
    print("Regenerating sample data with enhanced scenarios...")
    print("=" * 70)
    generate_sample_data(data_dir)
    print("=" * 70)
    print("Data regeneration complete!")

