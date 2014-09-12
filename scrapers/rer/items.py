# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

from scrapy.item import Item, Field

class RerScrappersItem(Item):
    time = Field()
    full_mission = Field()
    mission = Field()
    mission_id = Field()
    train_id = Field()
    station = Field()
    status = Field()
    item_id = Field()
