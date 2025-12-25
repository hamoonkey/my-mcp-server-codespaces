from mcp.server.fastmcp import FastMCP

# MCPサーバーのインスタンスを作成
mcp = FastMCP("Weather MCP Server")

@mcp.tool()
def hello_weather(name: str = "World") -> str:
    """シンプルな挨拶を返すツール"""
    return f"Hello, {name}! Welcome to Weather MCP Server!"

@mcp.tool()
def server_info() -> dict:
    """サーバー情報を返すツール"""
    return {
        "name": "Weather MCP Server",
        "version": "1.0.0",
        "description": "天気予報情報を提供するMCPサーバー（開発中）"
    }

if __name__ == "__main__":
    # MCPサーバーを起動
    print("Starting MCP server...")
    mcp.run(transport="streamable-http")