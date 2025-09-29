"""
Unified LLM client supporting both OpenAI and Hugging Face backends.
Provides a consistent interface for LLM calls across the PRISM framework.
"""

import os
from typing import List, Dict, Any, Union
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
import config


def get_llm():
    """
    Factory function to create the appropriate LLM client based on LLM_PROVIDER setting.
    
    Returns:
        LLM client instance (ChatOpenAI or HuggingFaceClient)
    """
    provider = config.LLM_PROVIDER.lower()
    
    if provider == "openai":
        return _create_openai_client()
    elif provider == "hf":
        return _create_hf_client()
    else:
        raise ValueError(f"Unsupported LLM_PROVIDER: {provider}. Use 'openai' or 'hf'")


def _create_openai_client():
    """Create OpenAI client with validation."""
    if not config.OPENAI_API_KEY or config.OPENAI_API_KEY == "your_openai_api_key_here":
        raise ValueError("OPENAI_API_KEY not set or invalid. Please set it in .env file.")
    
    return ChatOpenAI(
        model=config.OPENAI_MODEL,
        temperature=config.TEMPERATURE,
        api_key=config.OPENAI_API_KEY
    )


def _create_hf_client():
    """Create Hugging Face client with validation."""
    if not config.HF_TOKEN:
        raise ValueError("HF_TOKEN not set. Please set it in .env file.")
    
    return HuggingFaceClient(
        model=config.HF_MODEL,
        token=config.HF_TOKEN,
        temperature=config.TEMPERATURE
    )


class HuggingFaceClient:
    """
    Hugging Face Inference API client that mimics the LangChain ChatOpenAI interface.
    """
    
    def __init__(self, model: str, token: str, temperature: float = 0.1):
        self.model = model
        self.token = token
        self.temperature = temperature
        
        try:
            from huggingface_hub import InferenceClient
            self.client = InferenceClient(model=model, token=token)
        except ImportError:
            raise ImportError("huggingface_hub not installed. Run: pip install huggingface_hub")
    
    def invoke(self, messages: Union[List[BaseMessage], str]) -> AIMessage:
        """
        Invoke the HF model with messages, returning an AIMessage to match LangChain interface.
        
        Args:
            messages: List of BaseMessage objects or a string prompt
            
        Returns:
            AIMessage with the model's response
        """
        # Convert messages to text prompt
        if isinstance(messages, str):
            prompt = messages
        elif isinstance(messages, list):
            prompt = self._messages_to_prompt(messages)
        else:
            prompt = str(messages)
        
        try:
            # Use chat completion if available, otherwise text generation
            if hasattr(self.client, 'chat_completion'):
                messages_dict = [{"role": "user", "content": prompt}]
                response = self.client.chat_completion(
                    messages=messages_dict,
                    temperature=self.temperature,
                    max_tokens=512
                )
                content = response.choices[0].message.content
            else:
                # Fallback to text generation
                response = self.client.text_generation(
                    prompt,
                    temperature=self.temperature,
                    max_new_tokens=512,
                    return_full_text=False
                )
                content = response if isinstance(response, str) else str(response)
            
            return AIMessage(content=content.strip())
            
        except Exception as e:
            # Return error message as AIMessage to maintain interface consistency
            return AIMessage(content=f"HuggingFace API Error: {str(e)}")
    
    def _messages_to_prompt(self, messages: List[BaseMessage]) -> str:
        """Convert list of messages to a single prompt string."""
        prompt_parts = []
        
        for message in messages:
            if isinstance(message, HumanMessage):
                prompt_parts.append(f"Human: {message.content}")
            elif isinstance(message, AIMessage):
                prompt_parts.append(f"Assistant: {message.content}")
            else:
                prompt_parts.append(message.content)
        
        return "\n".join(prompt_parts)


# Convenience function for backward compatibility
def llm_chat(messages: Union[List[BaseMessage], str], **kwargs) -> AIMessage:
    """
    Unified interface for LLM chat completion.
    
    Args:
        messages: List of BaseMessage objects or string prompt
        **kwargs: Additional parameters (currently unused but for future extension)
        
    Returns:
        AIMessage with the model's response
    """
    llm = get_llm()
    return llm.invoke(messages)