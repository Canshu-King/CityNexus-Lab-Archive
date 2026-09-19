# OPPO 真机预检查，可以与 V19.2.5 热修并行

这一步只验证“手机链路”，不做正式外场 Shadow Journey。

## 电脑端
后端：
`cd /d D:\moodle\CityNexus\backend`
`uv run uvicorn app.main:app --host 0.0.0.0 --port 8000`

前端开发服务器：
`cd /d D:\moodle\CityNexus\frontend`
`npm run dev -- --host 0.0.0.0 --port 5173`

前端所有 API 使用相对路径 `/api/v1`，Vite 会代理到本机 127.0.0.1:8000。

## 手机端预检查目标
必须通过 HTTPS 安全上下文验证真实定位。局域网 HTTP 只可做页面连通性检查，
不要把它当成 PWA/GPS 正式通过。

检查：
1. 首页/Hub/Live/Copilot 正常打开
2. GPS 允许：产生真实 location observation
3. GPS 拒绝：明确错误，不伪装成已定位
4. 临时断网后恢复
5. SSE/Copilot 连接恢复且不重复事件
6. 后端重启后页面能恢复或明确提示
7. Recovery warning 的 Acknowledge 不消除 HARD 问题
8. stale plan 仍不能 start

禁止：
- 真实付款
- 依赖 CityNexus 做安全关键无障碍决定
- 在 V19.2.5 热修验收前做复杂多 C4 外场路线

记录：
手机型号、Android/浏览器版本、网络、GPS accuracy、run id、错误截图、后端日志时间段。
