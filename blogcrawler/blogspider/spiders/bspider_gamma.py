import re
import csv
import time
from items import BlogItem
from fuzzywuzzy import fuzz
from nltk import clean_html
from scrapy.item import Item
from urlparse import urlparse
from scrapy.http import Request
from scrapy.selector import Selector
from collections import OrderedDict, Counter
from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor


class MySpider(CrawlSpider):
	name = 'blogspider'
	DENY_PATTERNS = re.compile('(\/tag)|(\/search\/)|(\/category\/)|(\?tag\=)|(\/search\?max-results=)|(_archive\.html)|\
		(\/search\?by-date=)|(\?showComment=)|(\?shared=)|(\?msg=)|(\?replytocom=)|(\/author\/)|(\/\d{4}\/\d{2}\/$)|(\/page\/)|\
		([\/]?\?page=)|(\/\?pfstyle=)|(\/\d{4}\/\d{2}\/\d{2}\/$)|(\/archive\/)|(\/comment-page-1\/)|(\/\?attachment_id=)|\
		(\/\?adv_search=)|(\?redirect_to=)|(com\/\d{4}\/\d{2}$)')

	def __init__(self, blogurl='http://mycottoncreations.blogspot.com',blogid='7777'):
		self.start_urls = [blogurl,]
		self.allowed_domains = [self.get_domain(dom) for dom in self.start_urls]
		self.blog_ids = {blogurl: blogid}
		self.blog_id = blogid
		self.rules = (
			Rule(
				SgmlLinkExtractor(allow_domains=self.allowed_domains,deny_domains=['facebook.com','google.com','twitter.com','pintrest.com'],unique=True),
				process_request='add_meta',follow=True, callback='parse_item'),
		)
		super(MySpider, self).__init__()

	def get_domain(self, blog):
		blog = blog.replace('http://', '').replace('https://', '').replace('www.', '').split('/')[0]
		return blog

	def add_meta(self, request):
		request.meta['id'] = self.blog_id
		if not self.DENY_PATTERNS.search(request.url):
			return request
	
	def parse_item(self, response):
		sel = Selector(response)

		date = self.post_date_extract(sel,response)
		title,title_xpath = self.post_title_extract(sel, response)
		if title and title_xpath:
			post_text = self.find_post_text(title_xpath,sel)
			title = ' '.join(title.split()).replace('&amp;','&') if title else None
			text = ' '.join(post_text.split()).replace('&amp;','&') if post_text else None

			date = date if date else None
			base_url = urlparse(response.url)
			item = BlogItem(blog_url=base_url.netloc,
							post_url=response.url,
							post_date=date,
							post_title=title,
							post_text=text,
							blog_id=response.meta['id'],
							)
			if not self.DENY_PATTERNS.search(item['post_url']) and item['post_text']:
				yield item


	def post_date_extract(self,sel,response):
		date=None
		date_meta = sel.xpath('//meta[contains(@property,"article:published_time")]/@content').extract()
		if date_meta:
			date=date_meta[0] if date_meta else None
		if not date:
			date_title = re.compile('\d+\/\d+\/\d+').findall(response.url)
			date=date_title[0] if date_title else None
		if not date:
			date_span_xpath = ' '.join(sel.xpath('//span/text()').extract())
			date_span = re.compile('\w+ \d+, \d+').findall(date_span_xpath)
			date = date_span[0] if date_span else None
		if not date:
			date_text_xpath = ' '.join(sel.xpath('//text()').extract())
			date_text = re.compile('\w+ \d{2} \d{4}').findall(date_text_xpath)
			if not date_text:
				date_text = re.compile('\w+ \d+, \d{4}').findall(date_text_xpath)
			if not date_text:
				date_text = re.compile('\d+\/\d+\/\d+').findall(date_text_xpath)
			if not date_text:
				date_text = re.compile('\d+\.\d+\.\d+').findall(date_text_xpath)
			date = date_text[0] if date_text else None
		return date

	def post_title_extract(self,sel,response):
		title = None
		title_score = 0
		slug_score = 0
		title_xpath = None
		blog=self.get_domain(response.url)
		slug = response.url.split('/')[-1] or response.url.split('/')[-2]
		slug = slug.replace('-',' ').rstrip('.html')

		head_title = sel.xpath('//title/text()').extract()
		head_title = head_title[0] if head_title else ''
		if '|' in head_title:
			pos=[head_title.split('|')[0],head_title.split('|')[-1]]
			word = pos[0] if fuzz.partial_ratio(pos[0],blog)>fuzz.partial_ratio(pos[-1],blog) else pos[-1]
			head_title_clean = head_title.replace(word,'').replace('|','')
		else:		
			head_title_clean = head_title
			text_to_remove = sel.xpath('//link[@rel="alternate"]/@title').extract()
			if text_to_remove and head_title:
				words = (' '.join(text_to_remove)+head_title).split()
				if Counter(words).most_common(3):
					for wor in Counter(words).most_common(3):
						head_title_clean = head_title_clean.replace(wor[0],'')

		[h1,h1a,h2,h2a,h3,h3a]=["//h1","//h1/a","//h2","//h2/a","//h3","//h3/a"]
		head_xpaths = [h1a,h1,h2a,h2,h3a,h3]
		title_lists = [sel.xpath(head+'//text()').extract() for head in head_xpaths]
		title_dict = OrderedDict(zip(head_xpaths,title_lists))
		for title_xpaths,title_list in title_dict.iteritems():
			if title_list:
				for titles in title_list:
					#to prevent from one word getting higher score
					if titles.count(' ')>0 or head_title_clean.count(' ')<1:
						title_ratio = fuzz.partial_token_sort_ratio(titles,head_title_clean)
						if title_ratio>title_score:
							title_score = title_ratio
							title = titles
							title_xpath = title_xpaths
							if title_score==100 and title.count(' ')>0:
								break
						#slug_ratio to be added in case
						slug_ratio = fuzz.partial_ratio(titles.lower(),slug)
						if slug_ratio>80:
							slug_score = slug_ratio
							title = titles
							title_xpath = title_xpaths
							if slug_score==100:
								break
				if slug_score==100:
					break
				if title_score==100:
					break
		if title_score<51 and slug_score<81:
			title = head_title_clean
		return title,title_xpath

	def post_text_extract(self,sel,post_xpaths):
		sel = sel
		post_xpaths = post_xpaths
		div_len = 0
		div_html = ''
		div_text = ''
		post_text = ''

		for post_xpath in post_xpaths:
			div_html = sel.xpath(post_xpath).extract()
			div_text = clean_html(' '.join(div_html))
			if len(div_text) > div_len:
				if len(re.compile('\w+ \d+,.\d+').findall(div_html[0])) > 10:
					continue
				else:
					post_text = ' '.join(div_text.split())
					div_len = len(div_text)
		return post_text,div_len

	def find_post_text(self,title_xpath,sel):
		post_xpaths1 = [title_xpath + "/following-sibling::div[1]", title_xpath +
						"/following-sibling::div[2]", title_xpath + "/following-sibling::div[3]"]
		post_xpaths2 = [title_xpath + "/../following-sibling::div[1]", title_xpath +
						"/../following-sibling::div[2]", title_xpath + "/../following-sibling::div[3]"]
		post_xpaths3 = [title_xpath + "/../../following-sibling::div[1]", title_xpath +
						"/following-sibling::div[2]", title_xpath + "/following-sibling::div[3]"]

		post_text1,post_len1 = self.post_text_extract(sel,post_xpaths1)
		post_text2,post_len2 = self.post_text_extract(sel,post_xpaths2)
		post_text3,post_len3 = self.post_text_extract(sel,post_xpaths3)
		pos = [' '.join(post_text1.split()),' '.join(post_text2.split())]
		post_text = max(pos,key=lambda p:len(p))
		if len(post_text3)>len(post_text):
			if post_text3.lower().count('comments')<=post_text.lower().count('comments'):
				post_text = post_text3

		p_post=sel.xpath('//h1/../p')
		if title_xpath =='//h1':
			if len(p_post)>=5:
				post_text = clean_html(' '.join(p_post.xpath('//text()').extract())).strip()

		return post_text
