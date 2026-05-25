# FolioBrake 自动化优化任务计划

> 日期：2026-05-23
> 模式：自动化执行，无需人工干预
> 任务数：50个

## 上下文压缩设计

为应对长程任务的上下文丢失，每个任务的子Agent应当：
1. 接收完整的目标、文件路径、实现代码
2. 不依赖主会话的上下文
3. 完成后自行验证并报告结果

## 任务批次

### 批次A：Bug修复与代码质量 (Task 1-10)

| # | 任务 | 类型 | 文件 |
|---|------|------|------|
| 1 | 修复 celery-worker 容器健康检查失败 | bug | ops/docker-compose.yml, backend/app/workers/ |
| 2 | 修复 celery-beat 容器不断重启 | bug | ops/docker-compose.yml |
| 3 | 添加数据库连接池配置 | perf | backend/app/db/base.py |
| 4 | 添加 API 响应压缩 (gzip) | perf | backend/app/main.py |
| 5 | 修复前端 API 代理 baseURL 配置 | bug | frontend/src/api/client.ts |
| 6 | 添加全局错误边界 (Error Boundary) | feat | frontend/src/components/ErrorBoundary.tsx |
| 7 | 添加请求重试机制 (axios-retry) | feat | frontend/src/api/client.ts |
| 8 | 修复 Paper 页面 portfolioId 默认值问题 | bug | frontend/src/pages/Paper.tsx |
| 9 | 添加代码分割 (lazy loading pages) | perf | frontend/src/App.tsx |
| 10 | 统一数据库 session 管理 | bug | backend/app/db/base.py |

### 批次B：前端现代化 (Task 11-20)

| # | 任务 | 类型 | 文件 |
|---|------|------|------|
| 11 | 借鉴 Stripe Dashboard 设计首页布局 | feat | frontend/src/pages/Dashboard.tsx |
| 12 | 添加骨架屏 (Skeleton) 组件系统 | feat | frontend/src/components/Skeleton.tsx |
| 13 | 添加 Toast 通知组件 | feat | frontend/src/components/Toast.tsx |
| 14 | 添加 Modal/Dialog 组件 | feat | frontend/src/components/Modal.tsx |
| 15 | 添加 Tooltip 组件 | feat | frontend/src/components/Tooltip.tsx |
| 16 | 添加 Tabs 组件 | feat | frontend/src/components/Tabs.tsx |
| 17 | 添加 Dropdown Menu 组件 | feat | frontend/src/components/Dropdown.tsx |
| 18 | 优化暗色主题色彩系统 (OKLCH) | feat | frontend/src/index.css |
| 19 | 添加微交互动画 (hover/transition) | feat | frontend/src/pages/shared.css |
| 20 | 添加页面过渡动画 | feat | frontend/src/App.tsx |

### 批次C：功能增强 (Task 21-30)

| # | 任务 | 类型 | 文件 |
|---|------|------|------|
| 21 | 添加持仓导入功能 (CSV/手动) | feat | backend/app/api/paper.py |
| 22 | 添加批量 ETF 添加功能 | feat | frontend/src/pages/Universe.tsx |
| 23 | 添加策略对比功能 (A/B test) | feat | frontend/src/pages/Backtest.tsx |
| 24 | 添加定时任务配置页面 | feat | frontend/src/pages/Settings.tsx |
| 25 | 添加数据导出功能 (JSON/CSV/Excel) | feat | backend/app/api/data.py |
| 26 | 添加 Webhook 通知功能 | feat | backend/app/api/webhook.py |
| 27 | 添加组合回测对比功能 | feat | frontend/src/pages/Backtest.tsx |
| 28 | 添加风险评估问卷 | feat | frontend/src/pages/Risk.tsx |
| 29 | 添加策略模板市场 | feat | backend/app/api/strategy.py |
| 30 | 添加邮件报告订阅 | feat | backend/app/workers/ |

### 批次D：性能优化 (Task 31-40)

| # | 任务 | 类型 | 文件 |
|---|------|------|------|
| 31 | 添加 PostgreSQL 查询优化索引 | perf | backend/app/db/migrations/ |
| 32 | 添加 Redis 缓存中间件 | perf | backend/app/core/cache.py |
| 33 | 添加 API 响应分页 | perf | backend/app/api/ |
| 34 | 优化前端包体积 (tree-shaking) | perf | frontend/vite.config.ts |
| 35 | 添加前端 Service Worker 缓存 | perf | frontend/src/sw.ts |
| 36 | 添加数据库查询 N+1 优化 | perf | backend/app/api/ |
| 37 | 添加批量 API 端点 | perf | backend/app/api/batch.py |
| 38 | 优化图表渲染性能 (memo/virtual) | perf | frontend/src/components/Charts.tsx |
| 39 | 添加 CDN 配置支持 | perf | frontend/vite.config.ts |
| 40 | 添加健康检查端点增强 | perf | backend/app/api/health.py |

### 批次E：外部集成与测试 (Task 41-50)

| # | 任务 | 类型 | 文件 |
|---|------|------|------|
| 41 | 集成 TradingView 图表组件 | feat | frontend/src/components/TradingView.tsx |
| 42 | 添加 ETF 持仓数据导入 (东方财富API) | feat | backend/app/data/holdings.py |
| 43 | 添加新闻情感分析集成 | feat | backend/app/nlp/ |
| 44 | 添加端到端测试 (Playwright) | test | tests/e2e/ |
| 45 | 添加 API 集成测试 | test | backend/tests/ |
| 46 | 添加性能基准测试 | test | backend/tests/ |
| 47 | 添加 Docker Compose 健康检查完善 | feat | ops/docker-compose.yml |
| 48 | 添加日志聚合 (ELK 集成) | feat | ops/docker-compose.yml |
| 49 | 添加自动备份脚本 | feat | ops/backup.sh |
| 50 | 添加项目 README 完善 | docs | README.md |

## 执行规则

1. 每个任务独立派发子Agent执行
2. 每完成10个任务提交一次git（分阶段push）
3. 任务完成后进行端到端验证
4. 前端修改后运行 npx tsc --noEmit 验证
5. 后端修改后运行 python3 -m py_compile 验证
