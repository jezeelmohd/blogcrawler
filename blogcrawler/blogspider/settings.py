# Scrapy settings for blogspider project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#

BOT_NAME = 'blogspider'

SPIDER_MODULES = ['blogspider.spiders']
NEWSPIDER_MODULE = 'blogspider.spiders'
ITEM_PIPELINES = {'blogspider.pipelines.MongoPipeline':100}
DEPTH_LIMIT=20
SPIDER_MIDDLEWARES_BASE = {
    'scrapy.contrib.spidermiddleware.httperror.HttpErrorMiddleware': 50,
    'scrapy.contrib.spidermiddleware.offsite.OffsiteMiddleware': 500,
    'scrapy.contrib.spidermiddleware.referer.RefererMiddleware': 700,
    'scrapy.contrib.spidermiddleware.urllength.UrlLengthMiddleware': 800,
    'scrapy.contrib.spidermiddleware.depth.DepthMiddleware': 900,
}
DOWNLOADER_MIDDLEWARES = {
    'blogspider.middleware.RedirectMiddleware': 543,
}
"""
"""
# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'blogspider (+http://www.yourdomain.com)'
