from selenium import webdriver
from selenium.webdriver.common.by import By
from time import sleep
from PageStructure import Item, Page, Collection
import pandas as pd
import unicodedata
import re

'''define driver'''
driver = webdriver.Edge()
url = 'https://memoryzone.com.vn/'
driver.get(url)

def GetText(elems: list) -> list:
    res = []
    for elem in elems:
        res.append(elem.text)
    return res

def GetItemInfoInPage(page: int) -> list[object]:
    items = []
    # === Get name ===
    names_elems = driver.find_elements(By.CSS_SELECTOR, ".product-name")
    names = GetText(names_elems)
    # print(names)
    # === Get current price (discounted price) ===
    curr_prices_elems = driver.find_elements(By.CSS_SELECTOR, ".price, .price-contact")
    curr_prices = GetText(curr_prices_elems)
    # print(curr_prices)

    # === Get original price (before discount) ===
    price_box_elems = driver.find_elements(By.CSS_SELECTOR, ".price-box")
    original_prices = []
    for elem in price_box_elems:
        price_box_child = elem.find_elements(By.XPATH, "*")
        if len(price_box_child) == 1:
            original_prices.append("")
        else:
            original_prices.append(price_box_child[1].text)
    # === Get link ===
    link_elems = driver.find_elements(By.CSS_SELECTOR, ".product-name [href]")
    links = []
    for elem in link_elems:
        link = elem.get_attribute("href").strip()
        links.append(link)
    # print(links)
    # === Get ratings ===
    ratings = []
    rating_elems = driver.find_elements(By.CSS_SELECTOR, ".aer-review-result")
    for elem in rating_elems:
        stars = elem.find_elements(By.XPATH, ".//span[@class='aer-star-active']")
        # print(stars)
        ratings.append(len(stars))
    # print(ratings)
    # === Get rate count ===
    rate_count = []
    rate_elems = driver.find_elements(By.CSS_SELECTOR, ".aer-review-result")
    for elem in rate_elems:
        elem_class = elem.get_attribute("class")
        total_count = elem_class.split()[1].strip("ae-total-")
        if total_count:
            count = int(total_count)
        else:
            count = 0
        rate_count.append(count)
    # print(len(rate_count), rate_count)
    # print(f"names: {len(names)} | cur: {len(curr_prices)} | ori: {len(original_prices)} | links: {len(links)}")
    assert len(names) == len(curr_prices) == len(original_prices) == len(links), "ERROR: len not match"
    for i in range(len(names)):
        item = Item(names[i],curr_prices[i], original_prices[i], links[i], ratings[i], rate_count[i])
        items.append(item)
    return items

def GetItemCollection(link: str) -> Collection:
    # Get title
    title = driver.find_element(By.CSS_SELECTOR, ".title_page").text
    collection = Collection(title)
    print(title)
    print("Collecting in page 1...", end=' ')
    # Get items on first page
    page1 = Page(1)
    page1.AddItem(GetItemInfoInPage(1))
    collection.AddPage(page1)
    print("Done")
    # return collection # For debugging
    # Get items in every other page
    pages = driver.find_elements(By.CSS_SELECTOR, ".page-item")
    pages_count = len(pages) # Count number of pages: get all class .page-item count then - 2 (2 arrows)
    # print(f"PAGE COUNT: {pages_count}")
    # Find the start of the ? in the url (parameters)
    pos = 26
    while pos < len(link):
        if link[pos] == "?":
            break
        pos+=1
    # Start traversing through pages
    for i in range(2, pages_count - 1):
        print(f"Collecting in page {i}...", end=' ')
        link = link[:pos+1] + "page=" + str(i)
        # print(link)
        driver.get(link)
        sleep(2)
        page = Page(i)
        page.AddItem(GetItemInfoInPage(i))
        collection.AddPage(page)
        print("Done")
    return collection

def GetCollectionLinks() -> list[str]:
    link_product = []
    product_types = driver.find_elements(By.CSS_SELECTOR, ".item.slick-slide [href]")
    for type in product_types:
        link = type.get_attribute("href")
        if link not in link_product:
            link_product.append(link)
    if not link_product:
        product_types = driver.find_elements(By.CSS_SELECTOR, ".collections-slide [href]")
        for type in product_types:
            link = type.get_attribute("href")
            if link not in link_product:
                link_product.append(link)
    return link_product    

def FormatTitle(title: str) -> str:
    # Normalize the Unicode string and remove diacritics (accents)
    normalized = unicodedata.normalize('NFD', title)
    without_diacritics = ''.join([c for c in normalized if unicodedata.category(c) != 'Mn'])
    
    # Convert to lowercase
    lowercase = without_diacritics.lower()
    
    # Replace spaces and special characters with hyphens
    ret = re.sub(r'[\s/]+', '-', lowercase)
    
    # Remove any non-alphanumeric characters except hyphens
    ret = re.sub(r'[^a-z0-9-]', '', ret)
    
    return ret

def ToJSON(collections: list):
    for collection in collections:
        title = collection.title
        # print(title, FormatTitle(title))
        df = collection.ToDataFrame()
        with open(f'./JSON/{FormatTitle(title)}.json', 'w', encoding='utf-8') as file:
            df.to_json(file, force_ascii=False, orient='index')
def ToCSV(collections: list):
    for collection in collections:
        title = collection.title
        # print(title, FormatTitle(title))
        df = collection.ToDataFrame()
        df.to_csv(f'./CSV/{FormatTitle(title)}.csv', sep='\t', encoding='utf-8', header=True, index=False)

def main():
    link_collections = GetCollectionLinks()
    collections = []
    for link in link_collections[1:]:
        driver.get(link)
        # print(link)
        sleep(5)
        link = driver.current_url
        # print(link)
        collections.append(GetItemCollection(link))
        ToJSON(collections)
        ToCSV(collections)
    count = 0
    for collection in collections:
        count += collection.GetPageCount()

if __name__ == "__main__":
    main()