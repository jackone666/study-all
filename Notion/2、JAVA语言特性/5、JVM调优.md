---
notion-id: 2b6a95f7-5835-80a2-87ea-cbe6610b2f70
---
# JVM调优

> 重要性等级：S=至尊（必考，频率>80%） A=高级（高频，频率50%-80%） B=基础（中频，频率30%-50%） C=普通（低频，<30%）

| 序号 | 重要性 | 题目 + 三段式                                                                                                                                                                                                           |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 1   | S | **JVM 调优第一原则<br>金句**：没数据就调参 = 玄学，先开监控再动手<br>**专业版**：上线前必开 JFR / Async-Profiler / -Xlog:gc*，采集 Allocation Rate、GC 频率、Full GC 时长、Safepoint 时间、锁竞争。<br>**大白话**：先装摄像头看哪里脏了，再决定怎么打扫。拍脑袋调参的都是“键盘风水师”。                    |
| 2   | A | **堆内存黄金三件套**<br>**金句**：Xms = Xmx + 年轻代比例 + Survivor 比例<br>**专业版**：-Xms=-Xmx（避免动态扩缩容抖动）→ -XX:NewRatio=1~2 或 -Xmn → -XX:SurvivorRatio=6~8。<br>**大白话**：客厅大小必须固定，前台占一半，留两个备用小房间，别让实习生到处跑。                              |
| 3   | S | **减少 Full GC 频率 5 大招**<br>**金句**：短命死前台，长命早进里屋，大胖子别乱挤<br>**专业版**：① 调大年轻代 ② 降低晋升阈值（-XX:MaxTenuringThreshold=5）③ 调大 Survivor ④ 大对象直接老年代 ⑤ 禁 System.gc()。<br>**大白话**：实习生多留一会儿、别老往老员工区跑、大胖子走后门、禁止老板手贱喊“大扫除”。            |
| 4   | S | **CPU 100% 定位三板斧**<br>**金句**：top → jstack/Arthas → 看是不是 GC<br>**专业版**：top 找 PID → top -Hp 找 TID → printf "%x\n" TID → jstack 找栈 或直接 Arthas thread -n 3。<br>**大白话**：先看谁在嚎（CPU 高）→ 揪出凶手线程 → 看他到底在干嘛（死循环还是被 GC 卡住了）。  |
| 5   | S | **OOM 解决 6 大实战手段**<br>**金句**：先拍照，再法医，再改代码，最后才扩堆<br>**专业版**：自动 dump → MAT Dominator Tree → 常见 ThreadLocal/连接池/Finalizer/堆外 → 代码加 remove/限流 → 最后扩堆。<br>**大白话**：出事先拍现场 → 用 MAT 当法医 → 改代码堵漏洞 → 实在不行多租房子。               |
| 6   | A | **8G~32G 堆用哪个 GC？64G+ 用哪个？**<br>**金句**：8~32G 上 G1，64G+ 上 ZGC<br>**专业版**：G1（-XX:+UseG1GC）+ -XX:MaxGCPauseMillis=100；64G+ ZGC（-XX:+UseZGC）或 Shenandoah。<br>**大白话**：小公司用 G1 够了，大公司直接上 ZGC，停顿短到你感觉不到。                  |
| 7   | A | **对象分配速率太高怎么优化？**<br>**金句**：先降分配，再优化 GC<br>**专业版**：JFR 看 Allocation Rate > 2GB/s 就危险 → StringBuilder → 避免装箱 → 对象池 → 基本类型数组。<br>**大白话**：别疯狂 new 东西，能复用就复用，能用 int[] 就别用 List<Integer>。                               |
| 8   | B | **元空间 OOM 怎么解决？**<br>**金句**：先限大小，再查动态代理<br>**专业版**：-XX:MaxMetaspaceSize=512m → 常见 CGLIB、ASM、Spring 动态代理、热部署 → 升级框架或关动态类生成。<br>**大白话**：书架（元空间）爆了，先给书架设个上限，再查谁在疯狂印书（动态生成类）。                                          |
| 9   | A | **生产环境必开监控五件套**<br>**金句**：jstat + jstack + jmap + JFR + Arthas<br>**专业版**：jstat -gcutil 1s、jstack 死锁、jmap -histo:live、JFR 持续录制、Arthas dashboard。<br>**大白话**：jstat 看心跳、jstack 看谁卡住、jmap 看谁占地方、JFR 当黑匣子、Arthas 就是外挂。 |
| 10  | B | **JDK 21 虚拟线程对调优的影响**<br>**金句**：线程不再是稀缺资源，调优重点从线程池变成业务逻辑<br>**专业版**：百万虚拟线程，阻塞只挂虚拟线程不卡载体线程，线程池参数意义减弱，重点看业务是否合理阻塞。<br>**大白话**：以前 1 万线程就喘气，现在 100 万跟玩似的，调优不用再抠线程池参数了，专心看代码别傻等。                                        |
| 11  | A | **大厂生产到底用啥 GC？**<br>**金句**：阿里/字节/腾讯 ZGC，美团/京东 G1，小公司默认 G1<br>**专业版**：64G+ 基本 ZGC，32~64G G1 + 调参，8~32G G1 默认就行。<br>**大白话**：有钱任性直接 ZGC，省钱就 G1 凑合，小公司直接默认别折腾。                                                         |
| 12  | B | **怎么快速定位大对象？**<br>**金句**：JFR Allocation Profiling 一键看到<br>**专业版**：开启 JFR → Events → Allocation → TLAB/Outside TLAB → 排序看哪个类分配最多。<br>**大白话**：打开 JFR 看“谁在疯狂生孩子”，一秒找到大对象罪魁祸首。                                         |
| 13  | S | **调优终极三问（面试必被问）**<br>**金句**：你的堆多大？Full GC 多频繁？单次 Full GC 多长时间？<br>**专业版**：回答不出这三个数字，等于没做过生产调优。<br>**大白话**：老板问你：“客厅多大？多久大扫除一次？一次扫多久？”答不上来就尴尬了。                                                                      |
| 14  | A | **为什么说“99% 性能问题靠改代码”**<br>**金句**：参数只是微调，代码才是根<br>**专业版**：对象池、StringBuilder、基本类型数组、ThreadLocal remove、连接池限流，代码优化带来的提升远超参数调整。<br>**大白话**：调优就像减肥，先管住嘴（少 new 对象），再迈开腿（合理 GC），光靠吃药（调参数）没用。                              |
| 15  | A | **调优终极金句（收尾必说）**<br>**金句**：所有 JVM 问题最终都归结为对象分配速率和存活时间<br>**专业版**：短命对象死在年轻代、长命早进老年代、大对象合理分配、类加载不泄漏、分配速率降下来。<br>**大白话**：让该死的赶紧死，该活的长命百岁，大胖子别乱挤，老房子别占着茅坑不拉屎，少生孩子，问题就没了。                                               |

## 1、相关案例
### 1.1 出价系统：new BigDecimal(double) 把 96GB 堆干到跪 [重要性:S]
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
### 1.2 排序系统：G1 换 ZGC，一行参数让尾部时延从 2 秒干到 50ms [重要性:A]
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

```
**效果**：99.99 线 RT 12s → 180ms，CPU 90% → 22%，机器 160 → 48 台，省 4800 万/年。
### 1.3 投放系统：一行 debug 日志把公司差点干黄 [重要性:A]
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

```
**终极解法**（2 分钟上线）：
```java
if (log.isDebugEnabled()) {
    String payload = new String(body, StandardCharsets.UTF_8);
    log.debug("投放回调[{}bytes]: {}", payload.length(),
              payload.length() > 500 ? payload.substring(0, 500) + "..." : payload);
}

```
**效果**：CPU 100% → 18%，分配速率 240GB/s → 60MB/s，投放成功率 91% → 99.99%。
### 1.4 广告系统 GC 调优终极三板斧 [重要性:S]

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
