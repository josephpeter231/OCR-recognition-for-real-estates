import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import json
import re

# Path to the tesseract executable
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def preprocess_image(image_path):
    # Open the image file
    img = Image.open(image_path)
    
    # Convert to grayscale
    img = img.convert('L')
    
    # Apply some preprocessing
    img = img.filter(ImageFilter.SHARPEN)
    img = ImageEnhance.Contrast(img).enhance(2)  # Increase contrast
    
    return img

def extract_details(image_path):
    # Preprocess the image
    img = preprocess_image(image_path)
    
    # Perform OCR on the image
    text = pytesseract.image_to_string(img)
    
    # Initialize a dictionary to store extracted details
    details = {}
    
    # Extract phone numbers using regex
    phone_numbers = re.findall(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text)
    if phone_numbers:
        details['phone_numbers'] = phone_numbers

    # Extract email addresses using regex
    emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
    if emails:
        details['emails'] = emails
    
    # Extract addresses using regex
    addresses = re.findall(r'\d{1,5}\s[A-Za-z]+\s[A-Za-z]+(?:\s[A-Za-z]+)*', text)
    if addresses:
        details['addresses'] = addresses

    # Extract other potential details (e.g., price, date) using regex
    # Example for price: $123,456 or 123456
    prices = re.findall(r'\$\d+(?:,\d{3})*(?:\.\d{2})?|\d+(?:,\d{3})*(?:\.\d{2})?', text)
    if prices:
        details['prices'] = prices
    
    # Extract dates (e.g., MM/DD/YYYY or DD-MM-YYYY)
    dates = re.findall(r'\b\d{2}/\d{2}/\d{4}\b|\b\d{2}-\d{2}-\d{4}\b', text)
    if dates:
        details['dates'] = dates
    
    return details



# Example usage
image_path = "C:/Users/josep/Downloads/Real estate/modern-apartment-advertisement-video-design-template-cd47cdf257ad4d349a45db755e32a881_screen.jpg"
details = extract_details(image_path)

# Print details in JSON format
print(json.dumps(details, indent=4))
