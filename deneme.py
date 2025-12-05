import scrapy
from scrapy.crawler import CrawlerProcess
"""
def parse 
def parse_meal
def parse_ingredient
"""
class spider(scrapy.Spider):
    name='spider1'
    start_urls = ["https://www.themealdb.com/browse/letter/a"]
    def parse(self, response):
        food_links= response.css('a[href="/meal/"]')
        for link in food_links:
            yield response.follow(link,callback=self.parse_meal)
        next_page = response.css("a.pagination__next::attr(href)").get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)

    def parse_meal(self,response):
        food_name=response.css('h1::text').get()
        ingredients_links = response.css('a[href="/ingredient/"]')
        ingre_names=response.css('a[href="/ingredient/"]::text').getall()
        raw_instructions_nodes = response.xpath(
            "//h2[text()='Instructions']/following-sibling::text() | //h2[text()='Instructions']/following-sibling::br"
        ).getall()
        clean_ingredient=[]
        for node in raw_instructions_nodes:
            if node.lower().strip() == '<br>':
                clean_ingredient.append("\n")
            else:
                clean_ingredient.append(node.strip())
        instruction="".join(clean_ingredient)
        yield{
            'Food Name': food_name,
            'food_specified_ingre': ingre_names,
            'instruction': instruction,
        }
        for link in ingredients_links:
            yield response.follow(link,callback=self.parse_ingre)
    def parse_ingre(self,response):
        ingredient_name = response.css('h1::text').get()

        yield {
            'Ingredient Name': ingredient_name,
            'Ingredient URL': response.url,
        }
process = CrawlerProcess(settings={
    'FEEDS': {
        'yemekler.json':{
            'format': 'json',
            'encoding':'utf-8',
            'indent':4,
            'item_export_fmt': 'json',
            'overwrite': True,
        },
    },
   'DOWNLOAD_DELAY': 1,
})
process.crawl(spider)
process.start()


