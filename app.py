import json
import re
import requests
import os
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urlparse, urljoin
from flask import Flask, request, render_template, send_file

app = Flask(__name__)

# Function to validate URL
def is_valid_url(url):
    parsed_url = urlparse(url)
    return parsed_url.scheme in ['http', 'https']

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
    with open(json_file, 'r', encoding='utf-8') as file:
        data = json.load(file)
        html_content = data.get("html", "")

    soup = BeautifulSoup(html_content, 'html.parser')
    product_data = []
    product_cards = soup.find_all('div', class_='product-item-info')

    for product in product_cards:
        name = product.find('a', class_='product-item-link')
        product_name = name.text.strip() if name else 'N/A'

        sku = product.find('div', class_='sku')
        sku_text = sku.text.strip() if sku else 'N/A'

        price = product.find('span', class_='price')
        price_text = price.text.strip() if price else 'N/A'

        description = product.find('div', class_='description')
        description_text = description.text.strip() if description else 'N/A'

        description_text = re.sub(r'\s*Learn More.*$', '', description_text, flags=re.IGNORECASE).strip()
        product_data.append({'Product Name': product_name, 'SKU': sku_text, 'Price': price_text, 'Description': description_text})

    df = pd.DataFrame(product_data)
    df.to_excel(excel_file, index=False)
    print(f"Data successfully written to {excel_file}")


    try:
        os.remove(json_file)
        print(f"Temporary file '{json_file}' deleted.")
    except OSError as e:
        print(f"Error deleting file '{json_file}': {e}")

# Function to handle dynamic pagination with loop detection
def scrape_all_pages(base_url):
    current_page_url = base_url
    all_html_content = ""
    visited_urls = set()

    while True:
        if current_page_url in visited_urls:
            print(f"Page already visited: {current_page_url}. Stopping to avoid a loop.")
            break

        print(f"Scraping: {current_page_url}")
        visited_urls.add(current_page_url)
        html_content = scrape_webpage(current_page_url)

        if not html_content:
            break

        soup = BeautifulSoup(html_content, 'html.parser')
        product_cards = soup.find_all('div', class_='product-item-info')

        if not product_cards:
            print("No more products found on this page.")
            break

        all_html_content += html_content

        # Find the next page link
        next_page = soup.find('a', {'class': 'next'})
        if next_page:
            next_page_url = next_page['href']
            next_page_url = urljoin(base_url, next_page_url)

            if next_page_url in visited_urls:
                print(f"Next page URL {next_page_url} already visited. Stopping to avoid a loop.")
                break

            current_page_url = next_page_url
        else:
            print("Reached the last page.")
            break

    return all_html_content

# Main function
# Route for the home page
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form['url']
        html_content = scrape_all_pages(url)

        if html_content:
            save_html_to_json(html_content, 'product_data.json')
            parse_html_to_excel('product_data.json', 'product_data.xlsx')

            # Serve the Excel file for download
            return send_file('product_data.xlsx', as_attachment=True)

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
