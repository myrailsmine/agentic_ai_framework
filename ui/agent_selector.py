"""
Agent Selection Interface
"""

import streamlit as st
from typing import Optional
from agents.agent_registry import AgentRegistry, BaseAgent

def render_agent_selector(agent_registry: AgentRegistry) -> Optional[BaseAgent]:
    """Render agent selection interface"""
    
    st.sidebar.title("Agent Selection")
    
    available_agents = agent_registry.get_available_agents()
    
    if not available_agents:
        st.sidebar.error("No agents available")
        return None
    
    # Agent selection
    agent_options = ["Select an agent..."] + [
        f"{info['icon']} {info['name']}" for agent_id, info in available_agents.items()
    ]
    
    selected_option = st.sidebar.selectbox(
        "Choose your AI Agent:",
        agent_options,
        key="agent_selector"
    )
    
    if selected_option == "Select an agent...":
        return None
    
    # Extract agent_id from selection
    selected_agent_id = None
    for agent_id, info in available_agents.items():
        if f"{info['icon']} {info['name']}" == selected_option:
            selected_agent_id = agent_id
            break
    
    if not selected_agent_id:
        return None
    
    # Get the selected agent
    selected_agent = agent_registry.get_agent(selected_agent_id)
    
    if selected_agent:
        # Display agent info in sidebar
        render_agent_sidebar_info(selected_agent, available_agents[selected_agent_id])
    
    return selected_agent

def render_agent_sidebar_info(agent: BaseAgent, agent_info: dict):
    """Render agent information in sidebar"""
    
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"### {agent_info['icon']} {agent_info['name']}")
    
    # Status indicator
    status_color = {
        'active': 'green',
        'inactive': 'red',
        'loading': 'orange'
    }.get(agent_info['status'], 'gray')
    
    st.sidebar.markdown(f"**Status:** :{status_color}[{agent_info['status'].upper()}]")
    
    # Description
    st.sidebar.markdown(f"*{agent_info['description']}*")
    
    # Capabilities
    st.sidebar.markdown("**Key Capabilities:**")
    for capability in agent_info['capabilities'][:3]:  # Show top 3
        st.sidebar.markdown(f"• {capability}")
    
    if len(agent_info['capabilities']) > 3:
        st.sidebar.markdown(f"• ... and {len(agent_info['capabilities']) - 3} more")
    
    # Session info
    session_data = agent.get_session_data()
    if session_data.get('last_activity'):
        st.sidebar.markdown(f"**Last Activity:** {session_data['last_activity'].strftime('%H:%M:%S')}")
    
    # Quick stats
    conversation_history = agent.get_conversation_history()
    if conversation_history:
        st.sidebar.markdown(f"**Messages:** {len(conversation_history)}")
    
    # Agent controls
    st.sidebar.markdown("---")
    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        if st.button("Reset", key=f"reset_{agent.config.id}"):
            # Clear agent session
            if agent.session_key in st.session_state:
                del st.session_state[agent.session_key]
            if agent.conversation_key in st.session_state:
                del st.session_state[agent.conversation_key]
            st.rerun()
    
    with col2:
        if st.button("Help", key=f"help_{agent.config.id}"):
            st.sidebar.info(f"This is the {agent.config.name}. Use it for {agent.config.description.lower()}")
