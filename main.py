import asyncio
import json
import random
import re
import time

import requests
import undetected_chromedriver
from bs4 import BeautifulSoup

#some proxies
http1 = "http://185.162.230.10:80"
http2 = "http://185.162.229.47:80"

PROXIES_1 = {
    "http" : http1,
}
PROXIES_2 = {
    "http" : http2,
}

# headers for requests
HEADERS = {
    "Accept": "*/*",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36",
}

#for time sleep
time_const1 = 1.5
time_const2 = 3

SUCCESS = 0
FAILURE = 1

#CONSTANTS
CIAN = "https://www.cian.ru/"

LOCATION_CLASS = "a10a3f92e9--link--ulbh5 a10a3f92e9--address-item--ScpSN"
UNDERGROUND_NAME_CLASS = "a10a3f92e9--underground_link--Sxo7K"
UNDERGROUND_TIME_CLASS = "a10a3f92e9--underground_time--iOoHy"
PRICE_CLASS = "a10a3f92e9--price_value--lqIK0"
PRICE_PER_METRE_CLASS = "a10a3f92e9--color_gray60_100--MlpSF a10a3f92e9--lineHeight_5u--cJ35s a10a3f92e9--fontWeight_normal--P9Ylg a10a3f92e9--fontSize_14px--TCfeJ a10a3f92e9--display_block--pDAEx a10a3f92e9--text--g9xAG a10a3f92e9--text_letterSpacing__0--mdnqq a10a3f92e9--text_whiteSpace__nowrap--Akbtc"
OBJECT_SUMMARY_DESCRIPTION_TITLE_CLASS = "a10a3f92e9--info-title--JWtIm"
OBJECT_SUMMARY_DESCRIPTION_VALUE_CLASS = "a10a3f92e9--info-value--bm3DC"
ADDITIONAL_INFO_TITLE_CLASS = "a10a3f92e9--name--x7_lt"
ADDITIONAL_INFO_VALUE_CLASS = "a10a3f92e9--value--Y34zN"
ABOUT_BUILDING_TITLE_CLASS = "a10a3f92e9--name--pLPu9"
ABOUT_BUILDING_VALUE_CLASS = "a10a3f92e9--value--G2JlN"

BASE_1_FLAT_URL = "https://www.cian.ru/kupit-1-komnatnuyu-kvartiru-vtorichka-"
LINK_TO_NEXT_PAGE_CLASS = "_93444fe79c--list-itemLink--BU9w6"
LINK_TO_FLAT_CLASS = "_93444fe79c--link--eoxce"
SUM_HEADER_CLASS = "_93444fe79c--header--BEBpX"
MAIN_PAGE_UNDERGROUND_CLASS = "_025a50318d--c-geo-link--P1DwD"

def web_scrap_urls_to_underground(url: str, proxies: dict):
    """
        This function opens main cian web page and takes all the links to flats near undergrounds
        url must be cian.ru
    """
    print(f"Getting undergrounds from {url}")

    try:
        response = requests.get(url, headers=HEADERS, proxies=proxies)
        if(response.status_code != 200):
            print(f"Returned with {response.status_code} status code.")
            return FAILURE
    except Exception:
        print("Bad url")
        return FAILURE

    src = response.text
    soup = BeautifulSoup(src, "lxml")

    try:
        elements = soup.find_all(class_=MAIN_PAGE_UNDERGROUND_CLASS)[:300]
    except Exception:
        return FAILURE

    for i in range(len(elements)):
        elements[i] = elements[i].get("href").strip()
        idx = elements[i].find("moskva")
        elements[i] = elements[i][idx:]

    with open("underground_links.txt","w") as file:
        for element in elements:
            file.write(element + "\n")

    return SUCCESS

