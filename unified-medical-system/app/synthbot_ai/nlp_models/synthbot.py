import requests
import time
import requests
from PIL import Image
import time
import base64
import io
from dotenv import load_dotenv
import os

load_dotenv()

def roberta_QA(question):
    
    with open("unified-medical-system/app/synthbot_ai/nlp_models/disease.txt", "r") as file:
        context = file.read()
        
    # Your Hugging Face API key
    api_key = os.getenv("HUGGINGFACE_API_KEY")

    # API URL for the question-answering pipeline
    api_url = "https://api-inference.huggingface.co/models/deepset/roberta-base-squad2"

    # Headers for authentication
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    
    # Data to send in the POST request
    payload = {
        "inputs": {
            "question": question,
            "context": context
        }
    }

    # Making the request
    response = requests.post(api_url, headers=headers, json=payload)

    # Check if the request was successful
    if response.status_code == 200:
        # Print the answer from the response
        print(response.json()['answer'])
    else:
        print(f"Request failed with status code {response.status_code}: {response.text}")
        
def bart_summarize():
    try:
        with open("unified-medical-system/app/synthbot_ai/nlp_models/disease.txt", "r") as file:
            text = file.read()
        
        # Print the length of the input text for debugging
        print(f"Input text length: {len(text)} characters")
        
        # Your Hugging Face API key
        api_key = os.getenv("HUGGINGFACE_API_KEY")

        # API URL for the BART CNN Large summarization model
        api_url = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"

        # Headers for authentication
        headers = {
            "Authorization": f"Bearer {api_key}"
        }

        # Data to send in the POST request
        payload = {
            "inputs": text[:4096],  # Limit input to 4096 characters
            "parameters": {"max_length": 150, "min_length": 50}
        }

        # Making the request
        response = requests.post(api_url, headers=headers, json=payload)

        # Check if the request was successful
        if response.status_code == 200:
            # Print the summary from the response
            print(response.json()[0]['summary_text'])
        else:
            print(f"Request failed with status code {response.status_code}: {response.text}")
    
    except Exception as e:
        print(f"An error occurred: {str(e)}")

# Call the function
bart_summarize()
    
question = input("Enter your question: ")
roberta_QA(question)


def florence():
    api_key = os.getenv("HUGGINGFACE_API_KEY")
    api_url = "https://api-inference.huggingface.co/models/microsoft/trocr-base-handwritten"
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    image_path = "SIN13/unified-medical-system/app/synthbot_ai/nlp_models/test.jpeg"
    image = Image.open(image_path)
    image_bytes = image_to_base64(image)
    payload = {
        "inputs": image_bytes
    }
    max_retries = 5
    retry_delay = 5

    for attempt in range(max_retries):
        response = requests.post(api_url, headers=headers, json=payload)
        if response.status_code == 200:
            result = response.json()
            print("Florence model output:")
            print(result)
            break
        elif response.status_code == 503:
            print(f"Model is loading. Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
        else:
            print(f"Request failed with status code {response.status_code}: {response.text}")
            break
    else:
        print("Max retries reached. The model could not be loaded.")

def image_to_base64(image):
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='JPEG')
    return base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')

# def image_to_text():
#     api_key = os.getenv("HUGGINGFACE_API_KEY")
#     api_url = "https://api-inference.huggingface.co/models/Salesforce/blip-image-captioning-large"
#     headers = {
#         "Authorization": f"Bearer {api_key}"
#     }
#     image_path = "/home/chrisdepallan/Documents/python/flask/sinova/SIN13/unified-medical-system/app/synthbot_ai/nlp_models/test.jpeg"
#     image = Image.open(image_path)
#     image_bytes = image_to_base64(image)
#     payload = {
#         "inputs": image_bytes
#     }
#     max_retries = 5
#     retry_delay = 5

#     for attempt in range(max_retries):
#         response = requests.post(api_url, headers=headers, json=payload)
#         if response.status_code == 200:
#             result = response.json()
#             print("Image caption:")
#             print(result[0]['generated_text'])
#             break
#         elif response.status_code == 503:
#             print(f"Model is loading. Retrying in {retry_delay} seconds...")
#             time.sleep(retry_delay)
#         else:
#             print(f"Request failed with status code {response.status_code}: {response.text}")
#             break
#     else:
#         print("Max retries reached. The model could not be loaded.")

# Uncomment the following lines to run the functions
# florence()
# image_to_text()
def trocr():
    from transformers import TrOCRProcessor, VisionEncoderDecoderModel
    from PIL import Image
    import requests

    # Load image from local path
    image_path = "SIN13/unified-medical-system/app/synthbot_ai/nlp_models/test.jpeg"
    image = Image.open(image_path).convert("RGB")

    processor = TrOCRProcessor.from_pretrained('microsoft/trocr-base-handwritten')
    model = VisionEncoderDecoderModel.from_pretrained('microsoft/trocr-base-handwritten')
    pixel_values = processor(images=image, return_tensors="pt").pixel_values

    generated_ids = model.generate(pixel_values)
    generated_text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
    
    print("Generated text:", generated_text)
trocr()