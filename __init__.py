from collections import defaultdict
import wechatpy
from fastapi import FastAPI, Request, responses
import wechatpy.exceptions
import wechatpy.messages
import wechatpy.replies
import wechatpy.utils
from typing import Type, Callable, TypeVar
import logging


_TK = TypeVar('_TK')
_TV = TypeVar('_TV')

class Type2Func(dict[_TK, _TV]):
    default_factory: Callable[[], _TV]
    def __missing__(self, t: _TK) -> _TV:
        return self.default_factory()

class default_formatter(logging.Formatter):
    def format(self, record):
        log_format = f"%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        formatter = logging.Formatter(log_format)
        return formatter.format(record)

class Publisher:
    token: str
    fastapi: FastAPI
    handlers: Type2Func[_TK, Callable[[_TK], wechatpy.replies.BaseReply]]
    logger: logging.Logger
    
    def __init_logger(self, log_formatter_type: Type[logging.Formatter]):
        self.logger = logging.Logger("wechat.publisher", logging.INFO)
        handler = logging.StreamHandler()
        handler.formatter = log_formatter_type()
        self.logger.addHandler(handler)
        
        from uvicorn.config import LOGGING_CONFIG
        LOGGING_CONFIG["formatters"][self] = {"()": log_formatter_type}
        LOGGING_CONFIG["handlers"]["default"]["formatter"] = self
        LOGGING_CONFIG["handlers"]["access"]["formatter"] = self

    def __init__(self, token: str, log_formatter_type:Type[logging.Formatter] = default_formatter) -> None:
        self.fastapi = FastAPI()
        self.token = token

        self.handlers = Type2Func()
        def default_factory():
            def f(msg: wechatpy.messages.BaseMessage) -> wechatpy.replies.BaseReply:
                return wechatpy.replies.create_reply(None)
            return f
        self.handlers.default_factory = default_factory
        self.__init_logger(log_formatter_type)
        

    def handle(self, handler: Callable[[_TK], wechatpy.replies.BaseReply]):
        t = next(iter(handler.__annotations__.values()))
        self.handlers[t] = handler
        self.logger.info(f"add {t} handle")

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
                self.logger.error(request.__dict__)
                raise e
            body = await request.body()
            msg = wechatpy.parse_message(body)

            self.logger.info({"msg_type": type(msg)})
            return self.handlers[type(msg)](msg).render()
        
        import uvicorn
        uvicorn.run(app=self.fastapi, port=port)
