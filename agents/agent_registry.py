class AgentRegistry:
    """Registry for managing available agents"""
    
    def __init__(self):
        self.agents = {}
        self._load_agents()
    
    def _load_agents(self):
        """Load only BRD Generator and Database Chat agents"""
        try:
            # Import agents
            from agents.brd_generator_agent import BRDGeneratorAgent
            from agents.database_chat_agent import DatabaseChatAgent
            
            # Get available configs (only our two agents)
            from config.agent_config import get_available_agents
            available_configs = get_available_agents()
            
            # Register BRD Generator Agent
            if 'brd_generator' in available_configs:
                self.agents['brd_generator'] = BRDGeneratorAgent(available_configs['brd_generator'])
                logger.info("Loaded BRD Generator Agent")
            
            # Register Database Chat Agent
            if 'database_chat' in available_configs:
                self.agents['database_chat'] = DatabaseChatAgent(available_configs['database_chat'])
                logger.info("Loaded Database Chat Agent")
                
            logger.info(f"Successfully loaded {len(self.agents)} specialized agents")
            
        except ImportError as e:
            logger.warning(f"Could not load some agents: {e}")
            # Create minimal fallback agents if imports fail
            self._create_fallback_agents()
        except Exception as e:
            logger.error(f"Error loading agents: {e}")
    
    def _create_fallback_agents(self):
        """Create basic fallback agents if imports fail"""
        from config.agent_config import AGENT_CONFIGS
        
        # Simple fallback implementation
        class FallbackAgent(BaseAgent):
            def run(self):
                st.error(f"Agent {self.config.name} is not properly configured. Please check dependencies.")
            
            def process_input(self, user_input: str) -> str:
                return f"Sorry, {self.config.name} is not available. Please check system configuration."
        
        for agent_id, config in AGENT_CONFIGS.items():
            if agent_id not in self.agents:
                self.agents[agent_id] = FallbackAgent(config)
                logger.info(f"Created fallback for {agent_id}")
    
    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """Get specific agent by ID"""
        return self.agents.get(agent_id)
    
    def get_available_agents(self) -> Dict[str, Dict[str, Any]]:
        """Get information about available agents"""
        return {
            agent_id: {
                'name': agent.config.name,
                'description': agent.config.description,
                'capabilities': [cap.name for cap in agent.config.capabilities],
                'icon': agent.config.icon,
                'color': agent.config.color,
                'status': agent.config.status
            }
            for agent_id, agent in self.agents.items()
        }
    
    def list_agent_ids(self) -> List[str]:
        """Get list of available agent IDs"""
        return list(self.agents.keys())
    
    def register_agent(self, agent_id: str, agent: BaseAgent):
        """Register a new agent"""
        self.agents[agent_id] = agent
        logger.info(f"Registered new agent: {agent_id}")
    
    def unregister_agent(self, agent_id: str):
        """Unregister an agent"""
        if agent_id in self.agents:
            del self.agents[agent_id]
            logger.info(f"Unregistered agent: {agent_id}")"""
Agent Registry and Base Classes
"""

import streamlit as st
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
from config.agent_config import AgentConfig, get_available_agents
from utils.logger import get_logger

logger = get_logger(__name__)

