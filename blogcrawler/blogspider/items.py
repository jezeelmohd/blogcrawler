# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

from scrapy.item import Item, Field

class BlogItem(Item):
    blog_url=Field()
    post_url=Field()
    post_date=Field()
    post_title=Field()
    post_text=Field()