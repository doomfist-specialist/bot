import time
import random
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options  # Import Chrome Options


# Gmail credentials (use your Gmail address and App Password here)
GMAIL_USER = 'Email Here'  
GMAIL_PASSWORD = 'Email Creds. Here'  

# List of recipients to send notifications to
recipients = ['user1@email.com',
              'user2@email.com',
              'user3@email.com',
              'user4@email.com',
              'user5@email.com',
           ]  # Add multiple email addresses here

# File to persist product availability statuses between script runs (optional)
STATUS_FILE = 'product_status.json'

# Load product status from file (if it exists) or start with an empty dictionary
try:
    with open(STATUS_FILE, 'r') as f:
        product_status = json.load(f)
except FileNotFoundError:
    product_status = {}

# Function to send email notifications to multiple users
def send_email(subject, body, recipients):
    try:
        # Create the email content
        msg = MIMEMultipart()
        msg['From'] = GMAIL_USER
        msg['Subject'] = subject

        # Add the email body
        msg.attach(MIMEText(body, 'plain'))

        # Connect to the Gmail server
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()  # Secure the connection
        server.login(GMAIL_USER, GMAIL_PASSWORD)  # Login with your email and app password
        text = msg.as_string()

        # Send the email to each recipient
        for recipient in recipients:
            msg['To'] = recipient
            server.sendmail(GMAIL_USER, recipient, text)
            print(f"Email sent to: {recipient}")

        server.quit()

    except Exception as e:
        print(f"Failed to send email: {e}")

# Function to notify users about multiple available products in a single email
def notify_users(available_products):
    if available_products:
        subject = "Products Available Notification"
        body = "The following products are now available:\n\n" + "\n".join(available_products)
        send_email(subject, body, recipients)

# Function to save product status to file (optional, for persistence across script runs)
def save_status():
    with open(STATUS_FILE, 'w') as f:
        json.dump(product_status, f)

# Function to check product availability
def check_product_availability():
    available_products = []  # List to collect available products

    # Set up the WebDriver
    service = Service(executable_path='chromedriver.exe')  # Adjust the path to your ChromeDriver
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # Open the webpage
    driver.get('https://www.dzrt.com/en-sa/products')

    # Random wait time to avoid bot detection
    time.sleep(random.uniform(5, 10))

    # Interact with the "18 YEARS OR OLDER" button
    button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '18 YEARS')]"))
    )
    button.click()

    # Random wait time before interacting with the next element
    time.sleep(random.uniform(3, 6))

    # Interact with the "Reject Non-Essential" button for cookies
    reject_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//button[text()='Reject Non-Essential']"))
    )
    reject_button.click()

    # Wait for the main product grid to be visible
    main_container = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'grid grid-cols-2 gap-3 lg:grid-cols-5 lg:gap-6')]"))
    )

    # Find all products in the main container
    products = main_container.find_elements(By.XPATH, ".//div[contains(@class, 'relative bg-white')]")

    # Loop through each product and check availability
    for product in products:
        try:
            # Extract product name from the link (href attribute)
            product_name = product.find_element(By.XPATH, ".//a").get_attribute("href").split('/')[-1].replace('-', ' ')
            product_name = product_name.capitalize()

            # Check if the "Add to Basket" button is disabled
            add_to_basket_button = product.find_element(By.XPATH, ".//button[contains(text(), 'Add to Basket')]")
            is_disabled = add_to_basket_button.get_attribute("disabled")

            # If the button is not disabled, the product is available
            if not is_disabled:
                # Check if the product status has changed to available
                if product_name not in product_status or product_status[product_name] != 'AVAILABLE':
                    available_products.append(product_name)  # Add to list of available products

                # Update the product status to AVAILABLE
                product_status[product_name] = 'AVAILABLE'
            else:
                # Update status without notifying if it's out of stock (just for tracking)
                product_status[product_name] = 'OUT OF STOCK'

        except Exception as e:
            print(f"Error extracting product name or availability: {str(e)}")

    # Notify users if any products are available
    notify_users(available_products)

    # Save the status to file (optional, for persistence between script runs)
    save_status()

    # Close the driver after the process is complete
    driver.quit()

# Main loop to run the script every minute
while True:
    check_product_availability()

    # Wait for a minute between script runs (with slight randomization to avoid fixed intervals)
    wait_time = random.uniform(55, 65)  # Random wait between 55 and 65 seconds
    print(f"Waiting for {wait_time:.2f} seconds before checking again.")
    time.sleep(wait_time)
