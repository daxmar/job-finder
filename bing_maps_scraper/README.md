# Bing Maps Scraper

Aplikasi GUI untuk scraping data lengkap dari Bing Maps (bing.com/maps).

## Data yang di-scrape (semua rincian):
- **Nama Tempat** (business name)
- **Alamat Lengkap** (street, city, postal, country)
- **Telepon** (+62 format)
- **Website** (if available)
- **Rating** (stars 1-5)
- **Jumlah Review** 
- **Kategori/Tags** (restaurant, cafe, etc.)
- **Jam Buka** (Mon-Sun hours)
- **Level Harga** ($, $$, $$$)
- **Koordinat GPS** (lat, lng from URL)
- **Jumlah Foto**
- **Link Maps**
- **Nearby/Related** (if detected)

## Cara Pakai:
1. `cd bing_maps_scraper`
2. `pip install -r requirements.txt`
3. **Offline mode:** Download [msedgedriver.exe](https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/) → put in folder
4. `python bing_maps_gui.py`
5. Test Edge (works offline too) → "coffee solo" → Scrape → Export

## Tech:
- Selenium + Microsoft Edge (Windows native)
- Tkinter GUI
- Pandas Excel export
- ReportLab PDF cards

**Selectors Bing Maps** (per 2024):
- Place cards: `[data-bingmaps-id]`, `.b_mapBubbleMap`
- Details: `.mwpai21`, phone `.b_linkSans`, rating `.b_ratingNumber`

