import streamlit as st
import asyncio
import time
from typing import Dict, Any
import json

# 导入深度研究模块和异步运行器
from streamlit_runner import (
    run_research_workflow,
    create_research_config,
    format_research_result,
    async_runner,
    GRAPH_AVAILABLE,
)

# 页面配置
st.set_page_config(
    page_title="🔬 Deep Research Assistant",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 自定义CSS
st.markdown(
    """
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .status-box {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .status-running {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
    }
    .status-complete {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
    }
    .status-error {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
    }
</style>
""",
    unsafe_allow_html=True,
)

# 主标题
st.markdown(
    '<h1 class="main-header">🔬 Deep Research Assistant</h1>', unsafe_allow_html=True
)
st.markdown("---")

# 初始化会话状态
if "messages" not in st.session_state:
    st.session_state.messages = []
if "research_history" not in st.session_state:
    st.session_state.research_history = []
if "current_status" not in st.session_state:
    st.session_state.current_status = "等待输入"

# 侧边栏配置
with st.sidebar:
    st.header("⚙️ 配置选项")

    # 研究配置
    st.subheader("🔧 研究参数")
    max_sections = st.slider("最大章节数", min_value=3, max_value=10, value=5)
    search_depth = st.slider("搜索深度", min_value=1, max_value=5, value=2)

    # 模型配置
    st.subheader("🤖 模型配置")
    writer_model = st.selectbox(
        "写作模型",
        ["gpt-4", "gpt-3.5-turbo", "claude-3-sonnet", "claude-3-haiku"],
        index=0,
    )

    planner_model = st.selectbox(
        "规划模型", ["gpt-4", "claude-3-sonnet", "claude-3-haiku"], index=1
    )

    # 显示当前状态
    st.subheader("📊 当前状态")
    status_container = st.container()
    with status_container:
        if st.session_state.current_status == "等待输入":
            st.markdown(
                '<div class="status-box">🟡 等待研究主题输入</div>',
                unsafe_allow_html=True,
            )
        elif "进行中" in st.session_state.current_status:
            st.markdown(
                f'<div class="status-box status-running">🔄 {st.session_state.current_status}</div>',
                unsafe_allow_html=True,
            )
        elif "完成" in st.session_state.current_status:
            st.markdown(
                f'<div class="status-box status-complete">✅ {st.session_state.current_status}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="status-box status-error">❌ {st.session_state.current_status}</div>',
                unsafe_allow_html=True,
            )

    # 研究历史
    st.subheader("📚 研究历史")
    if st.session_state.research_history:
        for i, topic in enumerate(st.session_state.research_history[-5:], 1):
            st.write(f"{i}. {topic[:30]}...")
    else:
        st.write("暂无研究历史")

    # 清除历史按钮
    if st.button("🗑️ 清除历史", type="secondary"):
        st.session_state.messages = []
        st.session_state.research_history = []
        st.rerun()

# 主界面布局
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("💬 研究对话")

    # 聊天容器
    chat_container = st.container()

    with chat_container:
        # 显示聊天历史
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                if message["role"] == "assistant":
                    # 格式化助手回复
                    st.markdown(message["content"])
                    if "metadata" in message:
                        with st.expander("📋 详细信息"):
                            st.json(message["metadata"])
                else:
                    st.markdown(message["content"])

with col2:
    st.subheader("📈 研究进度")
    progress_container = st.container()

    # 工作流可视化占位符
    workflow_placeholder = st.empty()

# 输入区域
st.markdown("---")
input_container = st.container()

with input_container:
    col_input, col_button = st.columns([4, 1])

    with col_input:
        user_input = st.text_input(
            "请输入您要研究的主题:",
            placeholder="例如: Web3的发展趋势和挑战",
            key="topic_input",
            label_visibility="collapsed",
        )

    with col_button:
        submit_button = st.button(
            "🚀 开始研究", type="primary", use_container_width=True
        )


# 处理用户输入
def handle_research_request(
    topic: str, writer_model: str, planner_model: str, search_depth: int
):
    """处理研究请求"""
    # 创建配置
    config = create_research_config(writer_model, planner_model, search_depth)

    # 运行异步工作流
    future = async_runner.run_async_in_thread(run_research_workflow(topic, config))

    return future


def update_progress(step: str, progress: float):
    """更新进度显示"""
    with progress_container:
        st.progress(progress)
        st.write(f"🔄 {step}")


# 当用户提交时
if submit_button and user_input:
    # 添加用户消息
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.session_state.research_history.append(user_input)

    # 更新状态
    st.session_state.current_status = "研究进行中..."

    # 显示用户消息
    with chat_container:
        with st.chat_message("user"):
            st.markdown(user_input)

    # 显示助手思考过程
    with chat_container:
        with st.chat_message("assistant"):
            thinking_placeholder = st.empty()
            thinking_placeholder.markdown("🤔 正在分析您的研究主题...")

            # 进度条
            progress_bar = st.progress(0)
            status_text = st.empty()

            try:
                # 模拟进度更新
                steps = [
                    ("分析研究主题", 0.1),
                    ("生成研究计划", 0.2),
                    ("搜索相关信息", 0.4),
                    ("撰写研究章节", 0.7),
                    ("整合最终报告", 0.9),
                    ("完成研究", 1.0),
                ]

                for step, progress in steps:
                    status_text.markdown(f"🔄 {step}...")
                    progress_bar.progress(progress)
                    time.sleep(1)  # 模拟处理时间

                    # 实际运行研究
                thinking_placeholder.markdown("✨ 正在启动深度研究工作流...")

                # 运行真实的研究工作流
                if GRAPH_AVAILABLE:
                    future = handle_research_request(
                        user_input, writer_model, planner_model, search_depth
                    )

                    # 等待结果（模拟轮询）
                    max_wait_time = 300  # 最大等待5分钟
                    start_time = time.time()

                    while (
                        not future.done() and (time.time() - start_time) < max_wait_time
                    ):
                        elapsed = time.time() - start_time
                        progress = min(0.9, elapsed / 60)  # 基于时间的进度估算
                        progress_bar.progress(progress)
                        status_text.markdown(f"🔄 研究进行中... ({int(elapsed)}秒)")
                        time.sleep(2)

                    if future.done():
                        result = future.result()
                        final_report, metadata = format_research_result(
                            result, user_input
                        )
                    else:
                        # 超时处理
                        final_report = f"⏰ 研究超时。主题: {user_input}\n\n研究过程可能需要更长时间，请稍后重试。"
                        metadata = {"error": "timeout", "topic": user_input}
                else:
                    # 模拟模式
                    final_report = f"""# {user_input} - 深度研究报告 (模拟模式)

## 📋 执行摘要
基于您提供的研究主题"{user_input}"，我们进行了模拟的深度分析。

⚠️ **注意**: 当前运行在模拟模式下，因为深度研究模块未正确加载。

## 🔍 核心发现
1. **主要趋势**: 该领域正在经历快速发展
2. **关键挑战**: 存在多个技术和市场挑战  
3. **机遇分析**: 识别出重要的发展机遇

## 📊 详细分析
### 技术层面
- 技术创新持续推进
- 基础设施不断完善
- 标准化进程加速

### 市场层面
- 市场接受度逐步提升
- 监管环境日趋明确
- 投资活动保持活跃

## 🎯 结论与建议
基于以上分析，我们建议：
1. 关注技术发展动态
2. 跟踪监管政策变化
3. 把握市场机遇窗口

*本报告基于模拟数据生成，仅用于演示目的。*"""
                    metadata = {
                        "sections": ["执行摘要", "核心发现", "详细分析", "结论与建议"],
                        "search_queries": ["模拟查询1", "模拟查询2", "模拟查询3"],
                        "mode": "simulation",
                    }

                # 清除进度显示
                progress_bar.empty()
                status_text.empty()
                thinking_placeholder.empty()

                # 显示结果
                st.markdown(final_report)

                # 添加元数据
                with st.expander("📋 研究详情"):
                    col_meta1, col_meta2 = st.columns(2)
                    with col_meta1:
                        st.write("**研究信息:**")
                        st.write(f"• 主题: {metadata.get('topic', user_input)}")
                        st.write(
                            f"• 时间: {metadata.get('timestamp', time.strftime('%Y-%m-%d %H:%M:%S'))}"
                        )
                        if "sections_count" in metadata:
                            st.write(f"• 章节数: {metadata['sections_count']}")
                        if "word_count" in metadata:
                            st.write(f"• 字数: {metadata['word_count']}")
                        if "mode" in metadata:
                            st.write(f"• 模式: {metadata['mode']}")

                    with col_meta2:
                        st.write("**技术详情:**")
                        if "sections" in metadata:
                            st.write("**研究章节:**")
                            for section in metadata["sections"]:
                                st.write(f"• {section}")
                        if "search_queries" in metadata:
                            st.write("**搜索关键词:**")
                            for query in metadata["search_queries"]:
                                st.write(f"• {query}")
                        if "sources_used" in metadata:
                            st.write("• 使用了外部数据源")

                # 保存到消息历史
                st.session_state.messages.append(
                    {"role": "assistant", "content": final_report, "metadata": metadata}
                )

                # 更新状态
                st.session_state.current_status = "研究完成"

            except Exception as e:
                st.error(f"❌ 研究过程中发生错误: {str(e)}")
                st.session_state.current_status = f"错误: {str(e)}"

    # 清空输入框
    st.session_state.topic_input = ""
    st.rerun()

# 页脚
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #666; padding: 1rem;">
        🔬 Deep Research Assistant | Powered by LangGraph & Streamlit
    </div>
    """,
    unsafe_allow_html=True,
)

# 实时状态更新（可选）
if st.session_state.current_status != "等待输入":
    time.sleep(0.1)  # 避免过于频繁的重新运行
