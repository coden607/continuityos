from continuityos.memory import MemoryRecord, InMemoryMemoryAdapter
from continuityos.mcp import MCPServer, MCPRegistry
from continuityos.observability import InMemoryTracer
from continuityos.providers import ProviderRequest, ProviderResult


def test_memory_adapter_round_trip():
    mem = InMemoryMemoryAdapter()
    mem.put(MemoryRecord(namespace='user', key='tone', value='concise'))
    assert mem.get('user', 'tone').value == 'concise'


def test_mcp_registry_tracks_servers():
    registry = MCPRegistry()
    registry.register(MCPServer(name='courtlistener', url='https://mcp.courtlistener.com/', transport='streamable_http'))
    assert registry.get('courtlistener').url.startswith('https://')


def test_tracer_records_spans():
    tracer = InMemoryTracer()
    with tracer.span('route', {'task': 'text'}):
        pass
    assert tracer.spans[0]['name'] == 'route'
    assert tracer.spans[0]['status'] == 'ok'


def test_provider_types_are_serializable():
    req = ProviderRequest(model='local', messages=[{'role': 'user', 'content': 'hi'}])
    result = ProviderResult(text='hello', model='local', input_tokens=1, output_tokens=1)
    assert req.model_dump()['model'] == 'local'
    assert result.total_tokens == 2
