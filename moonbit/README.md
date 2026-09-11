# MoonBit Core Engine

该模块是 AI 智能数据分析助手的确定性业务计算核心，不是独立 Demo。

- `core/kpi.mbt`：根据 Python 已验证的订单金额计算销售总额、订单数和平均客单价。
- `core/risk.mbt`：根据设备温度、振动、故障次数和状态命中固定风险规则。
- `cmd/main/main.mbt`：只负责 JSON stdin/stdout 协议；Python 通过 `MoonBitService` 调用它。

Python 继续负责文件读取、Pandas 清洗、订单可信金额校验、数据库和 FastAPI 编排。DeepSeek 只解释已经计算完成的结构化指标，不参与 KPI 或风险等级计算。

## 验证

安装 MoonBit CLI 后，在本目录执行：

```powershell
moon test --target native
moon build cmd/main --target native --release
```

开发期可通过 stdin 验证订单 KPI：

```powershell
'{"operation":"order_kpi","verified_order_amounts":[120.0,80.0],"order_count":2}' |
  moon run cmd/main --target native
```

设备风险示例：

```powershell
'{"operation":"equipment_risk","temperature":85.0,"vibration":5.2,"fault_count":1,"status":"运行"}' |
  moon run cmd/main --target native
```

构建完成后，将生成的原生可执行文件路径配置到后端 `MOONBIT_ENGINE_PATH`，并将 `MOONBIT_ENGINE_ENABLED=true`。若可执行文件不可用、超时或输出非法 JSON，后端会自动使用既有 Python 确定性逻辑。
