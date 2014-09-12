# Scrapy settings for rer project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#

BOT_NAME = 'rer'

SPIDER_MODULES = ['rer.spiders']
NEWSPIDER_MODULE = 'rer.spiders'

ITEM_PIPELINES = {
    'rer.pipelines.StatusPipeline': 100,
    'rer.pipelines.FormatPipeline': 200,
    'rer.pipelines.SqlFilterPipeline': 800,
    'rer.pipelines.SqlInsertPipeline': 900
}

LOG_FORMATTER = 'rer.log_formatters.QuietLogFormatter'
# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'rer (+http://www.yourdomain.com)'

DOWNLOAD_DELAY = 0.

CONCURRENT_REQUESTS = 32
