from pymongo import MongoClient

class MongoPipeline(object):
    def __init__(self):
        self.db = MongoClient()['mutlu']
        #self.db = self.c.blog_spider
        self.coll = self.db.blog_post

    def process_item(self, item, spider):
        #self.db.blog_post.insert(dict(item))
        #return item
		try:
			self.coll.find({"post_url":"%s"%(item['post_url'])})[0]
		except:
			self.coll.insert(dict(item))
		return item