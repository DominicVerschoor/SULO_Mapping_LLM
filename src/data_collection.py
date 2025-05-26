import requests
from bs4 import BeautifulSoup
import json
import time

def scrape_page(url, property=False):
    resp = requests.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    data = {}
    # 1) Label is now in the top‐level <h1>
    h1 = soup.find("h1")
    if h1:
        # strip out any <small> text if present
        label_text = h1.get_text(" ", strip=True).split(" ")[0]
        if property:
            data["SULO Property"] = label_text
        else:
            data["SULO Class"] = label_text

    # 2) Description still lives in the panel
    for panel in soup.select("div.panel.panel-default"):
        title_el = panel.select_one("h3.panel-title")
        if title_el and title_el.get_text(strip=True) == "Description":
            body_el = panel.select_one("div.panel-body")
            data["description"] = body_el.get_text(strip=True) if body_el else ""
            break
        
    return data


def scrape_multiple(base_url_pattern, urls, property=False, delay=1):
    """Loop over pages, collect all items, return flattened list."""
    all_items = []
    for i in urls:
        url = base_url_pattern.format(url=i)
        print(f"Scraping {url}")
        try:
            if property:
                page_items = scrape_page(url, property=True)
            else:
                page_items = scrape_page(url, property=False)
        except requests.HTTPError as e:
            print(f" -> skipped (status {e.response.status_code})")
            continue
        all_items.append(page_items)
        time.sleep(delay)  # be polite
    return all_items


if __name__ == "__main__":
    classes = [
        "suloCapability",
        "suloDuration",
        "suloEndTime",
        "suloFeature",
        "suloInformationObject",
        "suloObject",
        "suloProcess",
        "suloQuality",
        "suloQuantity",
        "suloRole",
        "suloSet",
        "suloSpatialObject",
        "suloStartTime",
        "suloTime",
        "suloTimeInstant",
        "suloTimeInterval",
        "suloUnit",
    ]
    
    properties = [
        "suloatTime",
        "sulohasDirectPart",
        "sulohasFeature",
        "sulohasMember",
        "sulohasPart",
        "sulohasParticipant",
        "sulohasValue",
        "suloisDirectPartOf",
        "suloisFeatureOf",
        "suloisItemIn",
        "suloisLocatedIn",
        "suloisLocationOf",
        "suloisPartOf",
        "suloisParticipantIn",
        "suloisPrecededBy",
        "suloisReferredIn",
        "suloisTimeOf",
        "suloprecedes",
        "sulorefersTo",
    ]
    # https://aidava-dev.github.io/sulo/class-suloCapability.html
    class_urls = ['class-' + class_name + '.html' for class_name in classes]
    properties_urls = ['prop-' + class_name + '.html' for class_name in properties]

    data_cl = scrape_multiple(
        base_url_pattern="https://aidava-dev.github.io/sulo/{url}",
        urls=class_urls,
        property=False,
        delay=0.5,
    )
    
    data_prop = scrape_multiple(
        base_url_pattern="https://aidava-dev.github.io/sulo/{url}",
        urls=properties_urls,
        property=True,
        delay=0.5,
    )

    data = data_cl + data_prop

    # write out
    with open("data/data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
