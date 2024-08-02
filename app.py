from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from flask_pymongo import PyMongo
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
import os
import re
import json

app = Flask(__name__)
app.config['MONGO_URI'] = 'mongodb+srv://josephpeterjece2021:AJ9Hg6xTtQBUCoGr@cluster1.xaacunv.mongodb.net/flaskproject?retryWrites=true&w=majority'
mongo = PyMongo(app)

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Path to the tesseract executable
pytesseract.pytesseract.tesseract_cmd = r'C:/Program Files/Tesseract-OCR/tesseract.exe'

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
    prices = re.findall(r'\$\d+(?:,\d{3})*(?:\.\d{2})?|\d+(?:,\d{3})*(?:\.\d{2})?', text)
    if prices:
        details['prices'] = prices
    
    # Extract dates (e.g., MM/DD/YYYY or DD-MM-YYYY)
    dates = re.findall(r'\b\d{2}/\d{2}/\d{4}\b|\b\d{2}-\d{2}-\d{4}\b', text)
    if dates:
        details['dates'] = dates
    
    return details

@app.route('/')
def index():
    folders = mongo.db.folders.find()
    return render_template('index.html', folders=folders)

@app.route('/upload', methods=['POST'])
def upload_files():
    folder_name = request.form['folder_name']
    folder_path = os.path.join(app.config['UPLOAD_FOLDER'], folder_name)
    
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    
    files = request.files.getlist('files')
    
    for file in files:
        if file:
            file_path = os.path.join(folder_path, file.filename)
            file.save(file_path)
    
    mongo.db.folders.update_one(
        {'name': folder_name},
        {'$set': {'path': folder_path}},
        upsert=True
    )
    return redirect(url_for('index'))

@app.route('/folder/<folder_name>')
def view_folder(folder_name):
    folder = mongo.db.folders.find_one({'name': folder_name})
    if not folder:
        return redirect(url_for('index'))
    
    folder_path = folder['path']
    image_files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
    return render_template('folder.html', folder_name=folder_name, images=image_files)

@app.route('/uploads/<folder_name>/<filename>')
def uploaded_file(folder_name, filename):
    folder_path = os.path.join(app.config['UPLOAD_FOLDER'], folder_name)
    return send_from_directory(folder_path, filename)

@app.route('/image_details/<folder_name>/<filename>')
def image_details(folder_name, filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], folder_name, filename)
    details = extract_details(file_path)
    return render_template('image_details.html', folder_name=folder_name, filename=filename, details=details)

if __name__ == '__main__':
    app.run(debug=True)
