import glob
import os
import time
import sys
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, APIC
import magic
import logging
from yaspin import yaspin
from tkinter import Tk
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import InvalidArgumentException
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from oauth2client import file, client, tools

# Program created to automaticaly download rap leaks songs. The end goal would be to have is scan reddit and open posts, then automatically click and navigate the links to download files.

# Constants
location = r"C:\Users\isaac\Documents\SoundDL"
fid = "1-9HbOEJhzVIRQ4wyglgEVkB9-xqHft5C"
spinner = yaspin()

# Webdriver
options = Options()
options.add_experimental_option('excludeSwitches', ['enable-logging'])
prefs = {'download.default_directory': "C:\\Users\\isaac\\Documents\\SoundDL"}
options.add_experimental_option('prefs', prefs)
driver = webdriver.Chrome(options=options)
driver.minimize_window()
wait = WebDriverWait(driver, 4)


def download_wait(path_to_downloads):
    seconds = 0
    dl_wait = True
    while dl_wait and seconds < 20:
        time.sleep(1)
        dl_wait = False
        for fname in os.listdir(path_to_downloads):
            if fname.endswith('.crdownload'):
                dl_wait = True
        seconds += 1
    return seconds  # wait to allow dL to finish


def sound_dl(link):
    driver.get('https://scdownloader.io/')

    box = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//div[@id='conversionForm']/form/div/input")))  # text box
    box.send_keys(link)

    nxt = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//div[@id='conversionForm']/form/button")))  # convert button
    nxt.click()
    try:
        wait.until(EC.visibility_of_element_located(
            (By.XPATH, "//div[@id='result']")))

        result = driver.find_elements_by_xpath(
            "//div[@class='searchboxholder']//a")  # dl button

        if(len(result) > 0):
            result[0].click()
            download_wait(location)
            driver.quit()
            return
        else:
            raise TimeoutException
    except TimeoutException:
        raise


def pico_dl(link):
    driver.get(link)
    cont = True
    try:
        box = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//ul[@id='audio-actions']/li/a")))
    except TimeoutException:
        cont = False
        raise

    if cont == True:
        box.click()
        dl = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//div[@id='content']/div[2]/div/div/h3/a/strong")))
        dl.click()
        driver.minimize_window()
        download_wait(location)
        driver.quit()

    

def dbr_dl(link):
    driver.get(link)
    try:
        driver.implicitly_wait(5)
        box = wait.until(EC.element_to_be_clickable(
            (By.LINK_TEXT, "Download")))
        box.click()
    except TimeoutException:
        raise
    download_wait(location)
    driver.quit()
    return


def drive_up():
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

    # Gets path of most recent download

    list_of_files = glob.glob('C:\\Users\\isaac\\Documents\\SoundDL\\*')
    new = max(list_of_files, key=os.path.getctime)

    # Open File and upload song to leaks folder

    file_drive = drive.CreateFile(metadata={"title": os.path.basename(
        new), "parents": [{"kind": "drive#fileLink", "id": fid}]})
    file_drive.SetContentFile(new)
    file_drive.Upload()


def album_art(artist):
    os.chdir(r"C:\Users\isaac\Desktop\SounDL")
    os.system("sacad " + '"' + artist + '"' + ' "' + "" + '" ' + '"' + "600" '" ' + '"' + artist + ".jpg" + '"')


def metadata(file_name, artist, title):
    audio = EasyID3(file_name)
    audio['artist'] = artist
    audio['title'] = title
    audio.save()
    
    audio = ID3(file_name)
    with open(artist+".jpg", 'rb') as albumart:
        audio['APIC'] = APIC(
                          encoding=3,
                          mime='image/jpeg',
                          type=3, desc=u'Cover',
                          data=albumart.read()
                        )            
    audio.save()

def file_name():
    list_of_files = glob.glob('C:\\Users\\isaac\\Documents\\SoundDL\\*')
    new = max(list_of_files, key=os.path.getctime)
    return new

def meta_write(name, artist):
    with yaspin(text="Applying metadata", color="yellow") as spinner:
        metadata(file_name() , artist, name)
        head, tail = os.path.split(file_name())
        song_name = head + "\\" + name + ".mp3"
        os.rename(file_name(), song_name)
        spinner.ok("✅ ")

    with yaspin(text="Uploading to Google Drive", color="yellow") as spinner:   
        drive_up()
        spinner.ok("✅ ")
    

def link_finder():
    method = "pico"
    reddit = Tk().clipboard_get()
    with yaspin(text="Loading reddit", color="yellow") as spinner:
        try:
            driver.get(reddit)
        except InvalidArgumentException:
            spinner.fail("❌ ")
            driver.quit()
            return
        spinner.ok("✅ ")

    title = driver.title
    artist = title.split("]")[1].split(" -")[0]
    name = title.split("]")[1].split(" - ")[1]. split(" :")[0]
    with yaspin(text="Finding album art", color="yellow") as spinner:
        try:
            album_art(artist)
            spinner.ok("✅ ")
        except:
            spinner.fail("❌ ")

    if method == "pico":
        with yaspin(text="Downloading with Picosong", color="yellow") as spinner:
            try:
                pico = wait.until(EC.element_to_be_clickable(
                    (By.PARTIAL_LINK_TEXT, "picosong")))
                link = pico.get_attribute("href")
                pico_dl(link)
                spinner.ok("✅ ")
                meta_write(name, artist)
                return

            except TimeoutException:
                spinner.write("> Find by link text failed")
                pass
            try:
                pico = driver.find_element_by_xpath("//*[contains(text(), 'Picosong')]")
                link = pico.get_attribute("href")
                pico_dl(link)
                spinner.ok("✅ ")
                meta_write(name, artist)
                return 
            except TimeoutException:
                method = "sound"
                spinner.fail("❌ ")
                 

    if method == "sound":
        with yaspin(text="Downloading with Soundcloud", color="yellow") as spinner:
            try:
                driver.get(reddit)
                sound = wait.until(EC.element_to_be_clickable(
                    (By.PARTIAL_LINK_TEXT, "soundcloud")))
                link = sound.get_attribute("href")
                sound_dl(link)
                spinner.ok("✅ ")
                meta_write(name, artist)
                return
            except TimeoutException:
                spinner.write("> Find by link text failed")
            try:
                driver.get(reddit)
                sound = driver.find_element_by_xpath("//*[contains(text(), 'SoundCloud')]")
                link = sound.get_attribute("href")
                sound_dl(link)
                spinner.ok("✅ ")
                meta_write(name, artist)
                return
            except TimeoutException:
                spinner.fail("❌ ")
                method = "dbree"
 

    if method == "dbree":
        with yaspin(text="Downloading with Dbree", color="yellow") as spinner:
            try:
                driver.get(reddit)
                sound = wait.until(EC.element_to_be_clickable(
                    (By.PARTIAL_LINK_TEXT, "dbree")))
                link = sound.get_attribute("href")
                dbr_dl(link)
                spinner.ok("✅ ")
                meta_write(name, artist)
                return
            except TimeoutException:
                spinner.write("> Find by link text failed")
            try:
                driver.get(reddit)
                dbr = driver.find_element_by_xpath("//*[contains(text(), 'Dbree')]")
                link = dbr.get_attribute("href")
                dbr_dl(link)
                spinner.ok("✅ ")
                meta_write(name, artist)
            except TimeoutException:
                spinner.fail("❌ ")
                spinner.write("> Failed to find any links")
                driver.quit()



if __name__ == "__main__":
    link_finder()
