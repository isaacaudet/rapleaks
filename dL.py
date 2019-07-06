from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from oauth2client import file, client, tools
import glob
import os
import time
import sys

location = r"C:\Users\isaac\Documents\SoundDL"
fid = "1-9HbOEJhzVIRQ4wyglgEVkB9-xqHft5C"

    
def download_wait(path_to_downloads):
    seconds = 0
    dl_wait = True
    while dl_wait and seconds < 40:
        time.sleep(1)
        dl_wait = False
        for fname in os.listdir(path_to_downloads):
            if fname.endswith('.crdownload'):
                dl_wait = True
        seconds += 1
    return seconds  # wait to allow dL to finish

# Sets download location
options = Options()
prefs = {'download.default_directory': "C:\\Users\\isaac\\Documents\\SoundDL"}
options.add_experimental_option('prefs', prefs)

# Webdriver
driver = webdriver.Chrome(options=options)
driver.minimize_window()
driver.get('https://scdownloader.io/')
wait = WebDriverWait(driver, 20)

# Selenium
box = wait.until(EC.element_to_be_clickable(
    (By.XPATH, "//div[@id='conversionForm']/form/div/input")))  # text box
box.send_keys(Keys.CONTROL, 'v')

nxt = wait.until(EC.element_to_be_clickable(
    (By.XPATH, "//div[@id='conversionForm']/form/button")))  # convert button
nxt.click()

wait.until(EC.visibility_of_element_located((By.XPATH, "//div[@id='result']")))

result = driver.find_elements_by_xpath(
    "//div[@class='searchboxholder']//a")  # dl button

if(len(result) > 0):
    # print(result[0].get_attribute("href"))
    result[0].click()
else:
    print("Invalid link")
    driver.quit()
    raise SystemExit

# Drive API
g_login = GoogleAuth()
g_login.LoadCredentialsFile("mycreds.txt")

if g_login.credentials is None:
    g_login.LocalWebserverAuth()

elif g_login.access_token_expired:
    g_login.Refresh()

else:
    g_login.Authorize()
g_login.SaveCredentialsFile("mycreds.txt")

drive = GoogleDrive(g_login)

# Wait till downloads finished and quit driver after

download_wait(location)
driver.quit()

# Gets path of most recent download

list_of_files = glob.glob('C:\\Users\\isaac\\Documents\\SoundDL\\*')
new = newest = max(list_of_files, key=os.path.getctime)
base = os.path.basename(new)

# Open File and upload song to leaks folder

file_drive = drive.CreateFile(metadata={"title": os.path.basename(
    new), "parents": [{"kind": "drive#fileLink", "id": fid}]})
file_drive.SetContentFile(new)
file_drive.Upload()
