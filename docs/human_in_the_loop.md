HumanInTheLoopMiddleware ¶
Bases: AgentMiddleware

“人在环路”（Human in the loop）中间件。

state_schema 类属性 实例属性 ¶

state_schema: type[StateT] = cast('type[StateT]', AgentState)
传递给中间件节点的状态模式。

tools 实例属性 ¶

tools: list[BaseTool]
由中间件注册的额外工具。

name 属性 ¶

name: str
中间件实例的名称。

默认为类名，但可以为自定义命名而重写。

before_agent ¶

before_agent(state: StateT, runtime: Runtime[ContextT]) -> dict[str, Any] | None
在代理执行开始前运行的逻辑。

abefore_agent 异步 ¶

abefore_agent(state: StateT, runtime: Runtime[ContextT]) -> dict[str, Any] | None
在代理执行开始前运行的异步逻辑。

before_model ¶

before_model(state: StateT, runtime: Runtime[ContextT]) -> dict[str, Any] | None
在模型被调用前运行的逻辑。

abefore_model 异步 ¶

abefore_model(state: StateT, runtime: Runtime[ContextT]) -> dict[str, Any] | None
在模型被调用前运行的异步逻辑。

aafter_model 异步 ¶

aafter_model(state: StateT, runtime: Runtime[ContextT]) -> dict[str, Any] | None
在模型被调用后运行的异步逻辑。

wrap_model_call ¶

wrap_model_call(
request: ModelRequest, handler: Callable[[ModelRequest], ModelResponse]
) -> ModelCallResult
通过处理器回调拦截和控制模型执行。

处理器回调执行模型请求并返回一个 `ModelResponse`。中间件可以多次调用处理器以实现重试逻辑，跳过调用以进行短路，或修改请求/响应。多个中间件组合时，列表中的第一个为最外层。

参数 描述
request 要执行的模型请求（包括状态和运行时）。
类型： ModelRequest

handler 执行模型请求并返回 `ModelResponse` 的回调函数。调用此函数以执行模型。可以为重试逻辑多次调用。可以跳过调用以进行短路。
类型： Callable[[ModelRequest], ModelResponse]

返回 描述
ModelCallResult ModelCallResult
示例

出错时重试

def wrap_model_call(self, request, handler):
for attempt in range(3):
try:
return handler(request)
except Exception:
if attempt == 2:
raise
重写响应

def wrap_model_call(self, request, handler):
response = handler(request)
ai_msg = response.result[0]
return ModelResponse(
result=[AIMessage(content=f"[{ai_msg.content}]")],
structured_response=response.structured_response,
)
错误时回退

def wrap_model_call(self, request, handler):
try:
return handler(request)
except Exception:
return ModelResponse(result=[AIMessage(content="Service unavailable")])
缓存/短路

def wrap_model_call(self, request, handler):
if cached := get_cache(request):
return cached # Short-circuit with cached result
response = handler(request)
save_cache(request, response)
return response
简单的 AIMessage 返回（自动转换）

def wrap_model_call(self, request, handler):
response = handler(request) # Can return AIMessage directly for simple cases
return AIMessage(content="Simplified response")
awrap_model_call 异步 ¶

awrap_model_call(
request: ModelRequest, handler: Callable[[ModelRequest], Awaitable[ModelResponse]]
) -> ModelCallResult
通过处理器回调拦截和控制异步模型执行。

处理器回调执行模型请求并返回一个 `ModelResponse`。中间件可以多次调用处理器以实现重试逻辑，跳过调用以进行短路，或修改请求/响应。多个中间件组合时，列表中的第一个为最外层。

参数 描述
request 要执行的模型请求（包括状态和运行时）。
类型： ModelRequest

handler 执行模型请求并返回 `ModelResponse` 的异步回调函数。调用此函数以执行模型。可以为重试逻辑多次调用。可以跳过调用以进行短路。
类型： Callable[[ModelRequest], Awaitable[ModelResponse]]

返回 描述
ModelCallResult ModelCallResult
示例

出错时重试

async def awrap_model_call(self, request, handler):
for attempt in range(3):
try:
return await handler(request)
except Exception:
if attempt == 2:
raise
after_agent ¶

after_agent(state: StateT, runtime: Runtime[ContextT]) -> dict[str, Any] | None
在代理执行完成后运行的逻辑。

