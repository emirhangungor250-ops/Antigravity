import pypdf
import sys

# Uretilen bir faturayi okuyup metnini dogrulamak icin yardimci script.
# Kontrol etmek istediginiz PDF'in yolunu arguman olarak verin.
if len(sys.argv) < 2:
    print("Kullanim: python parse_pdf.py uretilen-faturalar/INVOICE_ornek.pdf", file=sys.stderr)
    sys.exit(1)

pdf_path = sys.argv[1]

try:
    with open(pdf_path, "rb") as f:
        r = pypdf.PdfReader(f)
        text = r.pages[0].extract_text()
        print(text)
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
