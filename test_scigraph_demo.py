import asyncio
import json
import httpx
from mcp.client.streamable_http import streamable_http_client
from mcp import ClientSession

async def main():
    server_url = "https://scp.intern-ai.org.cn/api/v1/mcp/37/SciGraph"
    # ⚠️ 注意：这里把 key 换成了你最新申请的那个 sk-2350... 开头的
    api_key = "sk-2350ba23-9e10-425b-b8d6-930b9c2853fe" 

    print("正在连接 SciGraph 服务...")
    try:
        # 1. 新版需要用 httpx 来统一管理 headers
        headers = {"SCP-HUB-API-KEY": api_key}
        async with httpx.AsyncClient(headers=headers) as http_client:
            
            # 2. 函数名变成了 streamable_http_client，并且只返回 read, write
            async with streamable_http_client(url=server_url, http_client=http_client) as (read, write):
                
                # 3. 用 async with 优雅地管理 Session 生命周期
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    print("✅ 连接成功！\n")

                    # 体验 1：查一下化学图谱（ElementKG）里有什么节点类型
                    print("--- 查询 ElementKG 的节点类型 ---")
                    result = await session.call_tool(
                        "get_node_labels",
                        arguments={"kg_name": "ElementKG"}
                    )
                    # 解析返回值
                    if hasattr(result, 'content') and result.content:
                        data = json.loads(result.content[0].text)
                        print(json.dumps(data, indent=2, ensure_ascii=False))

                    # 体验 2：跑一句 Cypher 查个数据看看
                    print("\n--- 随机查询 2 个节点 ---")
                    result2 = await session.call_tool(
                        "query_cypher",
                        arguments={
                            "cypher": "MATCH (n) RETURN n LIMIT 2", 
                            "kg_name": "ElementKG"
                        }
                    )
                    if hasattr(result2, 'content') and result2.content:
                        data2 = json.loads(result2.content[0].text)
                        print(json.dumps(data2, indent=2, ensure_ascii=False))

    except Exception as e:
        print(f"❌ 报错了: {e}")

if __name__ == "__main__":
    asyncio.run(main())