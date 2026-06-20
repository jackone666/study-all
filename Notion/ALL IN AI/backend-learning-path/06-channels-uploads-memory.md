# 上传、记忆与 IM 频道

## 上传入口

文件：`backend/app/gateway/routers/uploads.py`

主调用链：

```text
POST /api/threads/{thread_id}/uploads
  -> upload_files(thread_id, files, request)
      -> get upload limits
      -> validate file count / size
      -> resolve thread user-data uploads directory
      -> _write_upload_file_with_limits(...)
      -> optionally auto convert documents
      -> return UploadResponse
```

关键方法：

- `_get_upload_limits()`
- `_write_upload_file_with_limits()`
- `_cleanup_uploaded_paths()`
- `_auto_convert_documents_enabled()`
- `list_uploaded_files()`
- `delete_uploaded_file()`

## 上传进入 Agent 上下文

关键中间件：

- `ThreadDataMiddleware`
- `UploadsMiddleware`

大致链路：

```text
upload_files()
  -> 文件落到 thread uploads 目录
下一轮 run
  -> ThreadDataMiddleware 创建/恢复 thread_data
  -> UploadsMiddleware 扫描新增上传文件
  -> 写入 ThreadState.uploaded_files
  -> 注入 HumanMessage 附加上下文
```

阅读建议：

1. 先读 `uploads.py` 看 HTTP 如何接收文件。
2. 再读 `deerflow/uploads/manager.py` 看文件元数据和路径。
3. 最后读 `UploadsMiddleware` 看如何进入对话上下文。

## 长期记忆

目录：`backend/packages/harness/deerflow/agents/memory/`

核心文件：

- `storage.py`
- `queue.py`
- `updater.py`
- `middleware.py`
- `prompt.py`
- `message_processing.py`

高层链路：

```text
Agent 完成一轮
  -> MemoryMiddleware.after_agent
  -> filter user + final AI responses
  -> enqueue memory update
  -> MemoryQueue worker
  -> MemoryUpdater.aupdate_memory()
  -> storage writes facts/context
```

为什么异步入队：

- 记忆抽取通常需要模型调用或文件 IO。
- 不应阻塞用户主对话的最终响应。
- 摘要中间件压缩前会调用 `memory_flush_hook`，避免即将被裁剪的上下文尚未入库。

## IM 频道入口

目录：`backend/app/channels/`

核心文件：

- `base.py`
- `manager.py`
- `message_bus.py`
- `service.py`
- `feishu.py`
- `dingtalk.py`
- `slack.py`
- `telegram.py`
- `wechat.py`
- `wecom.py`

## ChannelManager 主链路

文件：`backend/app/channels/manager.py`

启动链：

```text
Gateway lifespan()
  -> start_channel_service(startup_config)
  -> ChannelManager.start()
  -> create dispatch loop task
```

消息处理链：

```text
Channel provider receives inbound message
  -> MessageBus inbound queue
  -> ChannelManager._dispatch_loop()
  -> _handle_message(msg)
      -> command? _handle_command()
      -> chat? _handle_chat()
          -> _create_thread()
          -> _resolve_run_params()
          -> _ingest_inbound_files()
          -> _handle_streaming_chat() or runs.wait
          -> outbound send / send_file
```

## IM 复用 Gateway API

`ChannelManager` 并不绕过 Gateway 直接调用 agent 内部函数，而是复用 LangGraph 兼容 API：

```text
ChannelManager
  -> LangGraph SDK client
  -> Gateway /api/threads
  -> Gateway /api/threads/{id}/runs/stream or runs/wait
```

好处：

- HTTP 前端和 IM 入口共享 run 生命周期。
- 权限、thread metadata、run event、SSE 语义更一致。
- 自定义 agent、模型选择、上传文件等功能不用重复实现。

## IM 中的附件

相关方法：

- `_resolve_attachments()`
- `_prepare_artifact_delivery()`
- `_ingest_inbound_files()`
- `_format_uploaded_files_block()`

链路：

```text
InboundMessage.attachments
  -> channel-specific file reader
  -> _ingest_inbound_files(thread_id, msg)
  -> uploads manager / Gateway upload-compatible metadata
  -> run context includes uploaded file block
```

## 频道命令

`_handle_command()` 处理非聊天类指令，例如：

- 查询状态
- 切换配置
- 拉取 Gateway 信息

建议读法：

1. 先读 `ChannelManager._handle_message()`。
2. 再读 `_handle_chat()`。
3. 最后读 `_handle_streaming_chat()` 和 `_handle_command()`。

