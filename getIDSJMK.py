# download actual departures from  to requested stations. Also detect delay
# finally are data send to zivyobraz.eu to be displayed on epaper 
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoAlertPresentException
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import requests
import re


chrome_options = Options()
chrome_options.add_argument("--headless")  # Run Chrome in headless mode
chrome_options.add_argument("--disable-gpu")  # Disable GPU acceleration (optional)
chrome_options.add_argument("--no-sandbox")  # Prevent sandboxing (useful in certain environments)
chrome_options.add_argument("--disable-dev-shm-usage")  # Prevent /dev/shm usage issues in Docker
chrome_options.add_argument("--window-size=1920,1080")  # Set a high resolution to avoid viewport issues

key="KEY"  # access key to zivy obraz
fromStation="Doubravice, nám."
toStation="Boskovice"
# set required type of transport to True, the rest to False
Bus=True                
tram=False
trolley=False
ship=False
train=False
maxcnt=5        # maximal number of connections to print


# Set up WebDriver (download the correct version of chromedriver)
driver = webdriver.Chrome(options=chrome_options) # no browser window
#driver = webdriver.Chrome() # show browser window

# Open the target webpage
driver.get("https://www.idsjmk.cz/connection-finder/search")  # Replace with the actual URL

# Wait for the checkbox to be clickable - important to obtain responses
checkbox = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.ID, "TRAMWAY"))
)

# Store the main window handle ()
main_window = driver.current_window_handle


if (not tram):
    checkbox = driver.find_element(By.ID, "TRAMWAY")
    # Check if it's selected and uncheck if needed
    if checkbox.is_selected():
        checkbox.click()
if (not train):
    checkbox = driver.find_element(By.ID, "TRAIN")
    # Check if it's selected and uncheck if needed
    if checkbox.is_selected():
        checkbox.click()
if (not trolley):
    checkbox = driver.find_element(By.ID, "TROLLEYBUS")
    # Check if it's selected and uncheck if needed
    if checkbox.is_selected():
        checkbox.click()
if (not ship):
    checkbox = driver.find_element(By.ID, "SHIP")
    # Check if it's selected and uncheck if needed
    if checkbox.is_selected():
        checkbox.click()

if (not Bus):
    checkbox = driver.find_element(By.ID, "BUS")
    # Check if it's selected and uncheck if needed
    if checkbox.is_selected():
        checkbox.click()


# Locate the ComboBox input field (adjust selector if needed)
combobox = driver.find_element(By.ID, "from")  # Adjust if necessary
combobox.clear()  # Clear any existing text
combobox.send_keys(fromStation)  # Change to the desired input
time.sleep(0.5)
combobox.send_keys(Keys.ENTER)  # Confirm selection
time.sleep(0.5)

combobox = driver.find_element(By.ID, "to")  # Adjust if necessary
combobox.clear()  # Clear any existing text
combobox.send_keys(toStation)  # Change to the desired input
time.sleep(0.5)
combobox.send_keys(Keys.ENTER)  # Confirm selection
time.sleep(0.5)

# press button
button = driver.find_element(By.XPATH, "/html/body/app-root/div/page-search-connection/app-search-connection/form/div[5]/div[2]/button")  # Adjust accordingly
button.click()

# Wait for the content to update
time.sleep(3)


# detect popup window if connection is not found
try:
    # Switch to the alert
    alert = driver.switch_to.alert
#    print("Popup detected:", alert.text)

    # Press Enter (same as clicking OK)
    alert.accept()  # Use alert.dismiss() if you want to cancel instead

except NoAlertPresentException:
#    print("No popup detected.")
    pass


# Get the list of opened windows
windows = driver.window_handles
if len(windows) > 1:
#    print("Popup window detected!")
    driver.switch_to.window(windows[-1])  # Switch to the popup window
else:
    pass
#    print("No popup detected.")

html_content = driver.page_source
# Save the content to a local HTML file
with open("updated_page.html", "w", encoding="utf-8") as file:
    file.write(html_content)

# parse data

# Load the saved HTML file
#with open("updated_page.html", "r", encoding="utf-8") as file:
#    html_content = file.read()


# Find all divs with class 'connection'
soup = BeautifulSoup(html_content, "html.parser")
connections = soup.find_all("div", class_="connection")


output=""
icnt=0
# Iterate through each connection and extract the spans
for connection in connections:
    #print("Connection")
    # Find the span with the specified class (adjust if necessary)
    spans = connection.find_all("span", class_="text-primary")
    Delay=""
    delay = connection.find("div", class_=["delay", "visible-lg-block"])
    if (delay):
        match = re.search(r"Aktuální zpoždění\s+(\d+)", delay.text)
        if match:
            Delay=" z"+match.group(1)

    if (len(spans)>=3):
        icnt=icnt+1
        Num=spans[2].get_text(strip=True)       # name of Bus/Tram/...
        Num=Num.replace("Bus ", "")
        Num=Num.replace("Vlak ", "")
        Num=Num.replace("Trol. ", "")
        Num=Num.replace("Loď ", "")
        Num=Num.replace("Tram. ", "")
        Departure=spans[0].get_text(strip=True)
        DepartureSplit=Departure.split(":")  # get only the first number X:XX. In case of delay is next number delayed time
        Departure=DepartureSplit[0]+":"+DepartureSplit[1][:2]
        if (icnt>1):
            output=output+f"\\n{Num}: {Departure} {Delay}"
        else:
            output=f"{Num}: {Departure} {Delay}"
        if icnt==maxcnt:
            break
if (icnt>0):
    url="https://in.zivyobraz.eu/?import_key="+key+"&autobusy="+output
else:
    # not detected any connection (usual on weekends)
    url="https://in.zivyobraz.eu/?import_key="+key+"&autobusy=Nic nejede"

if (key == "KEY"):
    print("Set zivyobraz key to send values")
    print(output)
else:
    response = requests.get(url)
