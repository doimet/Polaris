# -*-* coding:UTF-8
import os
from pymemcache.client.base import Client


class Plugin(Base):
    __info__ = {
        "author": "doimet",
        "references": ["-"],
        "description": "memcache服务口令破解",
        "datetime": "2022-01-02"
    }

    def ip(self) -> dict:
        with self.async_pool(max_workers=self.target.setting.asyncio, threshold=self.threshold) as execute:
            for username, password in self.build_login_dict(
                    method=self.target.args.method,
                    username=self.target.args.username or os.path.join('data', 'memcache_username'),
                    password=self.target.args.password or os.path.join('data', 'memcache_password'),
            ):
                execute.submit(self.task, username, password)
            return {'LoginInfo': execute.result()}

    async def task(self, username, password):
        self.log.debug(f'Login => username: {username}, password: {password}')
        conn = Client(
            server=(self.target.value, 11211),
            connect_timeout=self.target.args.timeout,
            timeout=self.target.args.timeout
        )
        conn.version()
        conn.close()
        self.log.info(f'Login => username: {username}, password: {password} [success]')
        return {
            'port': 11211,
            'server': 'memcache',
            'username': username,
            'password': password
        }
