# -*-* coding:UTF-8
import os
import aioredis


class Plugin(Base):
    __info__ = {
        "author": "doimet",
        "references": ["-"],
        "description": "redis服务口令破解",
        "datetime": "2022-01-02"
    }

    @cli.options('ip', desc="设置输入目标", default='{self.target.value}')
    @cli.options('port', desc="设置目标端口", type=int, default=6379)
    @cli.options('method', desc="口令爆破模式 1:单点模式 2:交叉模式", type=int, default=2)
    @cli.options('username', desc="用户名称或字典文件", default=os.path.join('data', 'redis_username.dict'))
    @cli.options('password', desc="用户密码或字典文件", default=os.path.join('data', 'redis_password.dict'))
    @cli.options('timeout', desc="连接超时时间", type=int, default=3)
    @cli.options('workers', desc="协程并发数量", type=int, default='{self.config.general.asyncio}')
    def ip(self, ip, port, method, username, password, timeout, workers) -> dict:
        with self.async_pool(max_workers=workers) as execute:
            for u, p in self.build_login_dict(
                    method=method,
                    username=username,
                    password=password,
            ):
                execute.submit(self.custom_task, ip, port, u, p, timeout)
            return {'LoginInfo': execute.result()}

    async def custom_task(self, ip, port, username, password, timeout):
        self.log.debug(f'Login => username: {username}, password: {password}')
        conn = aioredis.from_url(f"redis://:{password}@{ip}", encoding="utf-8", decode_responses=True)
        conn.close()
        self.log.info(f'Login => username: {username}, password: {password} [success]')
        return {
            'port': port,
            'server': 'redis',
            'username': username,
            'password': password
        }
