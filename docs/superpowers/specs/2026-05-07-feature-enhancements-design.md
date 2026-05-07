# FolioBrake 功能增强设计文档

> 日期：2026-05-07
> 作者：Sisyphus
> 状态：草稿

## 概述

本文档描述 FolioBrake 项目需要新增的6个核心功能，从用户视角提升系统的实用性和完整性。

## 当前状态

**已有功能：**
- 数据摄取（AKShare/efinance）
- 特征计算（17个特征）
- 策略引擎（综合评分）
- 回测引擎（成本模型、指标）
- 风险叠加（状态机）
- 审计门控（7项检查）
- 纸面交易（模拟交易）
- 前端（8个页面）

**缺失功能：**
- 组合绩效追踪
- 信号历史分析
- 风险告警通知
- 报告导出
- 数据质量监控
- WebSocket实时更新

---

## 功能1：组合绩效仪表盘

### 目标
用户可以在 Dashboard 页面看到纸面组合的完整历史表现。

### 后端设计

**新增端点：** `GET /api/paper/performance/{portfolio_id}`

**请求参数：**
- `portfolio_id` (路径参数): 纸面组合ID
- `start_date` (查询参数, 可选): 开始日期
- `end_date` (查询参数, 可选): 结束日期

**响应格式：**
```json
{
  "portfolio_id": 1,
  "equity_curve": [
    {"date": "2025-01-01", "value": 100000},
    {"date": "2025-01-08", "value": 101200}
  ],
  "benchmark_curve": [
    {"date": "2025-01-01", "value": 100000},
    {"date": "2025-01-08", "value": 100500}
  ],
  "drawdown_curve": [
    {"date": "2025-01-01", "drawdown": 0},
    {"date": "2025-01-08", "drawdown": -0.5}
  ],
  "metrics": {
    "total_return": 0.05,
    "cagr": 0.12,
    "sharpe_ratio": 1.8,
    "max_drawdown": -0.08,
    "volatility": 0.15,
    "win_rate": 0.65
  },
  "monthly_returns": [
    {"month": "2025-01", "return": 0.02},
    {"month": "2025-02", "return": 0.01}
  ]
}
```

**实现逻辑：**
1. 从 `PaperLedger` 获取组合历史交易记录
2. 从 `DailyBar` 获取每日价格数据
3. 计算每日权益曲线
4. 计算基准（510050）权益曲线
5. 计算回撤曲线
6. 计算各项指标

### 前端设计

**Dashboard 页面新增组件：**
- `PortfolioPerformanceCard`: 显示组合绩效概览
- `EquityCurveChart`: 权益曲线图（已有，需更新数据源）
- `DrawdownChart`: 回撤图（已有）
- `MetricsGrid`: 关键指标网格
- `MonthlyReturnsTable`: 月度收益表

**布局：**
```
┌─────────────────────────────────────────┐
│ Dashboard                               │
├─────────────────────────────────────────┤
│ [Risk State] [Portfolio] [Top Signal]   │
├─────────────────────────────────────────┤
│ Portfolio Performance                   │
│ ┌─────────────────────────────────────┐ │
│ │ Equity Curve Chart                  │ │
│ └─────────────────────────────────────┘ │
│ ┌─────────────────────────────────────┐ │
│ │ Drawdown Chart                      │ │
│ └─────────────────────────────────────┘ │
│ [CAGR] [Sharpe] [Max DD] [Vol] [Win]   │
├─────────────────────────────────────────┤
│ Latest Signals                          │
│ ...                                     │
└─────────────────────────────────────────┘
```

---

## 功能2：信号历史追踪

### 目标
用户可以查看过去所有信号及其后续表现。

### 后端设计

**新增端点：** `GET /api/strategy/signal-history`

**请求参数：**
- `limit` (查询参数, 默认50): 返回数量
- `offset` (查询参数, 默认0): 偏移量

**响应格式：**
```json
{
  "signals": [
    {
      "id": 1,
      "date": "2025-01-15",
      "instrument_id": 1,
      "symbol": "510050",
      "score": 85.5,
      "rank": 1,
      "reason": {"breakdown": {...}},
      "subsequent_return_7d": 0.02,
      "subsequent_return_30d": 0.05,
      "is_correct": true
    }
  ],
  "statistics": {
    "total_signals": 100,
    "accuracy_7d": 0.62,
    "accuracy_30d": 0.58,
    "avg_return_7d": 0.015,
    "avg_return_30d": 0.035
  }
}
```

**实现逻辑：**
1. 从 `Signal` 表获取历史信号
2. 对每个信号，计算后续7天和30天收益
3. 统计准确率（信号排名前3的标的后续收益为正）
4. 返回信号列表和统计数据

### 前端设计

**Signals 页面新增标签页：**
- "Current Signals" (现有)
- "Signal History" (新增)

**Signal History 标签页内容：**
- 统计概览卡片（总信号数、7天准确率、30天准确率）
- 信号列表表格（日期、标的、分数、排名、7天收益、30天收益）

---

## 功能3：风险告警通知

### 目标
用户可以收到风险状态变化的实时通知。

### 后端设计

**新增端点：** `GET /api/risk/alerts`

**响应格式：**
```json
{
  "alerts": [
    {
      "id": 1,
      "timestamp": "2025-01-15T10:30:00Z",
      "type": "STATE_CHANGE",
      "severity": "WARNING",
      "title": "Risk State Changed",
      "message": "Risk state changed from NORMAL to CAUTION",
      "read": false
    }
  ],
  "unread_count": 3
}
```

