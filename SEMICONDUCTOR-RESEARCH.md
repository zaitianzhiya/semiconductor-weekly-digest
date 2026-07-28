# 全球半导体产业 — 每周深度周报调研文档

## 领域定义

"半导体"在本课题中定义为：**全球半导体产业链**，覆盖 **芯片设计（Fabless/EDA/IP）→ 制造（Foundry/IDM）→ 封测（OSAT/Advanced Packaging）→ 设备与材料 → 存储（DRAM/NAND/HBM）→ AI 芯片（GPU/NPU/ASIC）→ 地缘政治与贸易政策** 全链条。不限定单一国家/地区，跟踪全球半导体产业的技术突破、产能布局、供应链重构和政策博弈。

## 信息来源体系

### Tier 1 — 一手/原创新闻源 (18 sources × 8 生态)

| # | Source | Type | Language | Ecosystem | What it provides |
|---|--------|------|----------|-----------|------------------|
| 1 | EE Times | web_search | EN | intl_trade | 全球电子工程深度报道，芯片设计/制造/测试 |
| 2 | Semiconductor Digest | web_search | EN | intl_trade | 半导体制造技术、设备、材料专题 |
| 3 | IEEE Spectrum (Semiconductors) | web_search | EN | research | IEEE 半导体前沿技术/学术突破 |
| 4 | AnandTech / Tom's Hardware | web_search | EN | consumer | CPU/GPU/存储芯片消费者端评测与制程分析 |
| 5 | TrendForce | web_search | EN | market_data | 全球半导体市场数据、价格走势、产能报告 |
| 6 | IC Insights / TechInsights | web_search | EN | market_data | 芯片市场预测、逆向工程、制程分析 |
| 7 | DIGITIMES | web_search | EN | supply_chain | 台湾半导体供应链一手情报（台积电/联发科/日月光） |
| 8 | Nikkei Asia (Semiconductors) | web_search | EN | asia_pacific | 亚洲芯片产业新闻，日中韩半导体竞争 |
| 9 | The Korea Herald / Korea Times (Tech) | web_search | EN | korea_semi | 韩国半导体：三星/SK海力士存储与代工新闻 |
| 10 | Reuters / Bloomberg (Technology) | web_search | EN | global_finance | 半导体公司财务/并购/股价/资本开支 |
| 11 | 半导体行业观察 (SemiInsights) | web_search | ZH | cn_media | 中国半导体行业最深度公众号/媒体 |
| 12 | 集微网 (JiWei) | web_search | ZH | cn_media | 中国半导体产业链新闻/政策/IPO |
| 13 | 芯思想 (ChipInsight) | web_search | ZH | cn_media | 中国芯片设计/制造/封测深度分析 |
| 14 | 问芯Voice (SemiVoice) | web_search | ZH | cn_media | 半导体产业政策/企业/技术深度报道 |
| 15 | 日经中文网 (半导体) | web_search | ZH | asia_pacific | 日本半导体设备/材料/车用芯片动态 |
| 16 | SEMI | web_search | EN | industry_body | 全球半导体行业协会：标准/展会/产业报告 |
| 17 | SIA (Semiconductor Industry Association) | web_search | EN | industry_body | 美国半导体行业协会：政策/市场数据 |
| 18 | SemiEngineering | web_search | EN | intl_trade | 芯片设计/制造/封装工程深度技术文章 |

### Tier 2 — 二手/聚合/垂直信息源 (14 sources)

| # | Source | Type | Ecosystem | What it provides |
|---|--------|------|-----------|------------------|
| 19 | DRAMeXchange | web_search | memory | 存储芯片现货价格/合约价/市场趋势 |
| 20 | Blocks & Files | web_search | memory | 企业级存储/SSD/NAND Flash/HBM 动态 |
| 21 | SemiAccurate | web_search | insider | 半导体行业内幕/传闻/爆料 |
| 22 | The Next Platform | web_search | ai_chip | AI 芯片/GPU/加速器/HPC 架构 |
| 23 | ServeTheHome | web_search | ai_chip | 服务器芯片/DPU/NPU/数据中心硅 |
| 24 | HPCwire | web_search | ai_chip | 高性能计算芯片/超算/量子计算 |
| 25 | Chiplet Summit / 3D Incites | web_search | packaging | Chiplet/先进封装/异构集成专题 |
| 26 | Yole Group | web_search | market_data | 半导体市场分析/功率半导体/先进封装 |
| 27 | 芯智讯 (ICSmarT) | web_search | cn_aggregator | 中国芯片全产业链快讯/分析 |
| 28 | 第三代半导体产业观察 | web_search | cn_aggregator | GaN/SiC 第三代半导体技术与市场 |
| 29 | 电子工程世界 (EEWorld) | web_search | cn_aggregator | 中国电子工程社区/芯片应用 |
| 30 | Semiconductor Today | web_search | compound_semi | 化合物半导体(GaN/SiC/GaAs)专题 |
| 31 | RISC-V International News | web_search | eda_ip | RISC-V 指令集架构生态新闻 |
| 32 | WikiChip Fuse | web_search | technical | 芯片制程/架构/微架构技术深度分析 |

## 分类体系 (8 Categories)

