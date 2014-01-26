import os, time

from scrapy.http import Request
from scrapy.item import BaseItem
from scrapy.utils.request import request_fingerprint
from scrapy.utils.project import data_path
from scrapy.exceptions import NotConfigured
from scrapy import log, signals
from pymongo import MongoClient

class DeltaFetch(object):
	def __init__(self, reset=False):
		self.reset = reset

	@classmethod
	def from_crawler(cls, crawler):
		s = crawler.settings
		o = cls()
		crawler.signals.connect(o.spider_opened, signal=signals.spider_opened)
		crawler.signals.connect(o.spider_closed, signal=signals.spider_closed)
		#crawler.signals.connect(o.item_scraped, signal=signals.item_scraped)
		return o
	
	#def item_scraped(self, item, response, spider):
	#	self.db.urls.insert({'url': response.url})

	def spider_opened(self, spider):
		#self.db = MongoClient('192.168.1.8')['mut']
		self.db = MongoClient()['mutlu']
	def spider_closed(self, spider):
		pass
		#self.db.close()

	def process_spider_output(self, response, result, spider):
		for r in result:
			if isinstance(r, Request):
				if self.db.urls.find({'url': r.url}).count()>0:
					spider.log("Ignoring already visited: %s" % r, level=log.INFO)
					continue
			yield r