aafter_agent 异步 ¶

aafter_agent(state: StateT, runtime: Runtime[ContextT]) -> dict[str, Any] | None
在代理执行完成后运行的异步逻辑。

wrap_tool_call ¶

wrap_tool_call(
request: ToolCallRequest,
handler: Callable[[ToolCallRequest], ToolMessage | Command],
) -> ToolMessage | Command
拦截工具执行以进行重试、监控或修改。

多个中间件会自动组合（先定义的为最外层）。除非在 `ToolNode` 上配置了 `handle_tool_errors`，否则异常会传播。

参数 描述
request 工具调用请求，包含调用 `dict`、`BaseTool`、状态和运行时。通过 `request.state` 访问状态，通过 `request.runtime` 访问运行时。
类型： ToolCallRequest

handler 执行工具的可调用对象（可以多次调用）。
类型： Callable[[ToolCallRequest], ToolMessage | Command]

返回 描述
ToolMessage | Command ToolMessage 或 Command (最终结果)。
处理器可调用对象可以为重试逻辑多次调用。对处理器的每次调用都是独立且无状态的。

示例

在执行前修改请求

def wrap_tool_call(self, request, handler):
request.tool_call["args"]["value"] \*= 2
return handler(request)
出错时重试（多次调用处理器）

def wrap_tool_call(self, request, handler):
for attempt in range(3):
try:
result = handler(request)
if is_valid(result):
return result
except Exception:
if attempt == 2:
raise
return result
基于响应的条件性重试

def wrap_tool_call(self, request, handler):
for attempt in range(3):
result = handler(request)
if isinstance(result, ToolMessage) and result.status != "error":
return result
if attempt < 2:
continue
return result
awrap_tool_call 异步 ¶

awrap_tool_call(
request: ToolCallRequest,
handler: Callable[[ToolCallRequest], Awaitable[ToolMessage | Command]],
) -> ToolMessage | Command
通过处理器回调拦截和控制异步工具执行。

处理器回调执行工具调用并返回一个 `ToolMessage` 或 `Command`。中间件可以多次调用处理器以实现重试逻辑，跳过调用以进行短路，或修改请求/响应。多个中间件组合时，列表中的第一个为最外层。

参数 描述
request 工具调用请求，包含调用 `dict`、`BaseTool`、状态和运行时。通过 `request.state` 访问状态，通过 `request.runtime` 访问运行时。
类型： ToolCallRequest

handler 执行工具并返回 `ToolMessage` 或 `Command` 的异步可调用对象。调用此对象以执行工具。可以为重试逻辑多次调用。可以跳过调用以进行短路。
类型： Callable[[ToolCallRequest], Awaitable[ToolMessage | Command]]

返回 描述
ToolMessage | Command ToolMessage 或 Command (最终结果)。
处理器可调用对象可以为重试逻辑多次调用。对处理器的每次调用都是独立且无状态的。

示例

出错时异步重试

async def awrap_tool_call(self, request, handler):
for attempt in range(3):
try:
result = await handler(request)
if is_valid(result):
return result
except Exception:
if attempt == 2:
raise
return result

async def awrap_tool_call(self, request, handler):
if cached := await get_cache_async(request):
return ToolMessage(content=cached, tool_call_id=request.tool_call["id"])
result = await handler(request)
await save_cache_async(request, result)
return result
**init** ¶

**init**(
interrupt_on: dict[str, bool | InterruptOnConfig],
\*,
description_prefix: str = "Tool execution requires approval",
) -> None
初始化“人在环路”中间件。

参数 描述
interrupt_on 工具名称到允许操作的映射。如果某个工具没有条目，则默认自动批准。
True 表示允许所有决策：批准、编辑和拒绝。
False 表示该工具被自动批准。
InterruptOnConfig 表示此工具允许的具体决策。InterruptOnConfig 可以包含一个 `description` 字段（`str` 或 `Callable`）用于自定义中断描述的格式。
类型： dict[str, bool | InterruptOnConfig]

description_prefix 构建操作请求时使用的前缀。这用于提供有关工具调用和所请求操作的上下文。如果工具在其 `InterruptOnConfig` 中有 `description`，则不使用此项。
类型： str默认： 'Tool execution requires approval'

after_model ¶

after_model(state: AgentState, runtime: Runtime) -> dict[str, Any] | None
