import os
import io
import json
from flask import Flask, request, jsonify, send_file, render_template, redirect, url_for
from flask_cors import CORS
from pymongo import MongoClient
from google.cloud import vision
from google.oauth2 import service_account
from werkzeug.utils import secure_filename
import google.generativeai as genai
import base64
from bson import ObjectId

app = Flask(__name__)
CORS(app)
app.config['UPLOAD_FOLDER'] = 'uploads/'

# Connect to MongoDB
client = MongoClient('mongodb+srv://josephpeterjece2021:AJ9Hg6xTtQBUCoGr@cluster1.xaacunv.mongodb.net/flaskproject?retryWrites=true&w=majority')
db = client.imageDatabase
collection = db.images

# Google Cloud Vision API setup
credentials = service_account.Credentials.from_service_account_file('diginotice-007-ef701c25e261.json')
vision_client = vision.ImageAnnotatorClient(credentials=credentials)

# Google Generative AI setup
genai.configure(api_key="AIzaSyArV4Qqu9sXkBbXE-CADQJu49fqbTyPEgI")

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/')
def index():
    return render_template('upload.html')

@app.route('/upload-folder', methods=['POST'])
def upload_folder():
    if 'folder' not in request.files:
        return "No folder part in the request", 400

    files = request.files.getlist('folder')
    folder_path = app.config['UPLOAD_FOLDER']

    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    for file in files:
        if file and file.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            filename = secure_filename(file.filename)
            file_path = os.path.join(folder_path, filename)
            file.save(file_path)

            # Encode the image to Base64 and save to MongoDB
            with open(file_path, 'rb') as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                image_data = {
                    "filename": filename,
                    "image": encoded_string
                }
                collection.insert_one(image_data)

    return redirect(url_for('show_images'))

@app.route('/images')
def show_images():
    images_cursor = collection.find()
    images = list(images_cursor)  # Convert the cursor to a list of dictionaries
    for image in images:
        image['_id'] = str(image['_id'])  # Convert ObjectId to string for JSON serialization
    return render_template('image-data-extraction.html', images=images)

