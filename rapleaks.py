import glob
import os
import time
import sys
import magic
import logging
import msvcrt
from tkinter import Tk
from yaspin import yaspin
from selenium import webdriver
from mutagen.id3 import ID3, APIC
from mutagen.easyid3 import EasyID3
from pydrive.auth import GoogleAuth
from yaspin.spinners import Spinners
from pydrive.drive import GoogleDrive
from colorama import init, Fore, Style
from selenium.webdriver.common.by import By
from oauth2client import file, client, tools
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import InvalidArgumentException
from selenium.webdriver.support import expected_conditions as EC

# Program created to automaticaly download rap leaks songs. The end goal would be to have is scan reddit and open posts, then automatically click and navigate the links to download files.

# Constants
dl_location = r"C:\Users\isaac\Documents\SoundDL"   # location for song dL
fid = "1-9HbOEJhzVIRQ4wyglgEVkB9-xqHft5C"           # "Leak" folder ID
spinner = yaspin()                                  # Used for loading icon
init()                                              # allows for ANSI colours in console

# Webdriver
options = Options()                                    
options.add_experimental_option('excludeSwitches', ['enable-logging'])
prefs = {'download.default_directory': dl_location} # Sets DL location
options.add_experimental_option('prefs', prefs)
driver = webdriver.Chrome(executable_path=r"C:\Users\isaac\Desktop\SounDL\chromedriver.exe", options=options)
driver.minimize_window()                        
wait = WebDriverWait(driver, 4)                     


def download_wait(path_to_downloads):               # checks path to DL if a file ends with .crdownload. Is used to close the webdriver when the program finishes
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


def sound_dl(link):                                 # uses selenium to open soundcloud downloader website and paste in the soundcloud link for download.
    driver.get('https://scdownloader.io/')          # Not optimal

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

        if(len(result) > 0):                       # finds list of elements and clicks the first one. 
            result[0].click()
            driver.minimize_window()
            download_wait(dl_location)
            driver.quit()
            return
        else:
            raise TimeoutException
    except TimeoutException:
        raise


def pico_dl(link):                              # uses selenium to download off of picosong
    driver.get(link)
    try:
        box = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//ul[@id='audio-actions']/li/a"))) # first DL button
    except TimeoutException:
        raise

    box.click()
    dl = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//div[@id='content']/div[2]/div/div/h3/a/strong"))) # second DL button
    dl.click()
    driver.minimize_window()
    download_wait(dl_location)
    driver.quit()

    

def dbr_dl(link):                                       # uses selenium to download from Dbree
    driver.get(link)
    try:
        driver.implicitly_wait(5)                       # implicit wait because of 5 second wait timer when accessing website
        box = wait.until(EC.element_to_be_clickable(
            (By.LINK_TEXT, "Download")))
        box.click()
        driver.minimize_window()

    except TimeoutException:
        raise
    download_wait(dl_location)
    driver.quit()
    return


def drive_up():                                 # Google Drive API to upload most recent file found in DL folder found using glob.
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


def album_art(artist, name):    # sacad is used to find album art by searching the artist title
    os.chdir(r"C:\Users\isaac\Desktop\SounDL")
    os.system("sacad " + '"' + artist + '"' + ' "' + "" + '" ' + '"' + "600" '" ' + '"' + artist + " - " +  name + ".jpg" + '"')


def metadata(file_name, artist, title):     # easyID3 and ID3 are used to write metadata tags and apply album art found using sacad
    audio = EasyID3(file_name)
    audio['artist'] = artist
    audio['title'] = title
    audio.save()
    
    audio = ID3(file_name)
    with open(artist + " - " + title + ".jpg", 'rb') as albumart:
        audio['APIC'] = APIC(
                          encoding=3,
                          mime='image/jpeg',
                          type=3, desc=u'Cover',
                          data=albumart.read()
                        )            
    audio.save()

def file_name():        # finds the most recent file using glob
    list_of_files = glob.glob('C:\\Users\\isaac\\Documents\\SoundDL\\*')
    new = max(list_of_files, key=os.path.getctime)
    return new

def meta_write(name, artist):   #calls metadata() and renmaes mp3
    with yaspin(text="Applying metadata", color="cyan") as spinner:
        metadata(file_name() , artist, name)
        head, tail = os.path.split(file_name())
        song_name = head + "\\" + artist + " - " + name + ".mp3"
        os.rename(file_name(), song_name)
        spinner.ok("✅ ")

    with yaspin(text="Uploading to Google Drive", color="cyan") as spinner:   
        drive_up()
        spinner.ok("✅ ")
    

