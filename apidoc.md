# Douban App Api 文档
本文描述豆瓣APP的API接口


## API基本结构

#### HTTP信息
> 方法: ***GET***
> 版本: ***HTTP/1.1***

#### 基本URL参数
> udid: 唯一ID，一般用设备ID即可
> device_id: 设备ID
> channel: 渠道，如***Meizu_Market***
> apiKey: APIKEY，Android平台为***0dad551ec0f84ed02907ff5c42e8ec70***
> os_rom: OS ROM版本，如***flyme4***

#### 请求头参数
> User-Agent: UA信息，如***api-client/1 com.douban.frodo/4.1.1(71) Android/22 m2note Meizu m2 note  rom:flyme4***
> Authorization: 身份信息，如***Bearer 336622359cd0sf6asaa2safsdas02ek1***
>


## API列表

#### 获取首页数据
地址 https://frodo.douban.com/api/v2/recommend_feed
附加URL参数: 
> since_id: 用于分页，上一次返回数据的recommend_feeds[-1].id
> gender: 性别?未知
> mooncake: 未知
> icecream: 未知
> apple: 未知

#### 日记数据
地址 https://frodo.douban.com/api/v2/note/日记ID
附加URL参数: 无

#### 日记评论
地址 https://frodo.douban.com/api/v2/note/日记ID/comments
附加URL参数: 无

#### 日记相关推荐
地址 https://frodo.douban.com/api/v2/note/日记ID/recommendations
附加URL参数: 无

