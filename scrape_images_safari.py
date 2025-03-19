import requests
from bs4 import BeautifulSoup
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
import subprocess

# Verify ChromeDriver and Chrome versions
try:
    chromedriver_version = subprocess.check_output(["/usr/local/bin/chromedriver", "--version"]).decode().strip()
    print(f"ChromeDriver version: {chromedriver_version}")
except Exception as e:
    print(f"Error checking ChromeDriver version: {e}")
    exit(1)

try:
    chrome_version = subprocess.check_output(["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "--version"]).decode().strip()
    print(f"Chrome version: {chrome_version}")
except Exception as e:
    print(f"Error checking Chrome version: {e}")
    exit(1)

# Set up Chrome options
chrome_options = Options()
chrome_options.add_argument('--headless')  # Try headless mode
chrome_options.add_argument('--no-sandbox')  # For stability
chrome_options.add_argument('--disable-dev-shm-usage')  # Avoid shared memory issues
chrome_options.binary_location = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# Set up ChromeDriver
chromedriver_path = '/usr/local/bin/chromedriver'
service = Service(executable_path=chromedriver_path)
driver = None
try:
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_page_load_timeout(60)  # Increase timeout to 60 seconds
    print("ChromeDriver initialized successfully")
except Exception as e:
    print(f"Error initializing ChromeDriver: {e}")
    exit(1)

# Stop if driver is None
if driver is None:
    print("Driver is None. Cannot proceed with scraping.")
    exit(1)

# Search parameters
query = "cars parked under no parking board in India"
url = f"https://www.google.com/search?q={query}&tbm=isch"

# Load page with retry mechanism
max_retries = 3
for attempt in range(max_retries):
    try:
        driver.get(url)
        print(f"Page loaded successfully on attempt {attempt + 1}")
        break
    except Exception as e:
        print(f"Attempt {attempt + 1} failed: {e}")
        if attempt == max_retries - 1:
            print("All retries failed. Exiting.")
            driver.quit()
            exit(1)
        time.sleep(2)

# Scroll to load more images with stability check
try:
    for i in range(10):
        # Check if window is still available
        driver.current_window_handle  # Raises exception if window is gone
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        print(f"Scrolled {i + 1}/10")
        time.sleep(3)
except Exception as e:
    print(f"Error scrolling page: {e}")
    driver.quit()
    exit(1)

# Parse page
try:
    soup = BeautifulSoup(driver.page_source, "html.parser")
except Exception as e:
    print(f"Error parsing page source: {e}")
    driver.quit()
    exit(1)

driver.quit()
images = soup.find_all("img")

print(f"Found {len(images)} <img> tags")
if len(images) < 100:
    print("Warning: Fewer than 100 images found. Google may not have loaded enough results.")

# Set up download directory on Desktop
save_dir = os.path.expanduser("~/Desktop/data")
os.makedirs(save_dir, exist_ok=True)

# Download exactly 100 images
count = 0
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.6998.89 Safari/537.36"
}

for img in images:
    if count >= 100:
        break
    try:
        img_url = img.get("src") or img.get("data-src")
        if not img_url:
            print(f"Image {count + 1}: No URL found")
            continue

        if img_url.startswith("/"):
            img_url = "https://www.google.com" + img_url

        if not img_url.startswith("http"):
            print(f"Skipping invalid URL: {img_url}")
            continue

        file_path = os.path.join(save_dir, f"image_{count:03d}.jpg")
        response = requests.get(img_url, headers=headers, timeout=10)
        response.raise_for_status()

        with open(file_path, "wb") as f:
            f.write(response.content)
        print(f"Downloaded image {count + 1}/100")
        count += 1

    except requests.exceptions.RequestException as e:
        print(f"Error downloading image {count + 1} from {img_url}: {e}")
    except Exception as e:
        print(f"Unexpected error for image {count + 1}: {e}")

# Final status
if count < 100:
    print(f"Warning: Only {count} images downloaded.")
else:
    print(f"Success: Downloaded {count} images to {save_dir}")