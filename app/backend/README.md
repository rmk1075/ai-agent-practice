# backend

## MCP 서버

대화 메모리 툴(save_memory / list_memory / delete_memory)을 streamable-http 로 제공하는 MCP 서버.
Django ORM 을 재사용하므로 Django 서버와 같은 환경에서 실행한다.

```shell
cd agent
uv run python mcp_server.py
```

- endpoint: `http://localhost:8001/mcp/`
- 동작 확인은 MCP Inspector 사용:

```shell
npx @modelcontextprotocol/inspector
```

Inspector 접속 후 transport 를 `Streamable HTTP`, URL 을 `http://localhost:8001/mcp/` 로 설정하면 툴 목록 조회와 호출을 테스트할 수 있다.

### curl 로 직접 호출

streamable-http 는 JSON-RPC + 세션 핸드셰이크 방식이라 순서가 있다. (URL 은 trailing slash 없이 `/mcp` — `/mcp/` 는 307 리다이렉트된다)

```shell
# 1) initialize — 응답 헤더의 mcp-session-id 를 보관
SID=$(curl -s -D - -o /dev/null -X POST http://localhost:8001/mcp \
  -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"curl","version":"0"}}}' \
  | tr -d '\r' | awk -F': ' 'tolower($1)=="mcp-session-id"{print $2}')

# 2) initialized 알림 (핸드셰이크 완료, 202 응답)
curl -s -X POST http://localhost:8001/mcp \
  -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'

# 3) 툴 목록
curl -s -X POST http://localhost:8001/mcp \
  -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list"}'

# 4) 툴 호출
curl -s -X POST http://localhost:8001/mcp \
  -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SID" \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"list_memory","arguments":{"conversation_id":1}}}'
```

응답은 `data: {...}` 형태의 SSE 라인으로 온다.
