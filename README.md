# AutoJogging

**WARNING: This project is only for learning and communication purposes. It is strictly prohibited to use it for commercial or illegal purposes. Any legal liability incurred for other purposes is not related to the author!**

**警告：此项目仅供学习交流使用，严禁用于商业用途级非法用途，如作他用所承受的法律责任一概与作者无关！**

通过抓取某大学健康跑软件的包，使用 Python 内置函数和模组，实现模拟客户端向服务端发送、请求数据，实现自动完成健康跑。

## How to use

首先在 Config.ini 中配置用户信息，然后运行 autoJogging.py 即可。

若要设置每天定时跑两次，可将脚本上传至服务端，并在 Crontab 中加入以下语句：

```
20 6,14 * * * python3 $脚本路径$/AutoJogging.py
```

## Requirements

- Python 3.6 or higher