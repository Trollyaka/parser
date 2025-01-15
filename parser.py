import json
import re
import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urlparse

# Function to validate URL
def is_valid_url(url):
    parsed_url = urlparse(url)
    return parsed_url.scheme in ['http', 'https']  # Ensures it's a valid HTTP/S URL

# Function to scrape a webpage and get HTML content
def scrape_webpage(url):
    if not is_valid_url(url):
        print(f"Invalid URL: {url}")
        return None
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        else:
            print(f"Failed to retrieve webpage. Status code: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error while fetching the URL: {e}")
        return None

# Function to save HTML to JSON file
def save_html_to_json(html_content, file_name):
    with open(file_name, 'w', encoding='utf-8') as json_file:
        json.dump({"html": html_content}, json_file, ensure_ascii=False, indent=4)
    print(f"HTML content saved to {file_name}")

# Function to parse HTML and save the data to Excel
def parse_html_to_excel(json_file, excel_file):
    # Load the HTML from the JSON file
    with open(json_file, 'r', encoding='utf-8') as file:
        data = json.load(file)
        html_content = data.get("html", "")

    # Parse the HTML using BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')

    # Extract product details
    product_data = []
    product_cards = soup.find_all('div', class_='product-item-info')  # Adjust this selector as needed

    for product in product_cards:
        # Extract product name
        name = product.find('a', class_='product-item-link')
        product_name = name.text.strip() if name else 'N/A'

        # Extract SKU
        sku = product.find('div', class_='sku')
        sku_text = sku.text.strip() if sku else 'N/A'

        # Extract price
        price = product.find('span', class_='price')
        price_text = price.text.strip() if price else 'N/A'

        # Extract description
        description = product.find('div', class_='description')
        description_text = description.text.strip() if description else 'N/A'

        # Clean the description text: remove "Learn More" and trim extra spaces
        description_text = re.sub(r'\s*Learn More.*$', '', description_text, flags=re.IGNORECASE).strip()

        # Append to the product list
        product_data.append({
            'Product Name': product_name,
            'SKU': sku_text,
            'Price': price_text,
            'Description': description_text
        })

    # Convert to DataFrame and save to Excel
    df = pd.DataFrame(product_data)
    df.to_excel(excel_file, index=False)
    print(f"Data successfully written to '{excel_file}'")

# Function to handle pagination and scrape all pages
def scrape_all_pages(base_url):
    current_page = 1
    all_html_content = ""
    
    while True:
        url = f"{base_url}?p={current_page}"  # Assuming pagination is done with ?p=page_number
        print(f"Scraping page {current_page}: {url}")
        
        html_content = scrape_webpage(url)
        
        if not html_content:
            print("No more pages to scrape.")
            break
        
        soup = BeautifulSoup(html_content, 'html.parser')
        product_cards = soup.find_all('div', class_='product-item-info')
        
        if not product_cards:
            print("No more products found on this page.")
            break

        all_html_content += html_content
        current_page += 1
        
        next_page = soup.find('a', {'class': 'next'})  # Adjust selector if necessary
        if not next_page:
            print("Reached the last page.")
            break

    return all_html_content

# Example usage
def main():
    url = input("Enter the base URL of the product page: ")  # Replace with the base URL of the product page
    html_content = scrape_all_pages(url)  # Scrape all pages
    
    if html_content:
        save_html_to_json(html_content, 'product_data.json')  # Clear and save to json
        parse_html_to_excel('product_data.json', 'product_data.xlsx')  # Parse and save to Excel

if __name__ == '__main__':
    main()
