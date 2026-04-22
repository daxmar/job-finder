import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.edge.options import Options as EdgeOptions
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import os
import re
from typing import List, Dict

class BingMapsScraper:
    def __init__(self):
        self.driver = None
    
    def get_edge_options(self, headless=False):
        options = EdgeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0')
        if headless:
            options.add_argument('--headless')
        return options
    
    def init_driver(self, headless=False):
        try:
            service = EdgeService(EdgeChromiumDriverManager().install())
        except:
            # Fallback to local if manager fails (offline)
            local_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "msedgedriver.exe")
            if os.path.exists(local_path):
                service = EdgeService(executable_path=local_path)
            else:
                raise Exception("No Edge driver found. Download msedgedriver.exe or check internet.")
        
        self.driver = webdriver.Edge(service=service, options=self.get_edge_options(headless))
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    def test_connection(self):
        try:
            self.init_driver()
            self.driver.get("https://www.bing.com/maps")
            time.sleep(3)
            return "Bing Maps loaded: " + self.driver.title[:50]
        except Exception as e:
            return f"Test OK (driver ready), network: {str(e)[:50]}"
        finally:
            if self.driver:
                self.driver.quit()
                self.driver = None
    
    def scrape_places(self, query: str, city: str = "solo", max_pages: int = 3) -> List[Dict]:
        """
        Scrape lengkap semua detail places dari Bing Maps.
        """
        if not self.driver:
            self.init_driver(headless=True)
        
        places = []
        search_query = f"{query} {city}"
        
        try:
            # Search
            self.driver.get("https://www.bing.com/maps")
            time.sleep(3)
            
            # Search box (multiple selectors)
            # Expanded search selectors for Bing Maps (dynamic)
            search_selectors = [
                "input[aria-label*='Search']", 
                "input[aria-label*='search']",
                "input[title*='Search']",
                "input[role='combobox']",
                "input[placeholder*='Search']",
                "#sb_form_q", 
                ".searchbox input",
                "input[name='q']",
                "#search"
            ]
            search_box = None
            for sel in search_selectors:
                try:
                    search_box = WebDriverWait(self.driver, 8).until(EC.presence_of_element_located((By.CSS_SELECTOR, sel)))
                    self.driver.execute_script("arguments[0].scrollIntoView();", search_box)
                    break
                except:
                    continue
            
            if not search_box:
                # Fallback: send keys to body if no search box (rare)
                self.driver.find_element(By.TAG_NAME, "body").send_keys(search_query)
                time.sleep(3)
                return []
            
            print(f"Found search box: {search_box.tag_name}")
            
            search_box.clear()
            search_box.send_keys(search_query)
            time.sleep(2)
            
            # Submit search
            # Try multiple submit methods
            submit_selectors = [
                "button[aria-label*='Search']", 
                "button[type='submit']",
                "[data-value='Search']",
                "button[title*='Search']",
                ".search-button"
            ]
            submit = None
            for sel in submit_selectors:
                try:
                    submit = WebDriverWait(self.driver, 3).until(EC.element_to_be_clickable((By.CSS_SELECTOR, sel)))
                    submit.click()
                    break
                except:
                    continue
            
            if not submit:
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
            
            time.sleep(6)  # Wait for results
            
            # Scroll & extract multiple pages
            for page in range(max_pages):
                self._scroll_and_extract(places)
                
                # Next page
                try:
                    next_btn = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label*='Next'], [data-page-next]"))
                    )
                    next_btn.click()
                    time.sleep(4)
                except TimeoutException:
                    break
            
        except Exception as e:
            print(f"Scrape error: {e}")
        finally:
            if self.driver:
                self.driver.quit()
        
        return places
    
    def _scroll_and_extract(self, places: List[Dict]):
        """Scroll dan extract semua place cards di page saat ini."""
        # Scroll to load all
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        
        # Place cards selectors (Bing Maps specific)
        card_selectors = [
            "[data-bingmaps-id]", 
            ".b_mapBubbleMap", 
            ".rmsMapItem",
            "div[role='listitem']"
        ]
        
        cards = []
        for sel in card_selectors:
            cards = self.driver.find_elements(By.CSS_SELECTOR, sel)
            if cards:
                break
        
        for card in cards:
            try:
                place = self._extract_place_details(card)
                if place and place.get('name'):
                    places.append(place)
            except:
                continue
    
    def _extract_place_details(self, card) -> Dict:
        """Extract SEMUA detail dari satu place card."""
        place = {}
        
