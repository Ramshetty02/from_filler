import time
import random
import string
import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from faker import Faker
import sys

# Configuration2
URL = 'https://www.ekamindia.org/offers/LV6Jrqzq/checkout'
DELAY = 0.001  # seconds between steps for visibility
LOG_FILE = 'registration_log.txt'
CSV_FILE = 'credentials.csv'

fake = Faker()

def log(msg):
    print(msg)
    with open(LOG_FILE, 'a') as f:
        f.write(str(msg) + '\n')

def random_password(length=10):
    chars = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(chars) for _ in range(length))

def scroll_and_send_keys(driver, by, value, text):
    elem = WebDriverWait(driver, 20).until(EC.presence_of_element_located((by, value)))
    driver.execute_script("arguments[0].scrollIntoView(true);", elem)
    WebDriverWait(driver, 20).until(EC.element_to_be_clickable((by, value)))
    elem.clear()
    elem.send_keys(text)
    time.sleep(DELAY)

def scroll_and_click(driver, by, value):
    elem = WebDriverWait(driver, 20).until(EC.presence_of_element_located((by, value)))
    driver.execute_script("arguments[0].scrollIntoView(true);", elem)
    WebDriverWait(driver, 20).until(EC.element_to_be_clickable((by, value)))
    elem.click()
    time.sleep(DELAY)

MAX_RETRIES = 3

def generate_gmail_email(base_name):
    import random
    return f"{base_name}{random.randint(1000,9999)}@gmail.com"

def fill_registration_form(driver, row, email_override=None):
    wait = WebDriverWait(driver, 20)
    # Fill Email
    email = email_override if email_override else row['email']
    scroll_and_send_keys(driver, By.NAME, 'checkout_offer[member][email]', email)
    # Fill Full Name
    scroll_and_send_keys(driver, By.NAME, 'checkout_offer[member][name]', row['name'])
    # Fill Phone Number
    scroll_and_send_keys(driver, By.NAME, 'checkout_offer[extra_contact_information][phone_number]', row['phone_number'])
    # Fill WhatsApp Number
    scroll_and_send_keys(driver, By.NAME, 'checkout_offer[extra_contact_information][custom_17]', row['whatsapp_number'])
    # Fill City
    scroll_and_send_keys(driver, By.NAME, 'checkout_offer[extra_contact_information][custom_40]', row['city'])
    # Select Country (dropdown)
    try:
        country_elem = driver.find_element(By.NAME, 'checkout_offer[extra_contact_information][custom_41]')
        driver.execute_script("arguments[0].scrollIntoView(true);", country_elem)
        Select(country_elem).select_by_visible_text(row['country'])
        time.sleep(DELAY)
    except Exception:
        log(f"Country dropdown not found or not selectable: {row['country']}")
    # Select State (dropdown)
    try:
        state_elem = driver.find_element(By.NAME, 'checkout_offer[extra_contact_information][custom_7]')
        driver.execute_script("arguments[0].scrollIntoView(true);", state_elem)
        Select(state_elem).select_by_visible_text(row['state'])
        time.sleep(DELAY)
    except Exception:
        log(f"State dropdown not found or not selectable: {row['state']}")
    # Fill Zip Code
    scroll_and_send_keys(driver, By.NAME, 'checkout_offer[extra_contact_information][custom_43]', row['zip_code'])
    # Select Language (dropdown)
    try:
        lang_elem = driver.find_element(By.NAME, 'checkout_offer[extra_contact_information][custom_30]')
        driver.execute_script("arguments[0].scrollIntoView(true);", lang_elem)
        Select(lang_elem).select_by_visible_text(row['language'])
        time.sleep(DELAY)
    except Exception:
        log(f"Language dropdown not found or not selectable: {row['language']}")
    # Agree to terms (must check)
    try:
        agree_checkbox = driver.find_element(By.NAME, 'checkout_offer[service_agreement]')
        driver.execute_script("arguments[0].scrollIntoView(true);", agree_checkbox)
        if not agree_checkbox.is_selected():
            try:
                agree_checkbox.click()
            except Exception:
                # Try clicking the label if checkbox is not interactable
                label = driver.find_element(By.XPATH, "//input[@name='checkout_offer[service_agreement]']/following-sibling::label")
                driver.execute_script("arguments[0].scrollIntoView(true);", label)
                label.click()
        time.sleep(DELAY)
    except Exception as e:
        log(f'Agreement checkbox not found or not clickable: {e}')
    # Click Sign up for free
    scroll_and_click(driver, By.NAME, 'commit')
    log('After clicking Sign up for free, current URL: ' + driver.current_url)
    # Removed the fixed wait here
    return email

def wait_for_password_fields(driver, timeout=15):
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.NAME, 'members_complete_setup[password]'))
        )
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.NAME, 'members_complete_setup[password_confirmation]'))
        )
        return True
    except Exception:
        return False

def set_password(driver):
    wait = WebDriverWait(driver, 20)
    password = random_password()
    # Wait for password fields to appear
    scroll_and_send_keys(driver, By.NAME, 'members_complete_setup[password]', password)
    scroll_and_send_keys(driver, By.NAME, 'members_complete_setup[password_confirmation]', password)
    # Click Create Account
    scroll_and_click(driver, By.NAME, 'commit')
    return password

def main():
    # Clear log file at start
    with open(LOG_FILE, 'w') as f:
        f.write('')
    with open(CSV_FILE, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for i, row in enumerate(reader, 1):
            attempt = 0
            success = False
            base_name = row['email'].split('@')[0]
            email_to_use = row['email']
            while attempt < MAX_RETRIES and not success:
                log(f"Registration {i} for {email_to_use} (attempt {attempt+1})")
                options = webdriver.ChromeOptions()
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                # options.add_argument('--headless')  # Uncomment to run without opening a browser window
                driver = webdriver.Chrome(options=options)
                try:
                    driver.get(URL)
                    fill_registration_form(driver, row, email_override=email_to_use)
                    if wait_for_password_fields(driver):
                        set_password(driver)
                        log(f"Registration {i} for {email_to_use} completed successfully.")
                        success = True
                    else:
                        log(f"Password fields not found after registration for {email_to_use}. Retrying with new gmail...")
                        attempt += 1
                        email_to_use = generate_gmail_email(base_name)
                except Exception as e:
                    log(f"Error during registration {i} for {email_to_use}: {e}")
                    attempt += 1
                    email_to_use = generate_gmail_email(base_name)
                finally:
                    driver.quit()
                time.sleep(DELAY)
            if not success:
                log(f"Failed to register for {row['email']} after {MAX_RETRIES} attempts.")

if __name__ == "__main__":
    main() 