# 文件分享系统
## 项目简介
这是一个简单的文件分享系统，允许用户上传文件并生成下载链接。系统支持以下功能：

- 文件上传与临时存储
- 生成唯一下载链接
- 设置下载次数限制
- 自动清理过期文件


## 使用说明
### 启动程序
```
python app.py
```

- 访问首页 `/`
- 上传 `/admin/add`


## 还需要完成的内容
- [X] 下载次数的改进，将下载次数更新放到下载成功而非鉴权
- [X] 规范化static问题;icon问题
- [X] 修缮40x报错网页
- [X] 增加页面用于查看当前服务器状态

## 提高
- 使用更为人性化的路径，引导输入密码
- 使用session管理代码
- 添加爆破密码防御，频繁下载防御


## 后期
- [X] 改进上传端口的密码输入
- [X] 改进session过期
- [X] 防止暴力破解管理员;429报错
- [X] 时区
- [ ] 查看所有文件（分页）
- [ ] 整理代码和环境

## 常用Git代码
丢弃所有未提交的更改（工作区和暂存区）
```
git reset --hard HEAD
```