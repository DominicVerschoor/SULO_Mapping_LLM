import requests
from bs4 import BeautifulSoup
import json
import time

def scrape_page(url, property=False):
    resp = requests.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    data = {}

    # 1) LABEL (always in <h1> on SULO pages)
    h1 = soup.find("h1")
    if h1:
        # strip out any <small>...</small> if present, e.g. "sulo:Capability <small>…</small>"
        label_text = h1.get_text(" ", strip=True).split(" ")[0]
        if property:
            data["SULO Property"] = label_text
        else:
            data["SULO Class"] = label_text

    # 2) DESCRIPTION (panel-heading “Description”)
    for panel in soup.select("div.panel.panel-default"):
        title_el = panel.select_one("h3.panel-title")
        if title_el and title_el.get_text(strip=True) == "Description":
            body_el = panel.select_one("div.panel-body")
            data["description"] = body_el.get_text(" ", strip=True) if body_el else ""
            break

    if not property:
        header_tr = soup.select_one("tr.table-classproperties")
        data["usedProperties"] = []
        if header_tr:
            current_row = header_tr.find_next_sibling("tr")
            while current_row:
                tds = current_row.find_all("td")
                if len(tds) == 4:
                    prop = tds[0].get_text(" ", strip=True)
                    prop_type = tds[1].get_text(" ", strip=True)
                    description = tds[2].get_text(" ", strip=True)
                    range_text = tds[3].get_text(" ", strip=True)

                    if prop.startswith('sulo'):
                        data["usedProperties"].append({
                            "property": prop,
                            "type": prop_type,
                            "description": description,
                            "range": range_text
                        })

                elif len(tds) == 1:
                    # Section header like "From class sulo:Process" — can optionally parse it if needed
                    pass

                current_row = current_row.find_next_sibling("tr")



    # 3) DOMAIN & RANGE (only if this is a property page)
    if property:
        # Look for that table whose header row has class="table-classproperties"
        header_tr = soup.select_one("tr.table-classproperties")
        if header_tr:
            # The next <tr> will contain three <td> columns: [DOMAIN] [PROPERTY] [RANGE]
            next_row = header_tr.find_next_sibling("tr")
            if next_row:
                tds = next_row.find_all("td")
                if len(tds) >= 3:
                    # Use get_text(" ", strip=True) so "owl:Thing" + " (inferred)" become "owl:Thing (inferred)"
                    domain_text = tds[0].get_text(" ", strip=True)
                    range_text  = tds[2].get_text(" ", strip=True)

                    # Only insert if we actually found text
                    if domain_text:
                        data["domain"] = [domain_text]
                    if range_text:
                        data["range"] = [range_text]

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
        delay=0.2,
    )
    
    data_prop = scrape_multiple(
        base_url_pattern="https://aidava-dev.github.io/sulo/{url}",
        urls=properties_urls,
        property=True,
        delay=0.2,
    )

    data = data_cl + data_prop

    # write out
    with open("data/sulo_data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
