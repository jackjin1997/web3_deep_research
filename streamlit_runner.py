"""
Streamlit 应用启动器
用于处理异步工作流与 Streamlit 的集成
"""

import asyncio
import streamlit as st
from typing import Dict, Any
import time
import threading
from concurrent.futures import ThreadPoolExecutor

# 导入深度研究模块
try:
    from deep_research import graph

    GRAPH_AVAILABLE = True
except ImportError as e:
    st.error(f"无法导入深度研究模块: {e}")
    GRAPH_AVAILABLE = False


class StreamlitAsyncRunner:
    """处理 Streamlit 中的异步操作"""

    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=2)

    def run_async_in_thread(self, coro, callback=None):
        """在新线程中运行异步函数"""

        def thread_target():
            try:
                # 创建新的事件循环
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(coro)
                loop.close()
                if callback:
                    callback(result)
                return result
            except Exception as e:
                if callback:
                    callback({"error": str(e)})
                return {"error": str(e)}

        future = self.executor.submit(thread_target)
        return future


# 全局异步运行器
async_runner = StreamlitAsyncRunner()


async def run_research_workflow(topic: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """运行真实的深度研究工作流"""
    if not GRAPH_AVAILABLE:
        return {
            "final_report": f"# {topic} - 模拟研究报告\n\n由于深度研究模块未正确加载，这是一个模拟报告。",
            "error": "深度研究模块不可用",
        }

    try:
        # 运行实际的 LangGraph 工作流
        result = await graph.ainvoke({"topic": topic}, config=config)
        return result
    except Exception as e:
        return {"error": str(e), "final_report": f"研究过程中发生错误: {str(e)}"}


def create_research_config(
    writer_model: str, planner_model: str, search_depth: int
) -> Dict[str, Any]:
    """创建研究配置"""
    return {
        "configurable": {
            "thread_id": f"streamlit_{int(time.time())}",
            "max_search_depth": search_depth,
            "writer_model": writer_model,
            "planner_model": planner_model,
            "writer_provider": "openai",  # 默认提供商
            "planner_provider": "anthropic",  # 默认提供商
        }
    }


def format_research_result(result: Dict[str, Any], topic: str) -> tuple:
    """格式化研究结果"""
    if "error" in result:
        return f"❌ 研究失败: {result['error']}", {}

    final_report = result.get("final_report", "未生成报告")

    # 提取元数据
    metadata = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "topic": topic,
        "sections_count": final_report.count("##") if final_report else 0,
        "word_count": len(final_report.split()) if final_report else 0,
    }

    if "sections" in result:
        metadata["sections"] = [s.name for s in result["sections"]]

    if "source_str" in result:
        metadata["sources_used"] = True

    return final_report, metadata


# 测试函数
def test_streamlit_integration():
    """测试 Streamlit 集成"""
    st.write("🧪 测试深度研究模块集成...")

    if GRAPH_AVAILABLE:
        st.success("✅ 深度研究模块加载成功")
        st.write("📊 工作流状态: 可用")
    else:
        st.warning("⚠️ 深度研究模块未正确加载，将使用模拟模式")

    # 显示配置信息
    with st.expander("🔧 配置详情"):
        st.json(
            {
                "graph_available": GRAPH_AVAILABLE,
                "async_runner": "已初始化",
                "thread_pool": "可用",
            }
        )


if __name__ == "__main__":
    # 如果直接运行此文件，显示测试信息
    st.title("🔬 Streamlit 异步运行器测试")
    test_streamlit_integration()
