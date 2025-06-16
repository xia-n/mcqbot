import pdfplumber
import pandas as pd

pdf_path = "markscheme.pdf"

all_tables = []

with pdfplumber.open(pdf_path) as pdf:
    # Skip first 3 pages
    for i, page in enumerate(pdf.pages[3:], start=4):  # page index 3 = 4th page
        # Define crop box to remove headers/footers (optional, based on your PDF layout)
        cropped = page.within_bbox((0, 80, page.width, page.height - 80))  # Top 80px and bottom 80px cropped

        # Extract tables
        tables = cropped.extract_tables()
        for table in tables:
            # Skip empty or malformed tables
            if table and len(table[0]) >= 3:
                df = pd.DataFrame(table)
                all_tables.append(df)

# Combine and clean
if all_tables:
    combined_df = pd.concat(all_tables, ignore_index=True)

    combined_df.to_excel("markscheme_cleaned.xlsx", index=False)
    print("✅ Done. Exported to markscheme_cleaned.xlsx")
else:
    print("⚠️ No valid tables found.")
