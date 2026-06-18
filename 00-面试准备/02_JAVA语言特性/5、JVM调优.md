---
notion-id: 2b6a95f7-5835-80a2-87ea-cbe6610b2f70

---

# 1、相关案例
## 1.1 出价系统：new BigDecimal(double) 把 96GB 堆干到跪 [重要性:S]
**金句**：**double 是广告系统的核弹，一行代码干掉 64 核机器**
**现象**：Full GC 每 3~8 秒一次，99.99 线 RT 从 80ms → 9 秒，曝光暴跌
**定位思路 + 工具 + 日志（10 分钟搞定）**：

| 步骤 | Arthas 命令 & 操作 | 关键日志/现象 | 发现 |
| --- | --- | --- | --- |
| 1. 先看 GC 频率 | `dashboard`（实时刷新，按 Enter） | YGC 列每秒增长几十次，FGC 每几秒增长一次，老年代占用快速上涨 | 分配速率爆炸，肯定有疯狂创建对象的代码 |
| 2. 采样对象分配热点 | `profiler start --event alloc --duration 120 --live`（采样 120 秒存活对象） | 采样进行中，无明显额外开销 | 开始收集分配数据 |
| 3. 生成并查看分配火焰图 | `profiler stop --format flamegraph`（生成 HTML 文件）<br>下载文件到本地浏览器打开 | 火焰图中 99%+ 的分配样本集中在 `java.math.BigDecimal.<init>(double)` 调用栈 | 罪魁祸首是 new BigDecimal(double) |
| 4. 定位具体代码位置 | 根据火焰图调用栈找到嫌疑类（如 com.example.service.PriceService）<br>`jad com.example.service.PriceService`（反编译查看源码）<br>或 `trace java.math.BigDecimal '<init>(double)' -n 1000`（实时追踪调用） | 反编译源码中看到多处 `new BigDecimal(bidPrice.doubleValue())` 或类似代码<br>trace 显示每秒成千上万次调用 | 确认 17 处（或更多）使用了 new BigDecimal(double) 的错误用法 |

**终极解法**：全局改成 new BigDecimal("0.1") 或 String 构造 + 常量缓存
**效果**：分配速率 7.8GB/s → 120MB/s，Full GC 消失，RT 回到 75ms。
## 1.2 排序系统：G1 换 ZGC，一行参数让尾部时延从 2 秒干到 50ms [重要性:A]
**金句**：**96GB 大堆下，G1 是笑话，ZGC 是救世主**
**现象**：99.99 线 RT 12 秒，CPU 90%，机器 160 台都救不回来
**定位思路 + 工具 + 日志（8 分钟搞定）**：

| 步骤 | 工具命令 | 关键日志/现象 | 发现 |
| --- | --- | --- | --- |
| 1. GC 日志 | -Xlog:gc*:file=gc.log:time,upid | [GC pause (G1 Evacuation Pause) 2.4s] 每 5 分钟一次 | G1 停顿完全失控 |
| 2. jstat 看老年代 | jstat -gc 1s | OG（老年代）占 92GB，一直在 90%+ | 大堆下 G1 退化 |
| 3. JFR 看 Safepoint | JFR → Safepoint | Safepoint 时间占 60% | G1 在大堆下彻底串行化 |
| 4. 压测对比 | 相同 QPS 下换 ZGC | 最长停顿 8ms | 确认 G1 是瓶颈 |

**终极解法**：只改一行参数
```bash
-XX:+UseZGC      # 就这一行，JDK 21 生产可用

**效果**：99.99 线 RT 12s → 180ms，CPU 90% → 22%，机器 160 → 48 台，省 4800 万/年。
## 1.3 投放系统：一行 debug 日志把公司差点干黄 [重要性:A]
**金句**：**广告系统最怕的不是 GC，是 debug 打印原始报文**
**现象**：CPU 100%（JVM 占 95%），ZGC 虽然不停顿但 CPU 被干到爆
**定位思路 + 工具 + 日志（5 分钟搞定）**：
| 步骤 | 工具命令 | 关键日志/现象 | 发现 |
| --- | --- | --- | --- |
| 1. top 看 CPU | top → top -Hp pid | 30+ 个线程全是 AsyncLogger | 日志线程爆炸 |
| 2. Arthas 大杀器 | arthas → thread -n 10 | 全是 AsyncLogger + 堆栈在 Disruptor | 异步日志堵死 |
| 3. tail 日志 | tail -f app.log | 每秒 8 万行“投放回调原始报文：{3KB}” | 找到毒瘤代码 |
| 4. JFR 验证 | Allocation Rate 240GB/s | 99% 是 byte[] → String 转换 | 确认是日志导致 |
**毒瘤代码**：
```java
log.debug("投放回调原始报文：{}", new String(body));  // 3KB × 8万 = 240GB/s 分配
**终极解法**（2 分钟上线）：
```java
if (log.isDebugEnabled()) {
    String payload = new String(body, StandardCharsets.UTF_8);
    log.debug("投放回调[{}bytes]: {}", payload.length(),
              payload.length() > 500 ? payload.substring(0, 500) + "..." : payload);
}
```

**效果**：CPU 100% → 18%，分配速率 240GB/s → 60MB/s，投放成功率 91% → 99.99%。
## 1.4 广告系统 GC 调优终极三板斧 [重要性:S]
| 场景 | 工具组合 | 一句口诀 |
| --- | --- | --- |
| 分配速率爆炸 | JFR Allocation Profiling | “先看谁在疯狂生孩子” |
| GC 停顿失控 | GC 日志 + jstat + JFR Safepoint | “G1 大堆必死，ZGC 一行救命” |
| CPU 被日志打爆 | top + Arthas thread + tail log | “广告系统 debug 打印报文 = 公司级事故” |
**面试终极金句（直接甩）**：
“广告系统 GC 调优只有三件事：
1. 出价扣费用 String，绝不用 double
2. 64GB 以上堆直接上 ZGC，一行参数省几千万
3. debug 日志敢打印原始报文，凌晨起来跪着修 Bug”
背完这套，2025 年广告系统任何 GC 调优问题直接乱杀！
