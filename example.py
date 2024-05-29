
from wechatpy.replies import create_reply
from wechatpy.messages import BaseMessage, TextMessage

if __name__ == '__main__':
    import __init__ as pub
    publisher = pub.Publisher('AAAAA')

    @publisher.handle
    def _(msg: TextMessage):
        print('user handle step in')
        return create_reply("user handle in",message=msg)

    publisher.run(path = '/wechat', port = 19000)