def link_finder():      # finds links on reddit posts by searching for the DL download links      
    method = "pico"
    reddit = Tk().clipboard_get()
    with yaspin(text="Loading reddit", color="cyan") as spinner:
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
    with yaspin(text="Finding album art", color="cyan") as spinner:
        try:
            album_art(artist, name)
            spinner.ok("✅ ")
        except:
            spinner.fail("❌ ")

    if method == "pico":
        with yaspin(text="Downloading with Picosong", color="cyan") as spinner:
            try:
                pico = wait.until(EC.element_to_be_clickable(
                    (By.PARTIAL_LINK_TEXT, "picosong")))
                link = pico.get_attribute("href")
                pico_dl(link)
                spinner.ok("✅ ")
                meta_write(name, artist)
                return

            except TimeoutException:
                spinner.write(">Find by link text failed")
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
        with yaspin(text="Downloading with Soundcloud", color="cyan") as spinner:
            try:
                driver.get(reddit)
                sound = wait.until(EC.element_to_be_clickable(
                    (By.PARTIAL_LINK_TEXT, "soundcloud")))
                link = sound.get_attribute("href")
                os.chdir(r"C:\Users\isaac\Documents\SoundDL")
                os.system("scdl -l " + Tk().clipboard_get())
                os.chdir(r"C:\Users\isaac\Desktop\SounDL")
                spinner.ok("✅ ")
                with yaspin(text="Uploading to Google Drive", color="cyan") as spinner:   
                    drive_up()
                    spinner.ok("✅ ")
            except TimeoutException:
                spinner.write(">Find by link text failed")
            try:
                driver.get(reddit)
                sound = driver.find_element_by_xpath("//*[contains(text(), 'SoundCloud')]")
                link = sound.get_attribute("href")
                os.chdir(r"C:\Users\isaac\Documents\SoundDL")
                os.system("scdl -l " + Tk().clipboard_get())
                os.chdir(r"C:\Users\isaac\Desktop\SounDL")
                spinner.ok("✅ ")
                with yaspin(text="Uploading to Google Drive", color="cyan") as spinner:   
                    drive_up()
                    spinner.ok("✅ ")
                    return
            except TimeoutException:
                spinner.fail("❌ ")
                method = "dbree"
 

    if method == "dbree":
        with yaspin(text="Downloading with Dbree", color="cyan") as spinner:
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
                spinner.write(">Find by link text failed")
            try:
                driver.get(reddit)
                dbr = driver.find_element_by_xpath("//*[contains(text(), 'Dbree')]")
                link = dbr.get_attribute("href")
                dbr_dl(link)
                spinner.ok("✅ ")
                meta_write(name, artist)
            except TimeoutException:
                spinner.fail("❌ ")
                spinner.write(">Failed to find any links")
                driver.quit()

def user_input():       # UI to facilitate using whochever download means necesssary
    print("[1]: " + Fore.MAGENTA + Style.BRIGHT + "Reddit" + Style.RESET_ALL + " Download")
    print("[2]: " + Fore.YELLOW + Style.DIM + "Soundcloud" + Style.RESET_ALL  + " Download")
    print("[3]: " + Fore.GREEN + Style.DIM + "Picosong" + Style.RESET_ALL + " Download")
    print("[4]: " + Fore.BLUE + "Dbree" + Fore.RESET +  " Download")
    print("\n[5]: " + Fore.RED + "Exit" + Fore.RESET)
    option = msvcrt.getche()
    os.system("cls")
    while option != b"5":
        if option == b"1":
            option = "5"
            link_finder()
        
        elif option == b"2":
            option = b"5"
            with yaspin(text="Downloading with Soundcloud", color="cyan") as spinner:
                driver.quit()
                os.chdir(r"C:\Users\isaac\Documents\SoundDL")
                os.system("scdl -l " + Tk().clipboard_get())
                os.chdir(r"C:\Users\isaac\Desktop\SounDL")
                spinner.ok("✅ ")
                with yaspin(text="Uploading to Google Drive", color="cyan") as spinner:   
                    drive_up()
                    spinner.ok("✅ ")
                
                
        elif option == b"3":
            option = b"5"
            with yaspin(text="Downloading with Picosong", color="cyan") as spinner:
                try:
                    driver.get(Tk().clipboard_get())
                    name = wait.until(EC.visibility_of_element_located((By.XPATH, "//div[@id='song-info']/table/tbody/tr/td[2]"))).text
                    artist = driver.find_element_by_xpath("//div[@id='song-info']/table/tbody/tr[2]/td[2]").text
                    pico_dl(Tk().clipboard_get())
                    spinner.ok("✅ ")
                    with yaspin(text="Finding album art", color="cyan") as spinner:
                        album_art(artist, name)
                        spinner.ok("✅ ")

                    meta_write(name, artist)
                    spinner.write(artist + " - " + name + " downloaded.")   
                except (TimeoutException, InvalidArgumentException) as n:
                    spinner.fail("❌ ")
                    driver.quit()
                    return print("Exception" + str(n) + "thrown.")
        
        elif option == b"4":
            option = b"5"
            with yaspin(text="Downloading with Dbree", color="cyan") as spinner:
                try:
                    dbr_dl(Tk().clipboard_get())
                    spinner.ok("✅ ")
                    with yaspin(text="Finding album art", color="cyan") as spinner:
                        album_art(artist, name)
                        spinner.ok("✅ ")

                        meta_write(name, artist)
                        spinner.write(artist + " - " + name + " downloaded.")   
                    with yaspin(text="Uploading to Google Drive", color="cyan") as spinner:   
                        drive_up()
                        spinner.ok("✅ ")
                except (TimeoutException, InvalidArgumentException) as n:
                    spinner.fail("❌ ")
                    driver.quit()
                    return print("Exception" + str(n) + "thrown.")

        elif option == b"5":
            driver.quit()
            return
        
        else:
            driver.quit()
            option = msvcrt.getche("Undefined input, try again!")

if __name__ == "__main__":
    user_input()