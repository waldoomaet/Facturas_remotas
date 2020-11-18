from fpdf import FPDF

def imageToPdf(savePath, photoPath):
    pdf = FPDF()
    pdf.add_page()
    pdf.image(str(photoPath), w = 105, h = 140)
    pdf.output(str(savePath), "F")