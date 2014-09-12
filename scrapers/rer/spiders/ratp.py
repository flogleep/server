from scrapy.selector import Selector
from scrapy.spider import Spider
from rer.items import RerScrappersItem
from scrapy import log
import time
import datetime


STATIONS_FILE = '/root/scrapers/rer/ratp_stations_list.txt'
ROOT_URL = 'http://www.ratp.fr/horaires/fr/ratp/rer/prochains_passages/RA/'
SUFFIXES = ['/A', '/R']


f = open(STATIONS_FILE, 'r')
stations_list = [s.rstrip() for s in f]
urls = []
for suf in SUFFIXES:
    urls += [ROOT_URL + s + suf for s in stations_list]

class RatpSpider(Spider):
    name = 'ratp'
    allowed_domains = ['ratp.fr']
    start_urls = urls

    def parse(self, response):
        sel = Selector(response)
        if response.url not in self.start_urls:
            self.log('Url (%s) not in list.' % response.url, level=log.ERROR)
            self.log('Origin url : %s' % response.request.url, level=log.ERROR)
        else:
            i = RerScrappersItem()

            i['time'] = datetime.datetime.now()
            i['full_mission'] = sel.xpath(
                '//div[@id="contenu_horaire"]//td[@class="name"]/a/text()'
            )[0].extract()
            i['station'] = sel.xpath(
                '//div[@class="line_details"]/span/text()'
            )[0].extract()
            i['status'] = sel.xpath(
                '//div[@id="contenu_horaire"]//td[@class="passing_time"]/text()'
            )[0].extract()

            self.log('%s : parsed' % i['station'], level=log.DEBUG)

            #yield response.request

            yield i
