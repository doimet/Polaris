# 插件编写
## 内置对象
+ `target`: 
  + `target.key`: 用于获取输入类型
  + `target.value`: 用于获取输入目标
  + `target.args`: 用于获取插件参数
  + `target.setting`: 用于获取程序配置
+ `log`: 
  + `log.debug`: 用于输出调式信息
  + `log.info`: 用于输出普通信息
  + `log.warn`: 用于输出警告信息
  + `log.error`: 用于输出错误信息
+ `async_pool`

## 内置方法
+ 网络请求: 
  + `request`: 
  + `async_http`:异步时调用
+ 其他方法:
  + `build_random_int`
  + `build_random_str`
  + `jsonp_to_json`
  + `load_file`
  + `build_login_dict`
## 内置装饰器
+ `cli`: 类方法装饰器, 将方法扩展成可交互的终端模式(使用--shell参数调用)
  + cli.command: 适用于无参数的情况
  + cli.options: 适用于有参数的情况

## 插件模板
### 信息收集插件模板
```shell script
# -*-* coding:UTF-8
import lxml.etree


class Plugin(Base):
    __info__ = {
        "author": "作者",
        "references": ["来源"],
        "description": "描述信息",
        "datetime": "日期"
    }

    def domain(self) -> dict:
        """ 编写代码 """
        ...
```
### 漏洞利用插件模板
```shell script
# -*-* coding:UTF-8


class Plugin(Base):
    __info__ = {
        "author": "作者",
        "references": ["来源"],
        "description": "描述信息",
        "datetime": "日期"
    }

    def url(self) -> dict:
        """ 验证代码 """
        ...
    
    @Cli.options('cmd', description="执行命令", default="whoami")
    def attack(self) -> dict:
        """ 利用代码 """
        ...

```
### 口令爆破插件模板
```shell script
# -*-* coding:UTF-8
import os


class Plugin(Base):
    __info__ = {
        "author": "作者",
        "references": ["来源"],
        "description": "描述信息",
        "datetime": "日期"
    }

    def ip(self) -> dict:
        """ 编写代码 """
        with self.async_pool(max_workers=self.target.setting.asyncio, threshold=self.threshold) as execute:
            for username, password in self.build_login_dict(
                    method=self.target.args.method,
                    username=self.target.args.username or os.path.join('data', 'test_username'),
                    password=self.target.args.password or os.path.join('data', 'test_password'),
            ):
                execute.submit(self.task, username, password)
            return {'LoginInfo': execute.result()}

    async def task(self, *args) -> dict:
        """ 编写代码 """
        ...
```
### 渗透辅助插件模板
```shell script
# -*-* coding:UTF-8


class Plugin(Base):
    __info__ = {
        "author": "作者",
        "references": ["来源"],
        "description": "描述信息",
        "datetime": "日期"
    }

    def md5(self) -> dict:
        """ 编写代码 """
        ...
```

## 注意事项
1. 为了方便对插件返回数据进行处理, 插件的返回数据类型需统一为`dict`(shell方法返回值类型需是`str`)
2. 除非调用内置打印输出方法, 任何写在插件内部的打印输出方法都不会被执行
3. 插件内定义的方法名称并非固定的, 而是根据这个插件所接受的输入类型来以此命名的
4. 一个插件类限定只允许使用一个类方法装饰器