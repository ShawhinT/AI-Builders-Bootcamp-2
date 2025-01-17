from bs4 import BeautifulSoup
import json
import asyncio
from pyppeteer import launch
import requests

# scrape job listing urls
async def scrape_jobs(search_term, num_pages=10):
    """
    Scrape job postings from www.themuse.com based on search term
    
    Args:
        search_term (str): Search term to look for
        num_pages (int): Number of "Load More" clicks to perform
    Returns:
        list: List of job URLs for the search term
    """
    print(f"Searching for {search_term} jobs over {num_pages} pages...")
    # Convert search term to URL-friendly format
    search_query = search_term.replace(' ', '%20')
    
    # Launch a headless browser
    browser = await launch(headless=True)
    page = await browser.newPage()

    # Navigate to the job search page
    url = f"https://www.themuse.com/search/keyword/{search_query}/"
    await page.goto(url)
    
    # First, scroll and click "Load More" the specified number of times
    load_more_selector = "#main-content > article > div.SearchResults_hasFade__KcoTL.SearchResults_resultsGrid__pHY29 > button"
    
    for i in range(num_pages-1):
        try:
            print(f"Loading more jobs (attempt {i+1}/{num_pages-1})...")
            # Scroll to bottom
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(1)
            
            # Click load more
            button = await page.waitForSelector(load_more_selector, {'timeout': 5000})
            if button:
                await page.click(load_more_selector)
                await asyncio.sleep(0.7)
        except Exception as e:
            print(f"Error on attempt {i+1}: {str(e)}")
            break
    
    # Now extract all job URLs
    job_urls = []
    content = await page.content()
    soup = BeautifulSoup(content, 'html.parser')
    script_tag = soup.find('script', {'id': 'ItemList'})
    
    if script_tag:
        job_data = json.loads(script_tag.string)
        job_urls = [item['url'] for item in job_data['itemListElement']]
        print(f"Found {len(job_urls)} URLs total")
    
    await browser.close()
    return job_urls

# function to scrape job details from a given URL
def scrape_job_details(url):
    """
    Scrape job details from a given URL
    
    Args:
        url (str): URL of the job to scrape
    Returns:
        dict: Dictionary containing job details
    """

    # get the HTML content of the job page
    response = requests.get(url)
    html_content = response.text

    # parse the HTML content with BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')

    # Find the script tag containing JSON-LD
    try:
        script_tag = soup.find('script', type='application/ld+json')
        job_data = json.loads(script_tag.string)
    except:
        print(f"Could not find job data for {url}")
        return None

    if job_data:
        # Extract relevant fields
        company_name = job_data['hiringOrganization']['name']
        job_title = job_data['title']
        job_description = job_data['description']

        return {
            'company_name': company_name,
            'job_title': job_title,
            'job_description': job_description,
            'job_url': url
        }
    else:
        return None
