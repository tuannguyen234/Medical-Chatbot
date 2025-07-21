import requests  # Import the requests library for making HTTP requests
from bs4 import BeautifulSoup  # Import BeautifulSoup for parsing HTML
import os  # Import the os module for interacting with the operating system

url = "https://youmed.vn/tin-tuc/trieu-chung-benh/"  # Define the URL to scrape
response = requests.get(url)  # Send an HTTP GET request to the URL
soup = BeautifulSoup(response.text, "html.parser")  # Parse the HTML content of the response

articles = soup.find_all("div", class_="letter-section")  # Find all 'div' elements with the class 'letter-section'
all_letter = [i for i in articles]  # Create a list of these 'div' elements (not used, can be removed)
list_article = []  # Initialize an empty list to store article links
disease_links = {}  # Initialize an empty dictionary to store disease names and their links

for article in articles:  # Iterate through each 'article' found
    links = article.find_all('a')  # Find all 'a' (anchor) tags within each article
    for link in links:  # Iterate through each link
        href = link['href'].split('#')[0]  # Extract the URL from the 'href' attribute, removing any anchor part
        name = link.text.strip()  # Extract the text of the link (disease name), removing leading/trailing spaces
        if name and href:  # Check if both name and href are not empty
            disease_links[name] = href  # Add the disease name and link to the dictionary
            print(f'Disease: {name}, Link: {href}')  # Print the disease name and link
        else:
            print('No disease name found')  # Print a message if no disease name is found
        list_article.append(href)  # Append the link to the list of article links

image_data = []  # Initialize an empty list to store image data

def scrape_article(name, url):
    response = requests.get(url)  # Send an HTTP GET request to the article URL
    soup = BeautifulSoup(response.text, "html.parser")  # Parse the HTML content

    # Extract Text Content
    content_div = soup.find("div", class_="prose max-w-none my-4 prose-a:text-primary")  # Find the div containing main text
    paragraphs = content_div.find_all(["h1", "h2", "h3", "p", 'li'])  # Find headings, paragraphs, and list items
    text_content = "\n".join([p.text.strip() for p in paragraphs])  # Join the text, with newlines and stripping
    with open(f"article_texts/{name}.txt", "w", encoding="utf-8") as f:  # Open a file to write the text
        f.write(text_content)  # Write the extracted text to the file

    # Extract Image Content
    disease_folder = f'article_images/{name}'  # Define folder to save images for this disease
    os.makedirs(disease_folder, exist_ok=True)  # Create the folder if it doesn't exist

    for figure in soup.find_all('figure'):  # Find all 'figure' elements
        img_tag = figure.find("img")  # Find the 'img' tag within the 'figure'
        caption_tag = figure.find("figcaption")  # Find the 'figcaption'

        if img_tag:  # If an image tag is found
            img_url = img_tag.get("src")  # Get the image URL
            img_title = img_tag.get("alt", "No Titile Available")  # Get the image title, or "No Title Available"
            caption_text = caption_tag.text.strip() if caption_tag else "No Caption Available"  #Get caption

            if img_url:  # If the image URL is available
                safe_img_title = img_title.replace(' ', '_').replace('/', '_')  # Sanitize the image title for use as a filename
                safe_img_title = (safe_img_title[:100] + '...') if len(safe_img_title) > 100 else safe_img_title #limit characters

                image_filename = f"{disease_folder}/{safe_img_title}.jpg"  # Construct the image filename
                img_response = requests.get(img_url)  # Download the image
                with open(image_filename, 'wb') as f:  # Open a file to write the image data
                    f.write(img_response.content)  # Write the image content to the file

                image_data.append({  # Append image information to the list
                    'url': img_url,
                    'title': img_title,
                    'filename': image_filename,
                    'caption': caption_text
                })
            else:
                image_data.append({  # Append image information to the list
                    'url': 'No URL Available',
                    'title': img_title,
                    'filename': 'No Name',
                    'caption': 'No Caption Available'
                })

    return image_data  # Return the list of image data

# name, url = list(disease_links.items())
for name, url in disease_links.items():  # Iterate through the disease names and links
    print(name, url)  # Print the name and URL
    image_data = scrape_article(name, url) #scrape
