# -*-* coding:UTF-8
from pymemcache.client.base import Client


class Plugin(Base):
    __info__ = {
        "author": "doimet",
        "references": ["-"],
        "description": "memcache服务口令破解",
    }

    @cli.options('ip', description="设置输入目标", default='{self.target.value}')
    @cli.options('port', description="设置目标端口", type=int, default=11211)
    @cli.options('timeout', description="连接超时时间", type=int, default=3)
    def ip(self, ip, port, timeout) -> dict:
        conn = Client(
            server=(ip, port),
            connect_timeout=timeout,
            timeout=timeout
        )
        conn.version()
        conn.close()
        self.log.info(f'Login => username: null, password: null [success]')
        return {
            'LoginInfo': {
                'port': port,
                'server': 'memcache',
                'username': 'null',
                'password': 'null'
            }
        }
