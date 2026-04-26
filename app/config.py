from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
SAMPLES_DIR = ROOT_DIR / "samples"
GENERATED_DIR = ROOT_DIR / "generated"
SAMPLE_INVOICE_PATH = SAMPLES_DIR / "sample_invoice.txt"
SAMPLE_INVOICE_IMAGE_PATH = SAMPLES_DIR / "sample_invoice_scan.pgm"
SAMPLE_LOW_QUALITY_IMAGE_PATH = SAMPLES_DIR / "sample_invoice_low_quality_scan.pgm"