| Category | Label | Weight | Description |
|----------|-------|--------|-------------|
| 晶圆代工 (`#foundry`) | 制程/产能/扩产 | 20% | 先进制程(2nm/3nm)量产、成熟制程产能扩张、代工价格、Foundry 竞争格局 |
| 存储芯片 (`#memory`) | DRAM/NAND/HBM | 15% | DRAM 合约价/现货价、NAND Flash 供需、HBM3e/HBM4 量产、存储原厂资本开支 |
| 半导体设备 (`#equipment`) | 光刻/刻蚀/检测/材料 | 15% | EUV/DUV 光刻机、刻蚀/沉积/量测设备、硅片/光刻胶/气体/靶材 |
| EDA/IP (`#eda_ip`) | 设计工具/处理器IP | 10% | EDA 工具 AI 化、ARM 授权/RISC-V 生态、Chiplet 互联标准(UCIe/BoW) |
| AI 芯片 (`#ai_chip`) | GPU/NPU/ASIC | 20% | 训练/推理芯片、数据中心 GPU、边缘 AI 芯片、Chiplet+AI 融合 |
| 先进封装 (`#advanced_packaging`) | CoWoS/3D IC/Chiplet | 10% | CoWoS/InFO/EMIB 产能、Hybrid Bonding、玻璃基板、HBM 堆叠 |
| 中国半导体 (`#china_semi`) | 自主化/国产替代 | 5% | 国产DUV/EUV突破、SMIC/华虹/长存/CXMT进展、设备材料国产化 |
| 政策/地缘 (`#policy_geopolitics`) | 出口管制/补贴/制裁 | 5% | 美国BIS出口管制、CHIPS Act拨款、日本/欧盟半导体补贴、中日韩台地缘博弈 |

## 评分维度 (5-dim)

| Dimension | Weight | Description |
|-----------|--------|-------------|
| Technology Significance (技术突破性) | 30% | 制程节点突破、新架构/新材料、性能密度跃升、良率提升 |
| Market Impact (市场影响力) | 25% | 公司市值/股价波动、产业链营收影响、供需格局改变、资本开支规模 |
| Supply Chain Criticality (供应链关键度) | 20% | 产能瓶颈/扩产、设备交期、材料短缺、单一供应商风险 |
| Geopolitical Weight (地缘政治权重) | 15% | 出口管制升级/松绑、多国博弈、技术主权、供应链去风险化 |
| Industry Novelty (行业新颖度) | 10% | 新品首发、技术路线首次公开、全新应用场景、跨行业突破 |

## 中国半导体生态独立维度 (叠加评分)

中国半导体因其"自主化"属性独立评估：
- **国产替代紧迫度**: 被卡脖子环节 × 国产突破的实质性（非 PPT）
- **技术真实度**: 区分量产/流片/研发/传闻，严格验证
- **产业链影响**: 对国内 Fabless/Foundry/Packaging 上下游的拉动

## 关键词体系

### 正向关键词 (置信度提升)

- 技术突破: EUV, High-NA, 2nm, GAA, CFET, HBM4, Hybrid Bonding, Chiplet UCIe, Glass Core, Backside Power
- 产能扩张: Fab investment, Capacity expansion, Capex, Greenfield fab
- 中国自主: 国产DUV, SMIC N+2, YMTC 232L, CXMT DDR5, 国产EDA
- AI 芯片: Blackwell, MI500, Trainium, Inferentia, TPU, Ascend

### 负向关键词 (置信度降低)

- 过度投机: 股价炒作, 传闻, 疑似, 或, may, rumor
- 无关噪音: 加密货币挖矿芯片, 过于小众的学术论文

## 事件条目质量门控

| 条件 | 动作 |
|------|------|
| 标题不含关键词 | PASS |
| 纯股价/财报 → 非产业事件 | PASS |
| 内容长度 < 100 chars | PASS |
| 来源为社交媒体无权威背书 | 降级为 D |
| 传闻/内幕无交叉验证 | 降级为 C |
| 纯日语(日経)/纯韩语 无法解析 | 降级 B→C |

## 技术架构

- **采集**: RealSearchCollector (DDG news for Tier 1, keyword skeleton for Tier 2)
- **AI**: Gemini 2.5 Flash (中文摘要 + 深度分析)
- **渲染**: MarkdownRenderer → `output/weekly/{YYYY}/{YYYY-WNN}.md`
- **部署**: GitHub Actions cron `42 9 * * 1` (Mon 17:42 CST)
- **Watchdog**: 3× Monday check (8:00, 9:30, 13:00 CST)

## Prompt 工程 (Domain-specific)

### 中文摘要风格规则

1. **禁止裸术语**: 每个专业术语/英文缩写在初次出现时至少用一句自然语言解释其实际含义和影响（例如 "High-NA EUV" → "使用0.55数值孔径的极紫外光刻机，可实现2nm以下单次曝光"）
2. **3 秒钩子**: 一句话概括「是什么 + 为什么值得你关注」
3. **双层阅读**:
   - 第一层（粗体标题下第一句）：适合电梯间快速扫读
   - 第二层（后续段落）：包含工艺细节、竞争分析、产业链推导
4. **避免**: "近期发生了一件事"、"值得关注"、"具有重要意义" 等空话；直接给事实+数字
5. **去重**: 同一事件被多个源报道，合并为一条（引用顶级源为主源，其余作为交叉验证计数）

### 半导体专属分析角度

每个事件覆盖至少以下 2 个角度之一：
- **制程/良率视角**: 对摩尔定律延续/先进制程 roadmap 的影响
- **供应链/产能视角**: 是扩产还是瓶颈？对上下游 1-2 个环节的传导逻辑
- **竞争格局视角**: 谁受益谁受损？市场份额如何再分配？
- **地缘博弈视角**: 出口管制变化、技术主权博弈、各国补贴竞赛
- **应用落地视角**: 下游 AI/汽车/消费电子的实际影响
