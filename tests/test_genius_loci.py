"""
地灵对话接口测试脚本
用于测试流式对话、视觉感知、记忆检索等功能
"""

import asyncio
import httpx
import json


async def test_genius_loci_chat():
    """测试地灵对话接口"""

    # API 配置
    base_url = "http://localhost:8000"
    endpoint = "/api/v1/genius-loci/chat"

    # 测试数据
    test_cases = [
        {
            "name": "首次对话（带图片）",
            "data": {
                "user_id": 1,
                "message": "你好，这里是什么地方？",
                "gps_longitude": 120.15507,
                "gps_latitude": 30.27408,
                "session_id": None,
                "image_url": "https://example.com/cafe.jpg"  # 替换为真实图片URL
            }
        },
        {
            "name": "多轮对话（第2轮）",
            "data": {
                "user_id": 1,
                "message": "今天天气真好，有什么推荐的地方吗？",
                "gps_longitude": 120.15507,
                "gps_latitude": 30.27408,
                "session_id": None,  # 会在第一次对话后获取
                "image_url": None
            }
        }
    ]

    async with httpx.AsyncClient(timeout=60.0) as client:
        session_id = None

        for i, test_case in enumerate(test_cases):
            print(f"\n{'='*60}")
            print(f"测试场景: {test_case['name']}")
            print(f"{'='*60}\n")

            # 如果是第二次对话，使用第一次的 session_id
            if i > 0 and session_id:
                test_case["data"]["session_id"] = session_id

            print(f"请求: {json.dumps(test_case['data'], ensure_ascii=False, indent=2)}\n")

            try:
                # 发送请求
                async with client.stream(
                    "POST",
                    f"{base_url}{endpoint}",
                    json=test_case["data"]
                ) as response:
                    if response.status_code != 200:
                        print(f"❌ 请求失败: {response.status_code}")
                        print(await response.aread())
                        continue

                    print("📡 响应流:\n")

                    # 解析 SSE 流
                    async for line in response.aiter_lines():
                        if not line:
                            continue

                        if line.startswith("data: "):
                            data_str = line[6:]
                            try:
                                data = json.loads(data_str)

                                # 处理不同类型的事件
                                if data.get("type") == "metadata":
                                    session_id = data.get("session_id")
                                    print(f"✅ 建立会话: {session_id}\n")

                                elif data.get("type") == "content":
                                    content = data.get("content", "")
                                    print(content, end="", flush=True)

                                elif data.get("type") == "end":
                                    print("\n\n✅ 对话结束")

                                elif data.get("type") == "error":
                                    print(f"\n❌ 错误: {data.get('message')}")

                            except json.JSONDecodeError:
                                print(f"⚠️  无法解析数据: {data_str}")

            except Exception as e:
                print(f"❌ 异常: {e}")

            # 等待一下再进行下一次对话
            if i < len(test_cases) - 1:
                print("\n⏳ 等待3秒后进行下一轮对话...")
                await asyncio.sleep(3)


async def test_health_check():
    """测试健康检查接口"""
    base_url = "http://localhost:8000"
    endpoint = "/api/v1/genius-loci/health"

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{base_url}{endpoint}")
        print(f"\n健康检查: {response.json()}")


if __name__ == "__main__":
    print("=" * 60)
    print("地灵对话接口测试")
    print("=" * 60)

    # 测试健康检查
    asyncio.run(test_health_check())

    # 测试对话接口
    print("\n开始测试对话接口...")
    asyncio.run(test_genius_loci_chat())

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
