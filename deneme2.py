import scrapy
from scrapy.crawler import CrawlerProcess

class SpiderMeals(scrapy.Spider):
    name = 'spider1'
    start_urls = ["https://www.themealdb.com/browse/letter/a"]

    def parse(self, response):
        # --- MEAL links ---
        food_links = response.css('a[href*="/meal/"]::attr(href)').getall()
        for link in food_links:
            yield response.follow(link, callback=self.parse_meal)

        # --- NEXT PAGE ---
        next_page = response.css("a.pagination__next::attr(href)").get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)

    def parse_meal(self, response):
        # --- MEAL NAME ---
        food_name = response.css('h1::text').get()

        # --- INGREDIENT LINKS + NAMES ---
        ingredient_links = response.css('a[href*="/ingredient/"]::attr(href)').getall()
        ingredient_names = response.css('a[href*="/ingredient/"]::text').getall()

        # --- INSTRUCTIONS ---
        raw_nodes = response.xpath(
            "//h2[text()='Instructions']/following-sibling::node()[not(self::h2)]"
        ).getall()

        clean_instructions = []
        for node in raw_nodes:
            text = node.strip()

            # BR kontrolü
            if "br" in text.lower():
                clean_instructions.append("\n")
            else:
                clean_instructions.append(text)

        instruction = "".join(clean_instructions)

        # --- MEAL INFO ---
        yield {
            'Food Name': food_name,
            'Ingredients Used': ingredient_names,
            'Instructions': instruction,
            'Meal URL': response.url,
        }

        # --- FOLLOW INGREDIENT PAGES ---
        for link in ingredient_links:
            yield response.follow(link, callback=self.parse_ingre)

    def parse_ingre(self, response):
        ingredient_name = response.css('h1::text').get()

        yield {
            'Ingredient Name': ingredient_name,
            'Ingredient URL': response.url,
        }


# --- RUN SCRAPY PROCESS ---
process = CrawlerProcess(settings={
    'FEEDS': {
        'yemekler.json': {
            'format': 'json',
            'encoding': 'utf-8',
            'indent': 4,
            'overwrite': True,
        },
    },
    'DOWNLOAD_DELAY': 1,
    'USER_AGENT': 'Mozilla/5.0',
})

process.crawl(SpiderMeals)
process.start()
