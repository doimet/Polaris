# -*-* coding:UTF-8
import os
import toml
import socket
import asyncio
import tornado.web
import tornado.escape
import tornado.options
from tornado.ioloop import IOLoop
from core.app import Application
from tornado.web import HTTPError
from core.utils import build_random_str

tornado.options.define('port', default=10020, type=int)
tornado.options.define('auth', default=build_random_str(16))
app = Application(config=toml.load(os.path.join('conf', 'setting.toml')), is_cli=False)


class BaseHandler(tornado.web.RequestHandler):

    def set_default_headers(self):
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Access-Control-Allow-Headers', 'x-requested-with')
        self.set_header('Access-Control-Allow-Methods', 'POST,GET')

    def get_safe_argument(self, name, default="", strip=True):
        argument = self._get_argument(name, default, self.request.arguments, strip)
        return argument

    def get_safe_data(self) -> dict:
        data = tornado.escape.json_decode(self.request.body)
        data = {k: (v if isinstance(v, str) else v) for k, v in data.items()}
        return data

    async def prepare(self) -> None:
        token = self.request.headers.get("token", default="")
        if not token or tornado.options.options.auth != token:
            raise HTTPError(403)


class NodeHandle(BaseHandler):

    async def get(self):
        command = self.get_safe_argument("command")
        plugins = self.get_safe_argument("plugins")
        app.options.update({"command": command, "plugin": [_ for _ in plugins.split(',') if _]})
        app.shows()
        return await self.finish({"code": 0, "data": app.infoset})

    async def post(self):
        json_data = self.get_safe_data()
        app.dataset = []
        app.log.records = []
        app.options.update(
            {
                "command": json_data["command"],
                "plugin": [_ for _ in json_data["plugins"].split(',') if _],
                "input": json_data["input"]
            }
        )
        app.setup()
        return await self.finish(
            {
                **json_data,
                "data": app.dataset,
                "logs": ''.join(app.log.records)
            }
        )


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    tornado.options.parse_command_line()
    print(f'\r\033[0;34m[+]\033[0m API-URL: http://{ip}:{tornado.options.options.port}/api/node')
    print(f'\r\033[0;34m[+]\033[0m PASSWORD: {tornado.options.options.auth}')
    loop = asyncio.get_event_loop()
    service = tornado.web.Application(
        [
            (r"/api/node", NodeHandle),
        ],
        loop=loop
    )
    # 启动Web服务
    service.listen(tornado.options.options.port)
    IOLoop.current().start()


if __name__ == "__main__":
    main()