def web_scrap_urls_to_flats(base_url: str, url: str, proxies: dict) -> list:
    """
        This function takes a base_url like: https://www.cian.ru/kupit-1-komnatnuyu-kvartiru-vtorichka-
        and url like: moskva-metro-aviamotornaya/
        Makes requests to base_url + url and then
        It searches links to flats via BeautifulSoup then returns the list of found links.
    """
    print(f"web_scrap_urls_to_flats() called with url: {url}")

    time.sleep(random.uniform(time_const1, time_const2)) 

    try:
        response = requests.get(base_url + url, headers=HEADERS, proxies=proxies)
        if(response.status_code != 200):
            print(f"{response.status_code} returned")
            return []
    except Exception:
        print("Initially wrong url of bad connection (check proxies)")
        return []

    src = response.text
    soup = BeautifulSoup(src, "lxml")

    try:
        sum_header = soup.find(class_=SUM_HEADER_CLASS).find("h5").text
    except Exception:
        print("sum_header gets error - CAPTCHA HIGH PROBOBILITY")
        return []

    sum_header = re.findall(r"\d+", sum_header)[0]
    sum_header = int(sum_header)
    if int(sum_header) > 1350:
        sum_header = 1350
    num_of_pages = int(sum_header) // 25

    link_to_next_page = None
    try:
        link_to_next_page = soup.find(class_=LINK_TO_NEXT_PAGE_CLASS).get("href")
        index = link_to_next_page.find("p=2")
        link_to_next_page = link_to_next_page[:index+2] + "_p_" + link_to_next_page[index+3:]
    except Exception:
        None

    print(f"Should be {sum_header} flat(s).")
    print("Getting links from #1 page.")

    links = []
    copy_count = 25
    if(sum_header < 25):
        copy_count = sum_header
    try:
        temp_links = soup.find_all(class_=LINK_TO_FLAT_CLASS)[:copy_count]
    except Exception:
        print("first try of getting flats gets error")
        return []

    for i in range(len(temp_links)):
        temp_links[i] = temp_links[i].get("href")

    links += temp_links

    if(link_to_next_page is None or sum_header <= 25):
        None
    else:
        current_sum = sum_header - 25

        for i in range(2, num_of_pages+1):
            try:
                response = requests.get(
                    link_to_next_page.replace("_p_", str(i)), 
                    headers=HEADERS, 
                    proxies=proxies
                    )
            except Exception:
                print(f"Wrong page {i} number")
                break

            print(f"Getting links from #{i} page.")

            src = response.text
            soup = BeautifulSoup(src, "lxml")

            if(current_sum < 25):
                difference = current_sum
            elif current_sum >= 25:
                difference = (current_sum - 25)
            current_sum -= 25

            try:
                temp_links = soup.find_all(class_=LINK_TO_FLAT_CLASS)[:difference]
            except Exception:
                print(f"#{i} page gets error while getting flats")
                break
            for i in range(len(temp_links)):
                temp_links[i] = temp_links[i].get("href")

            links += temp_links
            time.sleep(random.uniform(time_const1, time_const2))
    print(f"Found {len(links)} flat(s).")
    return links

