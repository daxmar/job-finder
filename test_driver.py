import sys
print('Python:', sys.version)
print('Architecture:', sys.maxsize > 2**32 and '64-bit' or '32-bit')

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    print('Selenium & WDM imported OK')
    
    print('Installing ChromeDriver...')
    chromedriver_path = ChromeDriverManager().install()
    print('ChromeDriver:', chromedriver_path)
    
    print('Starting Chrome...')
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    service = Service(chromedriver_path)
    driver = webdriver.Chrome(service=service, options=options)
    driver.get('https://www.google.com')
    print('✅ Chrome started successfully!')
    print('Title:', driver.title[:50])
    driver.quit()
    print('Driver quit OK')
except Exception as e:
    print('❌ Error:', str(e))
    import traceback
    traceback.print_exc()
