import time
import json
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException
from tqdm import tqdm
import random
import re
import traceback

class LoLChampionScraper:
    def __init__(self):
        self.champions_url = "https://universe.leagueoflegends.com/en_US/champions/"
        self.base_url = "https://universe.leagueoflegends.com"
        self.champions_data = []

        self.chrome_options = Options()
        self.chrome_options.add_argument("--window-size=1920,1080")
        self.chrome_options.add_argument("--disable-gpu")
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        self.chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.88 Safari/537.36") # Example user agent
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=self.chrome_options)
        print("WebDriver Initialized")

    def extract_champions_list(self):
        """Extract list of champions using Selenium"""
        self.driver.get(self.champions_url)
        time.sleep(5)
        selectors = [
            "li.item_30l8 a",
            ".champsListUl_2Lmb li a",
            "a[href*='/champion/']"
        ]
        champions = []
        timeout = 10
        for selector in selectors:
            try:
                WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                champion_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if champion_elements:
                    for element in champion_elements:
                        try:
                            url = element.get_attribute("href")
                            if not url or not url.startswith(self.base_url):
                                continue
                            name_element = element.find_element(By.CSS_SELECTOR, "h1") if element.find_elements(By.CSS_SELECTOR, "h1") else None
                            region_element = element.find_element(By.CSS_SELECTOR, "h2") if element.find_elements(By.CSS_SELECTOR, "h2") else None
                            name = name_element.text.strip() if name_element and name_element.text else ""
                            region = region_element.text.strip() if region_element and region_element.text else ""
                            if name and url and not any(c['name'] == name.upper() for c in champions):
                                champions.append({'name': name.upper(), 'region': region, 'url': url})
                        except Exception as e: print(f"  Warn: Error processing a champion list element: {e}")
                    if champions:
                        print(f"  Successfully extracted champion list using selector: {selector}")
                        break
            except TimeoutException: print(f"  Selector {selector} timed out.")
            except Exception as e: print(f"  Selector {selector} failed with error: {e}")
        print(f"Found {len(champions)} unique champions")
        return champions

    def extract_champion_details(self, champion_data):
        """Extract detailed information for a specific champion's main page"""
        print(f"Extracting details for {champion_data['name']}...")
        if not champion_data.get('url'):
            print(f"  Error: Missing URL for {champion_data['name']}")
            return champion_data
        try:
            self.driver.get(champion_data['url'])
            WebDriverWait(self.driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, "body")))
            time.sleep(1 + random.random())
        except Exception as e:
            print(f"  Error navigating to champion page {champion_data['url']}: {e}")
            return champion_data

        # Extract Role, Race, Quote, Short Bio
        try:
            role_element = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".typeDescription_ixWu h6, .playerType_3laO h6")))
            champion_data['role'] = role_element.text.strip()
        except: champion_data['role'] = ""
        try:
            race_elements = self.driver.find_elements(By.CSS_SELECTOR, ".ChampionRace_a_Fp h6, .race_3k58 h6")
            champion_data['race'] = race_elements[0].text.strip() if race_elements else ""
        except: champion_data['race'] = ""
        try:
            quote_elements = self.driver.find_elements(By.CSS_SELECTOR, ".quote_2507 p, .championQuotes_3FLE p")
            champion_data['quote'] = quote_elements[0].text.strip() if quote_elements else ""
        except: champion_data['quote'] = ""
        
        # IMPROVED: Extract short bio with multiple selectors and approaches
        try:
            # First try the original approach
            bio_elements = self.driver.find_elements(By.CSS_SELECTOR, ".biographyText_3-to p, .biography_3YIe p")
            if bio_elements and bio_elements[0].text.strip():
                champion_data['short_bio'] = bio_elements[0].text.strip()
            else:
                # Try getting the text from the div container directly
                bio_containers = self.driver.find_elements(By.CSS_SELECTOR, ".biographyText_3-to, .biography_3YIe")
                if bio_containers:
                    container_text = bio_containers[0].text.strip()
                    if container_text:
                        # Split by newlines and take the first paragraph if multiple exist
                        paragraphs = [p.strip() for p in container_text.split('\n') if p.strip()]
                        if paragraphs:
                            champion_data['short_bio'] = paragraphs[0]
                        else:
                            champion_data['short_bio'] = container_text
                    else:
                        champion_data['short_bio'] = ""
                else:
                    champion_data['short_bio'] = ""
        except Exception as e:
            print(f"  Warn: Error extracting short bio: {e}")
            champion_data['short_bio'] = ""

        # Extract Related Champions
        related_champions = []
        try:
            h5_locator = (By.CSS_SELECTOR, "ul.champions_jmhN li.champion_1xlO h5")
            WebDriverWait(self.driver, 3).until(EC.presence_of_element_located(h5_locator))
            related_elements = self.driver.find_elements(*h5_locator)
            if related_elements:
                for i, elem in enumerate(related_elements):
                    try:
                        champion_name = self.driver.execute_script("return arguments[0].textContent;", elem).strip()
                        if champion_name and champion_name not in related_champions:
                            related_champions.append(champion_name)
                    except Exception as inner_e: 
                        print(f"    Warn: Error processing related champion element {i+1}: {type(inner_e).__name__} - {inner_e}")
        except Exception as e: 
            print(f"  Warn: An unexpected error occurred while finding/processing related champions: {type(e).__name__} - {e}")
        champion_data['related_champions'] = related_champions
        print(f"  Assigned related champions list: {champion_data['related_champions']}")

        # Find Biography URL
        try:
            bio_link_elements = self.driver.find_elements(By.XPATH, "//a[.//button[.//span[contains(text(), 'Read Biography') or contains(text(), 'Read Bio')]]]|//a[contains(@href,'/story/champion/')]")
            found_bio_url = ""
            if bio_link_elements:
                for link_el in bio_link_elements:
                    href = link_el.get_attribute('href')
                    if href and '/story/champion/' in href: found_bio_url = href; break
                if not found_bio_url: found_bio_url = bio_link_elements[0].get_attribute('href')
            if found_bio_url: champion_data['bio_url'] = found_bio_url
            else:
                clean_name = re.sub(r'[^a-z0-9]', '', champion_data['name'].lower()); bio_url = f"{self.base_url}/en_US/story/champion/{clean_name}/"; champion_data['bio_url'] = bio_url; print(f"  Warn: Could not find bio button/link, constructed fallback URL: {bio_url}")
        except Exception as e: 
            print(f"  Warn: Could not find or construct biography URL: {e}"); champion_data['bio_url'] = ""
        champion_data['story_url'] = ""
        return champion_data

    def extract_page_content(self, container_selector, paragraph_selector):
        """Helper function to extract joined paragraph text from a container."""
        full_text = ""
        paragraphs_count = 0
        try:
            print(f"  Attempting to find container '{container_selector}' directly in DOM...")
            container_elements = self.driver.find_elements(By.CSS_SELECTOR, container_selector)

            if not container_elements:
                print(f"  Error: Container '{container_selector}' not found in DOM after interaction attempt.")
                return full_text, paragraphs_count

            container_element = container_elements[0]
            print(f"  Container '{container_selector}' found in DOM.")

            paragraphs = container_element.find_elements(By.CSS_SELECTOR, paragraph_selector)
            paragraphs_count = len(paragraphs)
            if paragraphs:
                extracted_texts = []
                for i, p in enumerate(paragraphs):
                    try:
                        para_text = self.driver.execute_script(
                            "return arguments[0].textContent;", p
                        ).strip()
                        if para_text:
                            extracted_texts.append(para_text)
                    except Exception as inner_e:
                        print(f"    Warn: Error processing paragraph {i+1}: {type(inner_e).__name__} - {inner_e}")

                full_text = "\n\n".join(extracted_texts)
                if not full_text and paragraphs_count > 0:
                    print(f"  Warn: Found {paragraphs_count} paragraphs in '{container_selector}', but all textContent was empty after processing.")
            else:
                print(f"  Warn: Container '{container_selector}' found, but no paragraphs matched selector '{paragraph_selector}'.")

        except Exception as e:
            print(f"  Error: Exception finding/processing content within '{container_selector}': {type(e).__name__} - {e}")

        return full_text, paragraphs_count

    def extract_bio_and_story(self, champion_data):
        """Extract full biography from bio_url and find the story_url."""
        champion_data['full_biography'] = ""
        if not champion_data.get('bio_url'):
            print(f"  Info: No biography URL available for {champion_data['name']}")
            return champion_data

        print(f"Navigating to biography page for {champion_data['name']}...")
        try:
            self.driver.get(champion_data['bio_url'])
            WebDriverWait(self.driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, "body")))
            time.sleep(1 + random.random())
        except Exception as nav_e:
            print(f"  Error navigating to biography URL '{champion_data['bio_url']}': {nav_e}")
            return champion_data
        
        clicked_scroll_button = False
        try:
            button_selector = (By.CSS_SELECTOR, "p.cta_VVdh")
            scroll_button = WebDriverWait(self.driver, 7).until(
                EC.presence_of_element_located(button_selector)
            )
            print("  'Scroll to Begin' button (p.cta_VVdh) is present.")
            try:
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});", scroll_button)
                time.sleep(1.0)
                self.driver.execute_script("arguments[0].click();", scroll_button)
                print("  Attempted click 'Scroll to Begin' button via JavaScript.")
                clicked_scroll_button = True
                print("  Performing small scroll down after click...")
                self.driver.execute_script("window.scrollBy(0, 150);")
                time.sleep(0.5)
            except Exception as js_click_e:
                print(f"  Warn: JavaScript click execution failed: {type(js_click_e).__name__} - {js_click_e}")
        except TimeoutException:
            print("  Info: 'Scroll to Begin' button (p.cta_VVdh) not found within timeout.")
        except Exception as scroll_e:
            print(f"  Warn: Error interacting with 'Scroll to Begin' button: {type(scroll_e).__name__} - {scroll_e}")

        primary_paragraph_selector = "p.p_1_sJ"
        container_selector = "#CatchElement"
        bio_text, para_count = self.extract_page_content(container_selector, primary_paragraph_selector)
        champion_data['full_biography'] = bio_text

        if bio_text:
            actual_paragraphs = len(bio_text.split('\n\n'))
            print(f"  Extracted biography text ({actual_paragraphs} non-empty paragraphs joined).")
        elif not bio_text:
            print(f"  Warn: Failed to extract biography text content from '{container_selector}'.")

        story_button_found = False
        try:
            story_links = self.driver.find_elements(By.XPATH, 
                "//a[.//button[.//span[contains(text(), 'story') or contains(text(), 'Story')]]]|" +
                "//a[contains(@href,'/story/')][not(contains(@href, '/story/champion/'))]|" +
                "//a[contains(@href,'-color-story')]"
            )
            
            found_story_url = ""
            if story_links:
                for link in story_links:
                    href = link.get_attribute('href')
                    if href and ('/story/' in href) and ('/story/champion/' not in href):
                        found_story_url = href
                        story_button_found = True
                        break
                
                if not found_story_url and story_links:
                    found_story_url = story_links[0].get_attribute('href')
                    story_button_found = True
            
            if found_story_url:
                champion_data['story_url'] = found_story_url
                print(f"  Found story URL on bio page: {champion_data['story_url']}")
            else:
                print(f"  No story link found on bio page.")
                champion_data['story_url'] = ""
        except Exception as e:
            print(f"  Warn: Error finding story link on bio page: {e}")
            champion_data['story_url'] = ""
            
        if not story_button_found and not champion_data['story_url']:
            try:
                clean_name = re.sub(r'[^a-z0-9]', '', champion_data['name'].lower())
                fallback_url = f"{self.base_url}/en_US/story/{clean_name}-color-story/"
                print(f"  Creating fallback story URL: {fallback_url}")
                champion_data['story_url'] = fallback_url
            except Exception as fallback_e:
                print(f"  Error creating fallback story URL: {fallback_e}")
                champion_data['story_url'] = ""
                
        return champion_data

    def extract_story_content(self, champion_data):
        """Extract the full story content from the story URL"""
        champion_data['full_story'] = ""
        if not champion_data.get('story_url') or not champion_data['story_url'].startswith(self.base_url):
            print(f"  Info: No valid story URL available for {champion_data['name']}")
            return champion_data

        print(f"Navigating to story page for {champion_data['name']}...")
        try:
            self.driver.get(champion_data['story_url'])
            WebDriverWait(self.driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, "body")))
            time.sleep(1 + random.random())
        except Exception as nav_e:
            print(f"  Error navigating to story URL '{champion_data['story_url']}': {nav_e}")
            return champion_data

        clicked_scroll_button = False
        try:
            button_selector = (By.CSS_SELECTOR, "p.cta_VVdh")
            scroll_button = WebDriverWait(self.driver, 7).until(
                EC.presence_of_element_located(button_selector)
            )
            print("  'Scroll to Begin' button (p.cta_VVdh) is present.")
            try:
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});", scroll_button)
                time.sleep(1.0)
                self.driver.execute_script("arguments[0].click();", scroll_button)
                print("  Attempted click 'Scroll to Begin' button via JavaScript.")
                clicked_scroll_button = True
                print("  Performing small scroll down after click...")
                self.driver.execute_script("window.scrollBy(0, 150);")
                time.sleep(0.5)
            except Exception as js_click_e:
                print(f"  Warn: JavaScript click execution failed: {type(js_click_e).__name__} - {js_click_e}")
        except TimeoutException:
            print("  Info: 'Scroll to Begin' button (p.cta_VVdh) not found within timeout.")
        except Exception as scroll_e:
            print(f"  Warn: Error interacting with 'Scroll to Begin' button: {type(scroll_e).__name__} - {scroll_e}")

        primary_paragraph_selector = "p.p_1_sJ"
        container_selector = "#CatchElement"
        story_text, para_count = self.extract_page_content(container_selector, primary_paragraph_selector)
        champion_data['full_story'] = story_text

        if story_text:
            actual_paragraphs = len(story_text.split('\n\n'))
            print(f"  Extracted story text ({actual_paragraphs} non-empty paragraphs joined).")
        elif not story_text:
            print(f"  Warn: Failed to extract story text content from '{container_selector}'.")

        return champion_data

    def scrape_champions(self, limit=None):
        """Scrape information for all champions"""
        all_data = []
        try:
            champions_list = self.extract_champions_list()
            if not champions_list:
                print("Error: Failed to extract champions list. Exiting.")
                return []
            if limit:
                champions_list = champions_list[:limit]
            self.champions_data = []

            for champion in tqdm(champions_list, desc="Scraping champions"):
                time.sleep(1.5 + random.random() * 2)
                current_champion_data = {'name': champion['name'], 'url': champion['url'], 'region': champion.get('region','')}
                current_champion_data = self.extract_champion_details(current_champion_data)
                current_champion_data = self.extract_bio_and_story(current_champion_data)
                current_champion_data = self.extract_story_content(current_champion_data)
                all_data.append(current_champion_data)
                self.champions_data = all_data
                self.save_to_json(self.champions_data, '../data/progress_champions_data.json') # Pass data

            print(f"\nScraping complete. Processed {len(all_data)} champions.")
            return all_data
        except KeyboardInterrupt:
            print("\nScraping interrupted by user.")
            return all_data
        except Exception as e:
            print(f"\nAn critical error occurred during scraping: {type(e).__name__} - {e}")
            traceback.print_exc()
            return all_data
        finally:
            print("Closing WebDriver...")
            if hasattr(self, 'driver'):
                self.driver.quit()

    def save_to_csv(self, data_to_save, filename='../data/lol_champions_data.csv'):
        """Save the collected data to a CSV file"""
        if not data_to_save:
            print("No champion data provided to save to CSV.")
            return
        try:
            df = pd.DataFrame(data_to_save)
            cols = ['name', 'region', 'role', 'race', 'quote', 'related_champions',
                    'short_bio', 'full_biography', 'full_story', 'url', 'bio_url', 'story_url']
            if 'related_champions' in df.columns:
                df['related_champions'] = df['related_champions'].apply(lambda x: ', '.join(x) if isinstance(x, list) else x)
            df = df.reindex(columns=[col for col in cols if col in df.columns])
            df.to_csv(filename, index=False, encoding='utf-8')
            print(f"Data saved to {filename}")
        except Exception as e:
            print(f"Error saving data to CSV {filename}: {e}")

    def save_to_json(self, data_to_save, filename='../data/lol_champions_data.json'):
        """Save the collected data to a JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, ensure_ascii=False, indent=4)
            if 'progress' not in filename: print(f"Data saved to {filename}")
            else: pass
        except Exception as e:
            print(f"Error saving data to JSON {filename}: {e}")

def main():
    scraper = LoLChampionScraper()
    final_champion_data = None
    try:
        final_champion_data = scraper.scrape_champions()
    finally:
        if final_champion_data:
            print("\nSaving final data...")
            scraper.save_to_csv(final_champion_data, '../data/lol_champions_data.csv')
            scraper.save_to_json(final_champion_data, '../data/lol_champions_data.json')
        else:
            if scraper.champions_data:
                print("\nScraping did not complete fully, saving data collected so far...")
                scraper.save_to_csv(scraper.champions_data, '../data/lol_champions_data.csv')
                scraper.save_to_json(scraper.champions_data, '../data/lol_champions_data.json')
            else:
                print("\nNo final data collected to save.")
        if hasattr(scraper, 'driver') and scraper.driver:
            scraper.driver.quit()
            print("WebDriver quit confirmed from main.")

if __name__ == "__main__":
    main()