async def web_scrap_flat_urls(url: str, driver, idx: int):
    """
        This function opens a flat url via selenium (using undetected_chromedriver)
        and then reads an html source of url, searches for needed params and returns dict of them
    """
    print(f"web_scrap_cian_urls() called with url: {url}")
    
    try:
        driver.switch_to.window(driver.window_handles[0])
        driver.execute_script(f"window.open('{url}');")
        await asyncio.sleep(10)
        driver.switch_to.window(driver.window_handles[idx])
        response = driver.page_source
        src = response
    except Exception:
        print("Wrong url")
        return {}

    soup = BeautifulSoup(src, "lxml")

    result = {}

    try:
        elements = soup.find_all(class_=LOCATION_CLASS)
        for i in range(len(elements)):
            elements[i] = elements[i].text.strip()

        result['city'] = elements[0]
        result['ao'] = elements[1]
        result['district'] = elements[2]
        result['street'] = elements[3]
        result['street_number'] = elements[4]  

        elements = soup.find(class_=PRICE_CLASS).find("span").text
        elements = elements.replace("\xa0", "").replace("₽", "")
        result['price'] = elements

        elements = soup.find(class_=PRICE_PER_METRE_CLASS).text
        elements = elements.replace("\xa0", "").replace("₽/м²", "").replace(" ", "")
        result['price_per_metre'] = elements

        temp_dict = {}

        elements = soup.find_all(class_=UNDERGROUND_NAME_CLASS)
        elements2 = soup.find_all(class_=UNDERGROUND_TIME_CLASS)

        for i in range(len(elements)):
            try:
                temp_dict[elements[i].text.strip()] = elements2[i].text.strip()[3:]
            except Exception:
                pass

        result["metro"] = temp_dict

        elements = soup.find_all(class_=OBJECT_SUMMARY_DESCRIPTION_TITLE_CLASS)
        elements2 = soup.find_all(class_=OBJECT_SUMMARY_DESCRIPTION_VALUE_CLASS)

        for i in range(len(elements)):
            result[elements[i].text.strip()] = elements2[i].text.strip().replace("\xa0", " ")

        elements = soup.find_all(class_=ADDITIONAL_INFO_TITLE_CLASS)
        elements2 = soup.find_all(class_=ADDITIONAL_INFO_VALUE_CLASS)

        for i in range(len(elements)):
            result[elements[i].text.strip()] = elements2[i].text.strip()

        elements = soup.find_all(class_=ABOUT_BUILDING_TITLE_CLASS)
        elements2 = soup.find_all(class_=ABOUT_BUILDING_VALUE_CLASS)

        for i in range(len(elements)):
            result[elements[i].text.strip()] = elements2[i].text.strip()

    except Exception:
        print("Reaing src error")
        return {}
    result = {
        url: result
    }

    return result

def pre_main():
    result = web_scrap_urls_to_underground(CIAN, PROXIES_1)
    if result == FAILURE:
        return FAILURE

    links = []
    with open("underground_links.txt") as file:
        links = file.readlines()

    for i in range(len(links)):
        links[i] = links[i].strip()

    proxies = PROXIES_1

    final_links = []
    for link in links:
        temp_links = web_scrap_urls_to_flats(BASE_1_FLAT_URL, link, proxies)
        if len(temp_links) == 0:
            proxies = PROXIES_2
        final_links += temp_links

    final_links_temp = set(final_links)
    final_links = []
    for final_link in final_links_temp:
        if final_link[12] != "c":
            continue
        final_links.append(final_link)

    with open("flat_links.txt","w") as file:
        for final_link in final_links:
            file.write(final_link + "\n")

async def main():
    print("main() called")

    links = []
    with open("flat_links.txt") as file:
        links = file.readlines()

    for i in range(len(links)):
        links[i] = links[i].strip()

    driver = undetected_chromedriver.Chrome()
    result = {}

    size_of_scrap = 10

    try:
        for i in range(0, len(links), size_of_scrap):
            temp_result = await asyncio.gather(*(web_scrap_flat_urls(links[j], driver, size_of_scrap-idx) for idx, j in enumerate(range(i, i+size_of_scrap))))
            for i in range(len(driver.window_handles)-1, 0, -1):
                driver.switch_to.window(driver.window_handles[i])
                driver.close()
            for res in temp_result:
                result.update(res)
    except Exception:
        print("Error in main loop")
    finally:
        time.sleep(5)
        driver.quit()

    print(f"{len(result)} of {len(links)} link(s) successfully read.")

    with open("ready.json", "w") as file:
        json.dump(result, file, indent=4, ensure_ascii=False)

if __name__ == '__main__':
    s = time.perf_counter()
    result = pre_main()             # Prepares all the links of flats
    if result == FAILURE:
        print("pre_main() failed")  
    else:    
        asyncio.run(main())         # Reads all the links of flats and makes json output
    elapsed = time.perf_counter() - s
    print(f"{__file__} executed in {elapsed:0.2f} seconds.")