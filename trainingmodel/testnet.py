import requests

url = "https://huggingface.co/models"

try:
    response = requests.get(url)
    if response.status_code == 200:
        print("Successfully accessed Hugging Face.")
    else:
        print(f"Failed to access Hugging Face. Status code: {response.status_code}")
except requests.exceptions.RequestException as e:
    print(f"Error accessing Hugging Face: {e}")