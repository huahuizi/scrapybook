import json
import traceback

from treq import put
from urllib import quote
from twisted.internet import defer
from scrapy.exceptions import NotConfigured
from twisted.internet.error import ConnectError
from twisted.internet.error import ConnectingCancelledError


class EsWriter(object):
    """A pipeline that writes to Elastic Search"""

    @classmethod
    def from_crawler(cls, crawler):
        """Create a new instance and pass it ES's url"""

        # Get Elastic Search URL
        es_url = crawler.settings.get('ES_PIPELINE_URL', None)

        # If doesn't exist, disable
        if not es_url:
            raise NotConfigured

        return cls(es_url)

    def __init__(self, es_url):
        """Store url and initialize error reporting"""

        # Store the url for future reference
        self.es_url = es_url
        # Report connection error only once
        self.report_connection_error = True

    @defer.inlineCallbacks
    def process_item(self, item, spider):
        """
        Pipeline's main method. Uses inlineCallbacks to do
        asynchronous REST requests
        """

        logger = spider.logger

        try:
            # Create a json representation of this item
            json_doc = json.dumps(dict(item), ensure_ascii=False)

            # Extract the ID (it's the URL)
            id = item['url'][0]

            # Calculate item's ES endpoint
            endpoint = '%s/%s' % (self.es_url, quote(str(id), ''))

            # Debug log the insert
            msg = "Insering \"%s...\" to %s" % (json_doc[:100], endpoint)
            logger.debug(msg)

            # Make the request
            yield put(endpoint, json_doc.encode("utf-8"), timeout=5)

        except (ConnectError, ConnectingCancelledError):
            if self.report_connection_error:
                logger.error("Can't connect to ES: %s" % self.es_url)
                self.report_connection_error = False
        except:
            print traceback.format_exc()
        finally:
            # Return the item for the next stage
            defer.returnValue(item)