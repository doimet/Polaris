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

    def ip(self) -> dict:
        with self.async_pool(max_workers=self.target.setting.asyncio, threshold=self.threshold) as execute:
            for username, password in self.build_login_dict(
                    self.target.args.method,
                    username=self.target.args.username or os.path.join('data', f'mysql_username'),
                    password=self.target.args.password or os.path.join('data', f'mysql_password'),
            ):
                execute.submit(self.task, username, password)
            return {'LoginInfo': execute.result()}

    async def task(self, username, password):
        self.log.debug(f'Login => username: {username}, password: {password}')
        conn = pymysql.connect(
            host=self.target.value,
            port=3306,
            user=username,
            passwd=password,
            connect_timeout=self.target.args.timeout,
            charset="utf-8"
        )
        conn.close()
        self.log.info(f'Login => username: {username}, password: {password} [success]')
        return {
            'port': 3306,
            'server': 'mysql',
            'username': username,
            'password': password
        }