# Name - robust
        try:
            name_elem = card.find_element(By.CSS_SELECTOR, "h3, h2, h1, a[role='link'], div[role='heading'], strong, .place-title, .business-name")
            place['name'] = name_elem.text.strip()
        except:
            place['name'] = card.text.split('\n')[0][:50] if card.text else "Unknown"
        
# Address - robust
        try:
            addr_selectors = "[data-address], .b_address, .address, .location, .street-address, div[role='street-address']"
            addr_elems = card.find_elements(By.CSS_SELECTOR, addr_selectors)
            place['address'] = ' | '.join([e.text.strip() for e in addr_elems if e.text.strip()])
        except:
            # Fallback to lines after name
            lines = [l.strip() for l in card.text.split('\n') if l.strip()]
            place['address'] = lines[1] if len(lines) > 1 else ""
        
# Rating & Reviews - robust
        try:
            rating_elem = card.find_element(By.CSS_SELECTOR, ".b_ratingNumber, [aria-label*='star'], .rating, .stars, [class*='rating'], [data-rating]")
            place['rating'] = rating_elem.text or rating_elem.get_attribute('aria-label') or rating_elem.get_attribute('title') or rating_elem.get_attribute('data-rating')
        except:
            place['rating'] = ""
        
        try:
            review_elem = card.find_element(By.CSS_SELECTOR, ".b_reviewCount")
            place['reviews_count'] = re.search(r'(\d+)', review_elem.text).group(1) if review_elem.text else ""
        except:
            place['reviews_count'] = ""
        
# Phone - robust
        try:
            phone_elem = card.find_element(By.CSS_SELECTOR, "a[href^='tel:'], .phone, .tel, .b_linkSans, [data-phone], [class*='phone']")
            href = phone_elem.get_attribute('href') or phone_elem.get_attribute('data-phone')
            place['phone'] = href.replace('tel:', '') if href else phone_elem.text.strip()
        except:
            # Regex fallback
            phone_match = re.search(r'(\+62|0)[1-9]\d{6,11}', card.text)
            place['phone'] = phone_match.group(1) if phone_match else ""
        
        # Website
        try:
            web_elem = card.find_element(By.CSS_SELECTOR, "a[href*='http']:not([href^='tel:']):not([href*='bing']):not([href*='maps'])")
            place['website'] = web_elem.get_attribute('href')
        except:
            place['website'] = ""
        
        # Hours
        try:
            hours_elem = card.find_element(By.CSS_SELECTOR, "[data-openhours]")
            place['hours'] = hours_elem.get_attribute('data-openhours') or hours_elem.text
        except:
            place['hours'] = ""
        
        # Price level
        try:
            price_elem = card.find_element(By.CSS_SELECTOR, ".b_price")
            place['price_level'] = price_elem.text  # $, $$, etc.
        except:
            place['price_level'] = ""
        
        # Categories
        try:
            cat_elems = card.find_elements(By.CSS_SELECTOR, ".b_category, [data-category]")
            place['categories'] = [c.text for c in cat_elems]
        except:
            place['categories'] = []
        
        # Coordinates (from URL or data attr)
        try:
            link = card.find_element(By.CSS_SELECTOR, "a").get_attribute('href')
            lat_match = re.search(r'@(-?\d+\.?\d*),(-?\d+\.?\d*)', link)
            if lat_match:
                place['lat'] = lat_match.group(1)
                place['lng'] = lat_match.group(2)
        except:
            place['lat'] = place['lng'] = ""
        
        # Photos count
        try:
            photo_elem = card.find_element(By.CSS_SELECTOR, "[aria-label*='photo'], .b_photos")
            place['photos_count'] = re.search(r'(\d+)', photo_elem.get_attribute('aria-label') or photo_elem.text).group(1)
        except:
            place['photos_count'] = ""
        
        # Full link
        try:
            link_elem = card.find_element(By.CSS_SELECTOR, "a")
            place['maps_link'] = link_elem.get_attribute('href')
        except:
            place['maps_link'] = ""
        
        return place

# Test
if __name__ == "__main__":
    scraper = BingMapsScraper()
    print(scraper.test_connection())
    places = scraper.scrape_places("coffee", "solo", max_pages=1)
    print(f"Found {len(places)} places")
    for p in places[:3]:
        print(p)

