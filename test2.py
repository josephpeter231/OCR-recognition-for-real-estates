from google.cloud import vision
from google.oauth2 import service_account
import io
import google.generativeai as genai

# Provide the path to your service account key file
credentials = service_account.Credentials.from_service_account_file('diginotice-007-ef701c25e261.json')

# Initialize the Vision client with the credentials
client = vision.ImageAnnotatorClient(credentials=credentials)

# Load the image into memory
with io.open('IMG-20240802-WA0006.jpg', 'rb') as image_file:
    content = image_file.read()

image = vision.Image(content=content)

# Perform text detection on the image
response = client.text_detection(image=image)
texts = response.text_annotations

extracted_text = ' '.join([text.description for text in texts])

if response.error.message:
    raise Exception('{}\nFor more info on error messages, check: https://cloud.google.com/apis/design/errors'.format(response.error.message))

# Configure the API key for generative AI
genai.configure(api_key="AIzaSyArV4Qqu9sXkBbXE-CADQJu49fqbTyPEgI")

json_format = '''
{
  "noticeType": "",
  "noticeDate": "",
  "publishedBy": "",
  "borrowerNames": [
    "",
    "",
    "",
    "",
    ""
  ],
  "advocateName": "",
  "advocatePhone": "",
  "advocateAddress": "",
  "propertyType": "",
  "state": "",
  "district": "",
  "taluka": "",
  "villageName": "",
  "locality": "",
  "propertyDetails": {
    "surveyNo": "",
    "khasraNo": "",
    "plotNo": "",
    "ctsNo": "",
    "area": ""
  },
  "googleMapLocation": "",
  "additionalInformation": ""
}
'''

prompt = f"""
I want to extract information from below notice in English,

--- Notice text: {extracted_text}

--- Give output in only JSON format. Use the following JSON format:{json_format}

--- As I need JSON output in English, you might have to translate notice in English before extracting information in JSON format.
"""

# Set up the model
generation_config = {
  "temperature": 0.4,
  "top_p": 0.95,
  "top_k": 0,
  "max_output_tokens": 8192,
}

safety_settings = [
  {
    "category": "HARM_CATEGORY_HARASSMENT",
    "threshold": "BLOCK_NONE"
  },
  {
    "category": "HARM_CATEGORY_HATE_SPEECH",
    "threshold": "BLOCK_NONE"
  },
  {
    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
    "threshold": "BLOCK_NONE"
  },
  {
    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
    "threshold": "BLOCK_NONE"
  },
]

model = genai.GenerativeModel(model_name="gemini-pro",
                              generation_config=generation_config,
                              safety_settings=safety_settings)

convo = model.start_chat(history=[])
convo.send_message(prompt)

print(convo.last.text)
