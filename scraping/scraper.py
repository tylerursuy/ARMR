from selenium import webdriver
from bs4 import BeautifulSoup
import requests
import time


def specialties(link):
    """Get all specialties from transcription website."""
    specialties_page = requests.get(link)
    soup = BeautifulSoup(specialties_page.content, "html.parser")
    specialties_ = soup.find_all("span", {
        "class": "collapsing categories expand"})
    specialty_list = [sp.find("a").text for sp in specialties_]
    return specialty_list


def get_transcriptions(link):
    """Get all transcriptions from website"""
    driver = webdriver.Chrome()
    driver.get(link)
    categories = driver.find_elements_by_css_selector(
        "span.collapsing.categories.expand")
    for cat in categories:
        driver.execute_script("return arguments[0].scrollIntoView();", cat)
        time.sleep(0.5)
        expander = cat.find_element_by_css_selector("span.sym")
        expander.click()
    transcription_items = driver.find_elements_by_css_selector(
        "li.collapsing.categories.item")
    transcription_links = [item.find_element_by_tag_name("a").get_attribute(
        "href") for item in transcription_items]
    transcriptions = []
    start = time.time()
    for i in range(len(transcription_links)):
        page = requests.get(transcription_links[i])
        soup = BeautifulSoup(page.content, "html.parser")
        content = soup.find("div", {"class": "post-content"})
        title = content.find("h1").text
        transcription = content.find_all("p")
        text = [txt.text for txt in transcription]
        transcriptions.append((title, text))
        if i % 100 == 0:
            check_in = time.time()
            print(i)
            print((check_in - start) / 60)
    end = time.time()
    print(end - start)
    return transcriptions


page_link = "http://www.medicaltranscriptionsamples.com/specialities/"
transcription_data = get_transcriptions(page_link)

with open("transcriptions.txt", "w") as file:
    for trn in transcription_data:
        file.write(trn[0] + "--" + "--".join(trn[1]) + "***")
