# -*-* coding:UTF-8


class Plugin(Base):
    __info__ = {
        "author": "doimet",
        "references": ["https://www.cmd5.com"],
        "description": "CMD5解密hash",
    }

    @cli.options('input', description='需要解密的hash', default='{self.target.value}')
    def md5(self, _input) -> dict:
        r = self.request(
            method='get',
            url='https://www.cmd5.com/api.ashx',
            params={'email': self.config.cmd5.email, 'key': self.config.cmd5.key, 'hash': _input}
        )
        if r.status_code == 200:
            response = r.text
            error_message = {
                0: '解密失败',
                -1: '无效的用户名密码',
                -2: '余额不足',
                -3: '解密服务器故障',
                -4: '不识别的密文',
                -7: '不支持的类型',
                -8: 'api权限被禁止',
                -999: '其它错误'
            }
            for code, message in error_message.items():
                if f'CMD5-ERROR:{code}' in response:
                    raise Exception(message)
            return {
                'MD5明文': response
            }

    @cli.command
    def demo(self, name):
        print(name)

    @cli.command
    def test(self):
        print('hello world1')
