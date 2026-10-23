# 智能清洁机器人监控平台 · 后续优化建议

> 生成日期：2026-10-19
> 范围：前端 `data-dashboard`（Vue3 + React 双实现待确认）、YOLO 后端、SSH 桥后端、设备端脚本
> 此文仅汇总建议，供你按优先级慢慢消化，未做任何代码改动。

---

## 一、必须处理：安全风险（最高优先级）

1. **硬编码设备 SSH 明文凭据**
   - 位置：`data-dashboard/src/camera_yolo_server/camera_yolo_server.py`（约 L381-383）与 `ssh_server.py`，含内网 IP `192.168.0.2`、用户 `nvidia`、密码 `nvidia`。
   - 影响：一旦仓库公开/泄露，任何拿到代码的人可直接 SSH 进设备执行任意命令。
   - 建议：
     - 改为从环境变量或本地配置文件读取（如 `.env` / `config.json`，加入 `.gitignore`）。
     - 或提供 `--config`/`--user`/`--pass` 启动参数，默认不携带敏感信息。
   - 同理：前端「控制台」表单默认填充设备凭据属于便捷但泄密点，建议改为留空、启动时读取本地环境变量注入。
2. **SSH/终端桥接无鉴权**
   - `ssh_server.py` 绑定 `0.0.0.0:8084`，未做认证；任何能访问 8084 的人都能连任意主机。
   - 建议：默认仅监听 `127.0.0.1`（开发环境），或增加一次性口令/Token 校验后再转发。
3. **高危快捷命令**：`sudo shutdown -h now` 已加入快捷栏，误点即关机会影响作业。建议该按钮加二次确认，或改为延时关机（`-h +1`）并提示。
4. **发布前自检**：`git grep -n -iE "password|passwd|192\.168|nvidia"` 扫一遍，确认无明文凭据后再公开。

---

## 二、稳定性 / 健壮性

1. **websockets 版本兼容锁定**
   - 本会话发现 `websockets>=12` 的 `serve()` 签名在无 runloop 时会抛 `no running event loop`。
   - 建议在 requirements/启动脚本中**锁定版本号**（如 `websockets==14.x`），避免设备升级 pip 后直接崩。
2. **SSH 桥连接治理**
   - 现有：写超时清理僵尸连接、try/finally 释放计数、并发上限。
   - 建议补充：
     - `connect` 阶段统一带超时与错误码回传前端（区分"主机不可达/Wrong user/host key changed"）。
     - 空闲 N 分钟自动断开，避免长期占用设备侧 shell 与连接。
     - （可选）命令白名单/只读模式开关，供现场调试怕误操作时用。
3. **keep-alive 与后台资源**
   - 已用 `<keep-alive>` 保留页面状态；代价是所有被缓存页面常驻内存且**相机 MJPEG 流、ROS 订阅在后台持续运行**。
   - 建议：切换离开相机页时主动置空 `<img src>` 暂停拉流、切回再重连（省带宽与浏览器连接槽，当前浏览器每主机 6 连接槽有限）。
4. **YOLO 后端异常兜底**
   - 相机流断开/重连、推理设备 GPU 掉线等异常目前多为静默 catch。
   - 建议统一在 `/status` 暴露模型是否加载成功、当前帧率、最近错误，前端展示"识别降级"提示。
5. **启动脚本（serve-all.js）看门狗**
   - 用 `npm run serve` 并行拉起三个服务，若某个子进程闪退无感知。
   - 建议加"子进程退出自动重启 + 汇总结错误到终端"。

---

## 三、前端体验

1. **终端渲染**
   - 已用 WebGL/Canvas 渲染器解决"英文单词插空格错位"；字体栈为 Sarasa Mono / YaHei Mono → Consolas。
   - 建议补 `prefers-reduced-motion` 与窄屏布局降级（参考其他页面的窄屏处理）。
2. **i18n 一致性**
   - 新增文案（liveFps、终端提示等）已同步 zh/en/th/ms/id/vi 六语言。
   - 建议提交前用脚本比对各语言文件 key 是否齐全，防止漏键。
3. **快捷命令可配置化**
   - 目前快速命令是硬编码数组。建议抽成 JSON（本地 `config` 或后端下发），便于现场快速增删命令而无需改码重建。
