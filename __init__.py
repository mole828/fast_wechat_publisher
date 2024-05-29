from collections import defaultdict
import wechatpy
from fastapi import FastAPI, Request, responses
import wechatpy.exceptions
import wechatpy.messages
import wechatpy.replies
import wechatpy.utils
from typing import Type, Callable, TypeVar


_TK = TypeVar('_TK')
_TV = TypeVar('_TV')

class Type2Func(dict[_TK, _TV]):
    default_factory: Callable[[], _TV]
    def __missing__(self, t: _TK) -> _TV:
        return self.default_factory()

class Publisher:
    token: str

    fastapi: FastAPI
    handlers: Type2Func[_TK, Callable[[_TK], wechatpy.replies.BaseReply]]

    def __init__(self, token: str) -> None:
        self.fastapi = FastAPI()
        self.token = token

        self.handlers = Type2Func()
        def default_factory():
            def f(msg: wechatpy.messages.BaseMessage) -> wechatpy.replies.BaseReply:
                return wechatpy.replies.create_reply(None)
            return f
        self.handlers.default_factory = default_factory

    def handle(self, handler: Callable[[_TK], wechatpy.replies.BaseReply]):
        t = next(iter(handler.__annotations__.values()))
        self.handlers[t] = handler
        print('add', t, 'handler')

    def run(self, *, path: str='/', port: int=8000):
        @self.fastapi.get(path)
        def url_check(signature: str, timestamp: str, nonce: str, echostr: str) -> responses.PlainTextResponse:
            try:
                wechatpy.utils.check_signature(self.token, signature=signature, timestamp=timestamp, nonce=nonce)
            except wechatpy.exceptions.InvalidSignatureException as e:
                return e
            return responses.PlainTextResponse(echostr)
        
        @self.fastapi.post(path)
        async def _(request: Request, signature: str, timestamp: str, nonce: str):
            try:
                wechatpy.utils.check_signature(self.token, signature=signature, timestamp=timestamp, nonce=nonce)
            except wechatpy.exceptions.InvalidSignatureException as e:
                print(request.__dict__)
                raise e
            body = await request.body()
            msg = wechatpy.parse_message(body)

            print(type(msg), 'be handle')
            return self.handlers[type(msg)](msg).render()
        
        import uvicorn
        uvicorn.run(app=self.fastapi, port=port)
