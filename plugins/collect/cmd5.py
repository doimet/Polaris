# -*-* coding:UTF-8


class Plugin(Base):
    __info__ = {
        "name": "CMD5",
        "description": "CMD5解密hash",
        "references": ["https://www.cmd5.com"],
    }

    def hash(self) -> dict:
        r = self.request(
            method='get',
            url='https://www.cmd5.com/api.ashx',
            params={'email': self.config.cmd5.email, 'key': self.config.cmd5.key, 'hash': self.target.value}
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
                'HashPlaintext': response
            }
