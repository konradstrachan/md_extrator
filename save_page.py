import requests
import os
import re
import sys
from bs4 import BeautifulSoup
from unidecode import unidecode
from dotenv import load_dotenv

load_dotenv()
destination_folder = os.getenv("DEST_PATH")

if destination_folder is None:
    print("destination_folder is not defined in the .env file!")


def remove_medium_div(soup, url):
    # Check if the domain is "medium" and remove the specified div
    if "medium.com" in url:
        medium_div = soup.find('div', class_="abb abc abd abe abf")
        if medium_div:
            medium_div.decompose()
        medium_div = soup.find('div', class_="rj rk rl rm rn l bw")
        if medium_div:
            medium_div.decompose()

def save_webpage(url):
    # Load the webpage content using requests library
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad responses

        # Parse HTML using BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')

        # Remove the specified div if the domain is "medium"
        remove_medium_div(soup, url)

        # Find the H2 tag containing the text "Recommended from Medium" and remove anything after it
        recommended_h2 = soup.find('h2', string=re.compile("Recommended from Medium", re.IGNORECASE))
        if recommended_h2:
            next_tag = recommended_h2.find_next()
            while next_tag and next_tag.name != 'h2':
                next_tag.decompose()
                next_tag = recommended_h2.find_next()

        # Find the first H1 heading
        h1_tag = soup.find('h1')

        # Get the title from either H1 or page title
        if h1_tag:
            title = re.sub("\n", "", h1_tag.get_text())  # Get heading text, strip newlines
        else:
            title = soup.title.string

        # If there is no title, set a default title
        if not title:
            title = "Untitled Page"

        # Convert the title to a filename-friendly format
        filename = re.sub(r'[^\w]', '', title) + ".md"

        # Write the title and original link to the Markdown file
        with open(filename, "w") as f:
            f.write(f"# {title}\n")
            f.write(f"Original Link: {url}\n\n")

        # Iterate through all headings (H1, H2, etc.) and paragraphs in the website
        with open(destination_folder + filename, "a") as f:
            for tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p']):
                if tag.name.startswith('h'):
                    heading_level = int(tag.name[1])
                    heading_text = re.sub("\n", "", tag.get_text())  # Get heading text, strip newlines
                    heading_text = unidecode(heading_text)  # Convert to ASCII
                    if tag != recommended_h2:  # Skip the recommended H2
                        f.write(f"{'#' * heading_level} {heading_text}\n\n")
                elif tag.name == 'p':
                    text = re.sub("\n", "", tag.get_text())  # Get text content, strip newlines
                    text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces with a single space
                    text = unidecode(text)  # Convert to ASCII
                    if text:  # Skip empty lines
                        f.write(f"{text}\n\n")

        print(f"Webpage content saved to {filename}")
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        sys.exit(1)

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 script_name.py your_webpage.com")
        sys.exit(1)
    else:
        save_webpage(sys.argv[1])

if __name__ == '__main__':
    main()