import csv
from serpapi import GoogleSearch
from dotenv import load_dotenv
import os
import requests, json
from PIL import Image
import pytesseract
load_dotenv() 

# --- Configuration ---
serpapi_api_key = os.environ["SERPAPI_API_KEY"] # Replace SERPAPI_API_KEY if not using env var
search_query = "cloud hosting" 
output_image_filename = "ad_creative.png"
pytesseract.pytesseract.tesseract_cmd = r'/opt/homebrew/bin/tesseract' # Example for macOS
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe' # Example for Windows

# --- 1. Fetch Ad Data from Google Ads Transparency Center ---
def get_ads_from_transparency_center(query):
    params = {
        "api_key": serpapi_api_key,
        "engine": "google_ads_transparency_center",
        "advertiser_id": "AR07223290584121737217",
        "region": "2840"
    }
    search = GoogleSearch(params)
    results = search.get_dict()
    return results.get("ad_creatives", [])

# --- 2. Download the Ad Image ---
def download_image(url, filename):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return filename
    except requests.exceptions.RequestException as e:
        print(f"Error downloading image from {url}: {e}")
        return None
    
# --- 3. Extract Text from the Image using Tesseract OCR ---
def extract_text_from_image(image_path):
    try:
        img = Image.open(image_path)
        extracted_text = pytesseract.image_to_string(img)
        return extracted_text
    except Exception as e:
        print(f"Error during OCR processing of {image_path}: {e}")
        return None
    
def create_csv():
    header = ["Advertiser", "Advertiser ID", "Details Link", "Image URL", "Extracted Text"] # Specify a list of the fields you are interested in
    with open("text_from_ads.csv", "w", encoding="UTF8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
    return
# --- Main Execution ---
if __name__ == "__main__":
    if not serpapi_api_key:
        print("Please set your SERPAPI_API_KEY environment variable or replace 'YOUR_SERPAPI_API_KEY' in the script.")
    else:
        print(f"Searching Google Ads Transparency Center for: '{search_query}'")
        ads_data = get_ads_from_transparency_center(search_query)
        if not ads_data:
            print("No ads found for the query.")
        else:
            create_csv()
            found_image_ad = False
            for ad in ads_data:
                if "image" in ad and ad["image"]:
                    image_url = ad["image"]
                    print(f"\n--- Processing Ad ---")
                    advertiser = ad.get('advertiser', 'N/A')
                    advertiser_id = ad.get("advertiser_id", "N/A")
                    details_link = ad.get('details_link', 'N/A')
                    downloaded_path = download_image(image_url, output_image_filename)
                    if downloaded_path:
                        # Display the downloaded image as an example
                        print(f"Image downloaded to: {downloaded_path}")
                        # Extract text from the image
                        extracted_text = extract_text_from_image(downloaded_path)
                        if extracted_text:
                            print("\n--- Extracted Text from Ad Image ---")
                            # Write to CSV
                            with open("text_from_ads.csv", "a", encoding="UTF8", newline="") as f:
                                print("\n--- Writing to CSV ---")
                                writer = csv.writer(f)
                                writer.writerow([advertiser, advertiser_id, details_link, image_url, extracted_text])
                        else:
                            print("Could not extract text from the image.")
                    found_image_ad = True

            if not found_image_ad:
                print("No ads with an image creative were found in the results.")
            