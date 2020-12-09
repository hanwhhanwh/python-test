import pytesseract

pytesseract.pytesseract.tesseract_cmd = r'C:\Dev\Tesseract-OCR\tesseract'

#print(pytesseract.image_to_string('./ocr/after2.jpg'))
print(pytesseract.image_to_string('./ocr/s1.png'))

print(pytesseract.image_to_string('./ocr/p1.png'))