@app.route('/process_image/<image_id>', methods=['GET'])
def process_image(image_id):
    image_data = collection.find_one({"_id": ObjectId(image_id)})

    if not image_data:
        return jsonify({"error": "Image not found"}), 404

    # Decode the base64 image
    image_bytes = base64.b64decode(image_data['image'])
    image = vision.Image(content=image_bytes)

    # Perform text detection with Google Vision
    response = vision_client.text_detection(image=image)
    if response.error.message:
        return jsonify({"error": response.error.message}), 500

    texts = response.text_annotations
    extracted_text = ' '.join(text.description for text in texts)

    # JSON template for extraction
    json_format = '''
    {
      "id": 0,
      "isPublisher": "false",
      "isPaid": "false",
      "isOcr": 1,
      "noticeTypeId": 1,
      "statusId": 1,
      "landCategoryId": "1",
      "paperId": "",
      "sectorNo": " ",
      "projectName": "",
      "ownerFullName": "",
      "advocateId": 0,
      "personId": 0,
      "state": "",
      "district": "",
      "taluka": "",
      "villageName": "",
      "countryId": 1,
      "stateId": 72,
      "cityId": "",
      "talukaId": "",
      "villageId": "",
      "createdBy": "",
      "noticeDetailList": [
        {
          "surveyNumber": "",
          "fullSurveyNumber": "",
          "gatNumber": "",
          "fullGatNumber": "",
          "finalPlotNo": "",
          "subPlotNo": "",
          "privatePlotNo": "",
          "catestrialSurveyNo": "",
          "plotNumber": "",
          "fullPlotNumber": "",
          "ctsNumber": "",
          "fullCtsNumber": "",
          "area": "",
          "unitTypeId": "",
          "propertyArea": "",
          "houseNo": "",
          "tenementNo": "",
          "factoryShedNo": "",
          "industrialBuilding": "",
          "grampanchayatNo": "",
          "nagarPanchyatMilkatNo": "",
          "complaintNoReportNo": "",
          "glrNo": "",
          "malmattaNo": "",
          "corporationRegistrationNo": "",
          "propertyCard": "",
          "phaseNo": "",
          "buildingNo": " ",
          "flatShopNo": "",
          "commencementCertificateNo": "",
          "completionCertificateNo": "",
          "shareCertificateNo": "",
          "propertyNo": "",
          "buildingName": "",
          "flatNo": "",
          "floorNo": "",
          "constructedPropertyArea": "",
          "propertyCardNo": ""
        }
      ],
      "noticeTitle": "",
      "isActive": true,
      "imageUrl": "",
      "userName": "",
      "googleMapLink": "",
      "borrowerName": "",
      "advocateAddress": "",
      "advocatePhone": "",
      "noticePeriod": "",
      "landMark": "",
      "otherDetails": [],
      "advocateName": "",
      "PublishedDateString": "",
      "publishedDate": "",
      "otherDetails": [
        {
          "key": "value"
        }
      ],
      "nameChange":[
        {
          "currentName": "Current Name",
          "changedName": "Changed Name"
        }
      ]
    }
    '''

    # Create a prompt for Generative AI
    prompt = f"""
    --- You are a Data Engineer, who extracts information from text-based notices.

    --- Notice text: {extracted_text}

    --- Provide the JSON output using the following format:
    {json_format}

    --- Translate the notice into English before extracting information.

    --- Populate all the fields in JSON template with English text only.

    --- Perform suitable NLP tasks on the translated notice such as semantic analysis, syntactic analysis, coreference resolution, dependency parsing, and discourse analysis to accurately understand the meaning of the notice.

    --- Perform pre-processing on the translated notice text – Remove punctuations and prefixes like Mr., Mrs. from names.

    --- Properly extract and populate the JSON field for property type with "constructed" for buildings, "plot" for land, or "land" for agricultural land.

    --- Extract and populate all numeric fields such as date, plot number, sector number, khasra number, gat number, and property card number.

    --- Populate the field ownerFullName with names of all property owners separated by commas.

    --- Add "Adv. " to the advocate name before displaying.

    --- Populate values for area, propertyArea, constructedPropertyArea with appropriate units.

    --- Replace project names like "co-op housing society" with "CHSL" in the field projectName.

    --- If values are comma-separated, split them for the noticeDetailsList.

    --- Add additional fields found in the notice to the 'otherDetails' section of the JSON.

    --- Extract the notice period in days, months, or years.

    --- Handle tabular formats to extract all fields accurately.

    --- Remove non-required fields and ensure no values are omitted.

    --- For multiple name changes, extract each as a separate JSON object in the "nameChanges" array.

    --- Ensure accurate extraction and format compliance.
    """

    # Set up the model configuration
    generation_config = {
        "temperature": 0.1,
        "top_p": 0.95,
        "top_k": 0,
        "max_output_tokens": 32760,
    }

    # Safety settings
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]

    # Initialize the Generative AI model
    model = genai.GenerativeModel(
        model_name="gemini-1.5-pro",
        generation_config=generation_config,
        safety_settings=safety_settings
    )

    # Start a chat with the model
    convo = model.start_chat(history=[])
    genai_response = convo.send_message(prompt)

    # Extract JSON output from Generative AI response
    extracted_info = genai_response.text.strip()
    print("Extracted Info:", extracted_info)

    # Extract JSON from response
    try:
        start_index = extracted_info.find('{')
        end_index = extracted_info.rfind('}') + 1

        if start_index == -1 or end_index == -1:
            raise ValueError("JSON part not found in the extracted info")

        json_string = extracted_info[start_index:end_index]
        parsed_json = json.loads(json_string)

        # Update the MongoDB document with the extracted information
        collection.update_one({"_id": ObjectId(image_id)}, {"$set": {"extracted_info": parsed_json}})
        
        return jsonify(parsed_json)
    except ValueError as e:
        return jsonify({"error": "Invalid JSON format in Generative AI response"}), 400

@app.route('/image/<image_id>')
def get_image(image_id):
    image_data = collection.find_one({"_id": ObjectId(image_id)})

    if not image_data:
        return jsonify({"error": "Image not found"}), 404

    image_bytes = base64.b64decode(image_data['image'])
    return send_file(io.BytesIO(image_bytes), mimetype='image/jpeg')

if __name__ == '__main__':
    app.run(debug=True)
