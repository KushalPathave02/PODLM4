import os
import re
import pdfplumber
def extractTextFromTxt(filePath):
    with open(filePath, 'r', encoding='utf-8') as file:
        return file.read()


def extractTextFromPdf(filePath):
    text = ''
    with pdfplumber.open(filePath) as pdf:
        for page in pdf.pages:
            text += page.extract_text()
    return text


def extractText(filePath):
    fileExt = os.path.splitext(filePath)[1].lower()
    
    if re.search(r'\.pdf$', fileExt):
        return extractTextFromPdf(filePath)
    elif re.search(r'\.txt$', fileExt):
        return extractTextFromTxt(filePath)
    else:
        raise ValueError("Unsupported file format")