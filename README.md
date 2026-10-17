# 高空幕墙机器人数据大屏

这是一个基于 Vue.js 和 Flask 的数据可视化大屏项目，用于展示高空幕墙机器人的各项数据。

## 项目结构

```
shujudaping/
├── data-dashboard/          # Vue.js 前端项目
│   ├── src/
│   │   ├── views/          # 页面组件
│   │   ├── components/     # 公共组件
│   │   └── assets/         # 静态资源
│   └── public/
└── server/                  # Flask 后端服务
    ├── app.py
    └── requirements.txt
```

## 技术栈

- **前端**: Vue 3 + ECharts + Element Plus
- **后端**: Flask + PyMySQL + JWT
- **数据库**: MySQL

## 功能模块

- 超声波雷达监控
- 深度摄像头监控
- 温湿度传感器数据
- 机器人状态监控
- 数据可视化大屏

## 安装运行

### 前端
```bash
cd data-dashboard
npm install
npm run serve
```

### 后端
```bash
cd server
pip install -r requirements.txt
python app.py
```

## 作者

胡钰迈 (hu-yumai)
黄鸿乐 (huangongle)
蒙虹伶 (mon-ling)