class BaseAgent(ABC):
    """Base class for all agents in the framework"""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.session_key = f"agent_{config.id}_session"
        self.conversation_key = f"agent_{config.id}_conversation"
        self.logger = get_logger(f"Agent.{config.id}")
        self.initialize_session()
    
    def initialize_session(self):
        """Initialize agent-specific session state"""
        if self.session_key not in st.session_state:
            st.session_state[self.session_key] = {
                'initialized': True,
                'last_activity': datetime.now(),
                'context': {},
                'history': []
            }
        
        if self.conversation_key not in st.session_state:
            st.session_state[self.conversation_key] = []
    
    def get_session_data(self) -> Dict[str, Any]:
        """Get agent session data"""
        return st.session_state.get(self.session_key, {})
    
    def update_session_data(self, data: Dict[str, Any]):
        """Update agent session data"""
        session_data = self.get_session_data()
        session_data.update(data)
        session_data['last_activity'] = datetime.now()
        st.session_state[self.session_key] = session_data
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get conversation history for this agent"""
        return st.session_state.get(self.conversation_key, [])
    
    def add_to_conversation(self, role: str, content: str, metadata: Dict[str, Any] = None):
        """Add message to conversation history"""
        message = {
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        }
        
        conversation = self.get_conversation_history()
        conversation.append(message)
        st.session_state[self.conversation_key] = conversation
    
    def render_header(self):
        """Render agent header with status and info"""
        col1, col2, col3 = st.columns([1, 6, 2])
        
        with col1:
            st.markdown(f"<div style='font-size: 3rem;'>{self.config.icon}</div>", 
                       unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"## {self.config.name}")
            st.markdown(f"*{self.config.description}*")
        
        with col3:
            st.markdown(f"""
            <div class="agent-status status-{self.config.status}">
                {self.config.status.upper()}
            </div>
            """, unsafe_allow_html=True)
    
    def render_capabilities(self):
        """Render agent capabilities"""
        with st.expander("Agent Capabilities", expanded=False):
            for capability in self.config.capabilities:
                st.markdown(f"""
                **{capability.name}**
                
                {capability.description}
                
                *Input:* {', '.join(capability.input_types)} | *Output:* {', '.join(capability.output_types)}
                """)
    
    @abstractmethod
    def run(self):
        """Main execution method for the agent"""
        pass
    
    @abstractmethod
    def process_input(self, user_input: str) -> str:
        """Process user input and return response"""
        pass
    
    def render_conversation(self):
        """Render conversation history"""
        conversation = self.get_conversation_history()
        
        if not conversation:
            st.info(f"Start a conversation with {self.config.name}")
            return
        
        # Chat container
        chat_container = st.container()
        
        with chat_container:
            for message in conversation[-20:]:  # Show last 20 messages
                role = message['role']
                content = message['content']
                timestamp = message['timestamp']
                
                if role == 'user':
                    st.markdown(f"""
                    <div class="message message-user">
                        <strong>You:</strong> {content}
                        <br><small>{timestamp}</small>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="message message-agent">
                        <strong>{self.config.name}:</strong> {content}
                        <br><small>{timestamp}</small>
                    </div>
                    """, unsafe_allow_html=True)
    
    def render_chat_input(self):
        """Render chat input interface"""
        with st.form(key=f"{self.config.id}_chat_form", clear_on_submit=True):
            user_input = st.text_area(
                "Message", 
                placeholder=f"Ask {self.config.name} anything...",
                height=100
            )
            
            col1, col2, col3 = st.columns([1, 1, 4])
            
            with col1:
                submitted = st.form_submit_button("Send", type="primary")
            
            with col2:
                clear_chat = st.form_submit_button("Clear Chat")
            
            if submitted and user_input.strip():
                # Add user message to conversation
                self.add_to_conversation('user', user_input)
                
                # Process input and get agent response
                try:
                    with st.spinner(f"{self.config.name} is thinking..."):
                        response = self.process_input(user_input)
                    
                    # Add agent response to conversation
                    self.add_to_conversation('agent', response)
                    
                    # Rerun to show new messages
                    st.rerun()
                    
                except Exception as e:
                    self.logger.error(f"Error processing input: {e}")
                    error_response = f"Sorry, I encountered an error: {str(e)}"
                    self.add_to_conversation('agent', error_response)
                    st.error(error_response)
            
            if clear_chat:
                st.session_state[self.conversation_key] = []
                st.rerun()

class AgentRegistry:
    """Registry for managing available agents"""
    
    def __init__(self):
        self.agents = {}
        self._load_agents()
    
    def _load_agents(self):
        """Load all available agents"""
        try:
            # Import agents dynamically
            from agents.brd_generator_agent import BRDGeneratorAgent
            from agents.database_chat_agent import DatabaseChatAgent
            
            # Register agents
            available_configs = get_available_agents()
            
            if 'brd_generator' in available_configs:
                self.agents['brd_generator'] = BRDGeneratorAgent(available_configs['brd_generator'])
            
            if 'database_chat' in available_configs:
                self.agents['database_chat'] = DatabaseChatAgent(available_configs['database_chat'])
                
            logger.info(f"Loaded {len(self.agents)} agents")
            
        except ImportError as e:
            logger.warning(f"Could not load some agents: {e}")
        except Exception as e:
            logger.error(f"Error loading agents: {e}")
    
    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """Get specific agent by ID"""
        return self.agents.get(agent_id)
    
    def get_available_agents(self) -> Dict[str, Dict[str, Any]]:
        """Get information about available agents"""
        return {
            agent_id: {
                'name': agent.config.name,
                'description': agent.config.description,
                'capabilities': [cap.name for cap in agent.config.capabilities],
                'icon': agent.config.icon,
                'color': agent.config.color,
                'status': agent.config.status
            }
            for agent_id, agent in self.agents.items()
        }
    
    def list_agent_ids(self) -> List[str]:
        """Get list of available agent IDs"""
        return list(self.agents.keys())
    
    def register_agent(self, agent_id: str, agent: BaseAgent):
        """Register a new agent"""
        self.agents[agent_id] = agent
        logger.info(f"Registered new agent: {agent_id}")
    
    def unregister_agent(self, agent_id: str):
        """Unregister an agent"""
        if agent_id in self.agents:
            del self.agents[agent_id]
            logger.info(f"Unregistered agent: {agent_id}")
