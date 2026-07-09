from pypdf import PdfReader

reader = PdfReader(r"C:\ferrycast\docs\FerryCast_블로그_홍보글.pdf")
out_dir = r"C:\blog\drafts\ferrycast_pdf_images"

count = 0
for page_num, page in enumerate(reader.pages, start=1):
    for img in page.images:
        count += 1
        fname = f"{out_dir}\\p{page_num}_{img.name}"
        with open(fname, "wb") as f:
            f.write(img.data)
        print(f"saved: {fname} ({len(img.data)} bytes)")

print(f"\ntotal images: {count}")
