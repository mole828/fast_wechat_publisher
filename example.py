
from wechatpy.replies import create_reply
from wechatpy.messages import BaseMessage, TextMessage
import logging

if __name__ == '__main__':
    import __init__ as pub
    publisher = pub.Publisher(token='AAAAA', log_formatter_type=pub.default_formatter)

    logger = logging.Logger(__name__, logging.DEBUG)
    handler = logging.StreamHandler()
    handler.formatter = pub.default_formatter()
    logger.addHandler(handler)
    

    @publisher.handle
    def _(msg: TextMessage):
        logger.info("user handle in")
        return create_reply("user handle in",message=msg)

    publisher.run(path = '/wechat', port = 19000)