4. **大屏数据**
   - 「实时超声波距离趋势」已改为 Y 轴动态缩放 + X 轴 1 小时滚动窗口；数据量大时建议加 `sampling: 'lttb'` 降采样，避免 re-render 卡顿。
   - 三路数值/传感器视图建议抽公共 ECharts 配置，减少重复代码。

---

## 四、工程化与依赖

1. **清理未使用依赖**
   - 审查 `package.json`，删除脚手架残留/未引用包（旧版 `xterm` 已换 `@xterm/xterm` 等）。可用 `npx knip` 或 ESLint no-unused 辅助定位。
2. **Vue3 / React 双实现**
   - 若项目同时维护 Vue3 与新版 React 实现，建议明确一份为"主干"，避免两套逻辑漂移；共享的 ROS/Store 逻辑抽公共层。
3. **配置外置**
   - 设备 IP、端口、相机地址、SSH 凭据集中到配置文件/环境变量，杜绝散落硬编码。
4. **代码质量信号**
   - 多处使用 `/* eslint-disable no-empty */` 的守卫性空 catch——建议统一加日志（debug 级别）便于排障，而不是完全吞掉。
   - 长视图文件（如 Screen1.vue）建议按"图表/订阅/日志"拆分组合逻辑（Composables）。
5. **构建与提交规范**
   - 已建 `.gitignore` 排除 `.trae` 目录；确认远程仓库更新后，`git rm -r --cached .trae` 已执行。
   - 建议补 CI 的 build + lint 检查，提交前自动卡住硬编码密钥（如用 gitleaks/semgrep）。

---

## 五、性能与设备负载

1. **相机 HTTP 节点**：帧缓存复用 + 版本号推送 + TCP_NODELAY + 10s 写超时 已完成；建议保留负载基准数据，跟踪设备 CPU/内存趋势。
2. **YOLO 推理**：推理在本地 GPU 跑，可下调 `imgsz` 或按目标框裁剪提速；建议对帧率/延迟做基准，确认无需进一步降载。
3. **日志**：Werkzeug 与 ROS `*.log` 建议统一轮转，避免长期运行占满磁盘。

---

## 六、运维侧（设备端）

1. **服务自启动**：`start_all_services.py` 为手动脚本；若需开机自动拉起，建议封装为 systemd unit（camera / rosbridge / http / stm32 / ultrasonic / localization）。
2. **免 sudo 权限**：`robot_service_manager.py` 若需 root 权限操作，建议明确 `nvidia` 的 `sudoers` 配置，避免 SSH 进终端后还需手动输入密码影响脚本。
3. **回滚能力**：设备端改配置前备份原文件（项目已约定），保留 `name_huanghongle3` 这类可回退快照，建议写入 README 的"设备端维护"章节。

---

## 七、文档与同步

1. **README**：已整合一键 `npm run serve` 启动与 GPU 安装命令。
2. **新增**：建议补充一张架构图（浏览器 → serve-all → YOLO/SSH 桥 → rosbridge → 设备节点），以及"公开/发布前检查清单"。
3. **SSH 控制台开发文档**：已有 `data-dashboard/ssh-console-development.md`，与本项目改动保持同步，删除过时引用。

---

## 优先级速查

| 优先级 | 事项 | 位置 |
| --- | --- | --- |
| P0 | 移除/外置设备 SSH 明文凭据 | camera_yolo_server.py、ssh_server.py、Terminal.vue |
| P0 | 发布前密钥扫描 & 尝试公开自检 | git grep / gitleaks |
| P1 | SSH 桥鉴权 + 绑定 127.0.0.1 | ssh_server.py |
| P1 | websockets 版本锁定 | requirements/启动脚本 |
| P1 | 关机等危险快捷命令二次确认 | Terminal.vue |
| P2 | 相机页切走暂停流 / 依赖清理 / 配置外置 | DepthCamera.vue / package.json |
| P2 | 后端异常状态暴露 + 子进程看门狗 | camera_yolo_server.py / serve-all.js |
| P3 | 快捷命令可配置化 / i18n 校验 / 视图拆分 | Terminal.vue / composables |