**新增 WebSocket 端点：** `/ws/alerts`

**消息格式：**
```json
{
  "type": "ALERT",
  "data": {
    "id": 2,
    "timestamp": "2025-01-15T11:00:00Z",
    "type": "SIGNAL_GENERATED",
    "severity": "INFO",
    "title": "New Signal",
    "message": "New trading signal generated for 510050"
  }
}
```

**实现逻辑：**
1. 在风险状态变化时创建告警记录
2. 在信号生成时创建告警记录
3. 在审计完成时创建告警记录
4. 通过 WebSocket 实时推送新告警

### 前端设计

**Layout 组件新增：**
- 通知铃铛图标（显示未读数）
- 点击展开告警列表面板

**告警列表面板：**
```
┌─────────────────────────────────────┐
│ Notifications (3)              [✕]  │
├─────────────────────────────────────┤
│ ⚠️ Risk State Changed               │
│    NORMAL → CAUTION                 │
│    2 minutes ago                    │
├─────────────────────────────────────┤
│ 📊 New Signal                       │
│    510050: Score 85.5, Rank #1      │
│    5 minutes ago                    │
├─────────────────────────────────────┤
│ ✅ Audit Complete                   │
│    Grade: GREEN, Score: 82.8        │
│    1 hour ago                       │
└─────────────────────────────────────┘
```

---

## 功能4：报告导出

### 目标
用户可以导出PDF/CSV格式的策略报告。

### 后端设计

**新增端点：**
- `GET /api/reports/backtest/{run_id}/pdf` — 回测报告PDF
- `GET /api/reports/portfolio/{portfolio_id}/csv` — 组合数据CSV
- `GET /api/reports/audit/{run_id}/pdf` — 审计报告PDF

**实现逻辑：**
1. 使用 `matplotlib` 生成图表
2. 使用 `reportlab` 生成PDF（轻量级，无系统依赖）
3. 使用 `csv` 模块生成CSV

### 前端设计

**各页面新增 "Export" 按钮：**
- Backtest 页面：Export PDF 按钮
- Audit 页面：Export PDF 按钮
- Paper 页面：Export CSV 按钮

---

## 功能5：数据质量监控

### 目标
用户可以查看数据源健康状态和数据质量。

### 后端设计

**新增端点：** `GET /api/data/health`

**响应格式：**
```json
{
  "sources": [
    {
      "name": "akshare",
      "status": "healthy",
      "last_sync": "2025-01-15T10:00:00Z",
      "instruments_count": 5,
      "bars_count": 25000
    },
    {
      "name": "efinance",
      "status": "degraded",
      "last_sync": "2025-01-14T08:00:00Z",
      "error": "Rate limited"
    }
  ],
  "data_quality": {
    "total_instruments": 5,
    "instruments_with_gaps": 1,
    "latest_bar_date": "2025-01-15",
    "stale_instruments": []
  }
}
```

### 前端设计

**Universe 页面新增 "Data Health" 卡片：**
- 数据源状态列表
- 数据质量概览
- 缺失数据告警

---

## 功能6：WebSocket 实时更新

### 目标
替代轮询，实时推送价格和风险状态更新。

### 后端设计

**新增 WebSocket 端点：**
- `/ws/prices` — 推送价格更新
- `/ws/risk` — 推送风险状态变化

**技术实现：**
- 使用 FastAPI 内置 WebSocket 支持
- 使用 Redis Pub/Sub 作为消息中间件
- 后台定时任务推送价格更新
- 风险状态变化时立即推送

**消息格式：**
```json
// 价格更新
{
  "type": "PRICE_UPDATE",
  "data": {
    "symbol": "510050",
    "price": 2.35,
    "change": 0.02,
    "change_pct": 0.85,
    "timestamp": "2025-01-15T10:30:00Z"
  }
}

// 风险状态变化
{
  "type": "RISK_STATE_CHANGE",
  "data": {
    "old_state": "NORMAL",
    "new_state": "CAUTION",
    "reason": "Volatility spike detected",
    "timestamp": "2025-01-15T10:30:00Z"
  }
}
```

### 前端设计

**替换轮询为 WebSocket：**
- Dashboard 页面：实时更新风险状态
- Signals 页面：实时推送新信号
- Risk 页面：实时更新风险状态

---

## 实现顺序

| 优先级 | 功能 | 预计工作量 | 依赖 |
|--------|------|-----------|------|
| 1 | 组合绩效仪表盘 | 2天 | 无 |
| 2 | 信号历史追踪 | 1天 | 无 |
| 3 | 风险告警通知 | 1.5天 | WebSocket |
| 4 | 报告导出 | 1天 | 无 |
| 5 | 数据质量监控 | 0.5天 | 无 |
| 6 | WebSocket 实时更新 | 1.5天 | 无 |

**总计：** 约7.5天

---

## 技术约束

- 最小化外部依赖（优先使用现有技术栈）
- PDF导出允许使用 `reportlab`（轻量级PDF生成库，无额外系统依赖）
- 保持现有API风格一致
- 保持现有前端设计风格一致
- 所有新功能需要测试验证

---

## 成功标准

1. **组合绩效仪表盘**：用户可以在Dashboard看到组合历史表现
2. **信号历史追踪**：用户可以查看过去信号的准确率
3. **风险告警通知**：用户可以收到实时风险告警
4. **报告导出**：用户可以导出PDF/CSV报告
5. **数据质量监控**：用户可以查看数据源健康状态
6. **WebSocket实时更新**：用户可以实时看到价格和风险状态变化
