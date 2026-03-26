from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class LocalMCPClient:
    def __init__(self):
        self.server_params = StdioServerParameters(
            command="uv",
            args=["run", "mcp_server/server.py"],
        )
        self.session = None
        self.exit_stack = None

    async def connect(self):
        """Connects to the local MCP server via stdio."""
        print("Connecting to Local-Intel MCP Server... 🔌")
        self.exit_stack = AsyncExitStack()

        read_stream, write_stream = await self.exit_stack.enter_async_context(
            stdio_client(self.server_params)
        )

        self.session = await self.exit_stack.enter_async_context(
            ClientSession(read_stream, write_stream)
        )
        await self.session.initialize()

        response = await self.session.list_tools()
        return response.tools

    def to_generic_tool_defs(self, mcp_tools):
        """Converts MCP tool definitions into provider-neutral tool schemas."""
        generic_tools = []
        for tool in mcp_tools:
            generic_tools.append({
                "type": "function",
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.inputSchema,
            })
        return generic_tools

    async def call_tool(self, name, arguments):
        """Executes a tool on the MCP server and returns the result."""
        result = await self.session.call_tool(name, arguments)
        return result.content[0].text

    async def disconnect(self):
        """Gracefully shuts down the server connection."""
        if self.exit_stack:
            await self.exit_stack.aclose()
            print("MCP Server disconnected.")
