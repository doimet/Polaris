# 插件编写
## 内置对象
+ `target`: 
  + `target.key`: 用于获取输入类型
  + `target.value`: 用于获取输入目标
+ `config`: 用于获取配置参数
+ `log`: 
  + `log.debug`: 用于输出调式信息
  + `log.info`: 用于输出普通信息
  + `log.warn`: 用于输出警告信息
  + `log.error`: 用于输出错误信息
+ `async_pool`: 用于创建异步连接池(上下文管理)
  ```
  async_pool(max_workers: int) -> Object
  传入并发数量
  返回执行对象
  ```
+ `echo_query`: 针对命令无回显时调用(上下文管理)
  ```
  echo_query() -> Object
  返回查询对象
  ```
  
## 内置方法

+ `request`: 网络请求方法
  ```
  request(method: str, url: str, path: str, **kwargs) -> Response
  传入请求参数
  返回响应对象
  ```
+ `async_http`:异步网络请求方法
  ```
  await self.async_http(method: str, url: str, path: str, **kwargs) -> Response
  传入请求参数
  返回响应对象
  ```
+ `build_random_int`: 生成随机整数
  ```
  build_random_int(length: int) -> int
  传入生成长度
  返回随机整数
  ```
+ `build_random_str`: 生成随机字符串
  ```
  build_random_str(length: int) -> str
  传入生成长度
  返回随机字符串
  ```
+ `build_random_lower_str`: 生成随机小写字符串
  ```
  build_random_lower_str(length: int) -> str
  传入生成长度
  返回随机小写字符串
  ```
+ `build_random_upper_str`: 生成随机大写字符串
  ```
  build_random_upper_str(length: int) -> str
  传入生成长度
  返回随机大写字符串
  ```
+ `jsonp_to_json`: jsonp字符串转json
  ```
  jsonp_to_json(jsonp_str: str) -> dict
  传入jsonp字符串
  返回字典类型数据
  ```
+ `build_web_shell`: 生成WebShell
  ```
  build_web_shell(lang: str) -> tuple
  传入生成的脚本语言
  返回webshell代码、webshell密码、webshell验证代码
  注: 目前只支持php、asp、aspx三种语言, 后面会添加jsp
  ```
+ `build_login_dict`: 构建口令字典
  ```
  build_login_dict(method: int, username: str, password: str) -> iterable
  传入口令组合模式、用户名称字典、用户密码字典
  返回用户名称、用户密码
  ```
## 内置装饰器
+ `cli`: 类方法装饰器, 将方法扩展成可交互模式(使用--shell参数调用)
  + cli.command: 适用于无参数的情况
  + cli.options: 适用于有参数的情况

## 插件模板
### 信息收集插件模板
```python
# -*-* coding:UTF-8


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
```python
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
    
    @cli.options('cmd', desc="执行命令", default="whoami")
    def attack(self) -> dict:
        """ 利用代码 """
        ...

```
### 口令爆破插件模板
```python
# -*-* coding:UTF-8
import os


class Plugin(Base):
    __info__ = {
        "author": "作者",
        "references": ["来源"],
        "description": "描述信息",
        "datetime": "日期"
    }
    
    @cli.options('ip', desc="设置输入目标", default='{self.target.value}')
    @cli.options('port', desc="设置目标端口", type=int, default=3306)
    @cli.options('method', desc="口令爆破模式 1:单点模式 2:交叉模式", type=int, default=2)
    @cli.options('username', desc="用户账号或字典文件", default=os.path.join('data', 'mysql_username.dict'))
    @cli.options('password', desc="用户密码或字典文件", default=os.path.join('data', 'mysql_password.dict'))
    @cli.options('timeout', desc="连接超时时间", type=int, default=5)
    @cli.options('workers', desc="协程并发数量", type=int, default=50)
    def ip(self, ip, port, method, username, password, timeout, workers) -> dict:
        with self.async_pool(max_workers=workers) as execute:
            for u, p in self.build_login_dict(method=method, username=username, password=password):
                execute.submit(self.custom_task, ip, port, u, p, timeout)
            return {'LoginInfo': execute.result()}

    async def custom_task(self, ip, port, username, password, timeout):
        """ 编写代码 """
        ...
```
### 渗透辅助插件模板
```python
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
2. 插件内定义的方法名称并非固定的, 而是根据这个插件所接受的输入类型来以此命名的
3. 一个插件类限定只允许使用一个类方法装饰器