"""Scrapes MealDB website to extract meals and ingredients."""

import scrapy
from scrapy.crawler import CrawlerProcess


class SpiderMeals(scrapy.Spider):
    """Scrapy spider class to scrape meals and ingredients from MealDB."""

    name = 'spider1'
    start_urls = ["https://www.themealdb.com/browse/letter/a"]
    allowed_domains = ["themealdb.com"]

    visited_meals = set()
    visited_ingredients = set()
    visited_letters = set()

    MAX_PAGES = 2000
    page_counter = 0

    def safe_link(self, link):
        """Simple and safe check: Accept the link if it exists and starts with '/'."""
        try:
            if not link:
                return None
            if not link.startswith("/"):
                return None
            return link
        except AttributeError as e:
            self.logger.error(f"AttributeError in safe_link(): {e}")
            return None

    def parse(self, response):
        """Parse the main page to get meal links and follow them."""
        try:
            self.page_counter += 1
            if self.page_counter > self.MAX_PAGES:
                return

            food_links = response.css('a[href*="/meal/"]::attr(href)').getall()
            for link in food_links:
                link = self.safe_link(link)
                if not link:
                    continue
                if link not in self.visited_meals:
                    self.visited_meals.add(link)
                    yield response.follow(link, callback=self.parse_meal)

            next_pages = response.css('a[href^="/browse/letter/"]::attr(href)').getall()
            for page in next_pages:
                page = self.safe_link(page)
                if not page:
                    continue
                if page not in self.visited_letters:
                    self.visited_letters.add(page)
                    yield response.follow(page, callback=self.parse)

        except AttributeError as e:
            self.logger.error(f"AttributeError in parse(): {e}")

    def parse_meal(self, response):
        """Extract meal name, ingredients, instructions, and follow ingredient pages."""
        try:
            food_name = response.css('h1::text').get()
            if food_name:
                food_name = food_name.strip()
        except AttributeError as e:
            self.logger.error(f"AttributeError in parse_meal() when getting food_name: {e}")
            food_name = None

        try:
            ingredient_links = response.css('a[href^="/ingredient/"]::attr(href)').getall()
        except AttributeError as e:
            self.logger.error(f"AttributeError getting ingredient_links in parse_meal(): {e}")
            ingredient_links = []

        try:
            ingredient_names = response.css('figcaption::text').getall()
        except AttributeError as e:
            self.logger.error(f"AttributeError getting ingredient_names in parse_meal(): {e}")
            ingredient_names = []

        try:
            raw_nodes = response.xpath(
                "//h2[text()='Instructions']/following-sibling::node()[not(self::h2)]"
            ).getall()
        except AttributeError as e:
            self.logger.error(f"AttributeError getting raw_nodes in parse_meal(): {e}")
            raw_nodes = []

        clean_instructions = []
        for node in raw_nodes:
            try:
                text = node.strip()
                if "br" in text.lower():
                    clean_instructions.append("\n")
                else:
                    clean_instructions.append(text)
            except AttributeError as e:
                self.logger.warning(f"AttributeError processing node in parse_meal(): {e}")
                continue

        instruction = "".join(clean_instructions)

        try:
            yield {
                'TYPE': 'MEAL',
                'Food Name': food_name,
                'Ingredients Used': ingredient_names,
                'Instructions': instruction,
                'Meal URL': response.url,
            }
        except AttributeError as e:
            self.logger.error(f"AttributeError yielding meal in parse_meal(): {e}")

        for link in ingredient_links:
            try:
                link = self.safe_link(link)
                if not link:
                    continue
                if link not in self.visited_ingredients:
                    self.visited_ingredients.add(link)
                    yield response.follow(link, callback=self.parse_ingre)
            except AttributeError as e:
                self.logger.warning(f"AttributeError following ingredient link in parse_meal(): {e}")
                continue

    def parse_ingre(self, response):
        """Extract ingredient name and URL."""
        try:
            ingredient_name = response.css('h1::text').get()
            if ingredient_name:
                ingredient_name = ingredient_name.strip()
        except AttributeError as e:
            self.logger.error(f"AttributeError in parse_ingre(): {e}")
            ingredient_name = None

        try:
            yield {
                'TYPE': 'INGREDIENT',
                'Food Name': ingredient_name,
            }
        except AttributeError as e:
            self.logger.error(f"AttributeError yielding ingredient in parse_ingre(): {e}")


if __name__ == "__main__":
    process = CrawlerProcess(settings={
        'FEEDS': {
            'yemekler1.json': {
                'format': 'json',
                'encoding': 'utf-8',
                'indent': 4,
                'overwrite': True,
            },
        },
        'DOWNLOAD_DELAY': 0,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36'
    })

    process.crawl(SpiderMeals)
    process.start()