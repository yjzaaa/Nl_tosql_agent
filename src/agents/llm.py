"""LLM 提供商 - 使用依赖注入"""

from langchain.chat_models import init_chat_model
from langchain_openai import ChatOpenAI
from langchain_core.callbacks import BaseCallbackHandler

from src.config.settings import get_config
from src.core.interfaces import ILLMProvider

import os
from typing import List, Optional, Dict


class OpenAILLMProvider(ILLMProvider):
    """OpenAI LLM 提供商实现"""

    def __init__(self, model_name: str = None, api_key: str = None,
                 base_url: str = None, temperature: float = 0.1, max_tokens: int = 4096,
                 callbacks: list = None, model_kwargs: dict = None):
        self._model_name = model_name
        self._api_key = api_key
        self._base_url = base_url
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._callbacks = callbacks or []
        self._model_kwargs = model_kwargs or {}
        self._llm = None
        self._initialize_llm()

    def _initialize_llm(self):
        """初始化 LLM 实例"""
        if self._model_name and self._api_key:
            self._llm = ChatOpenAI(
                model=self._model_name,
                api_key=self._api_key,
                base_url=self._base_url if self._base_url else None,
                temperature=self._temperature,
                max_tokens=self._max_tokens,
                callbacks=self._callbacks,
                model_kwargs=self._model_kwargs,
            )

    def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate text from LLM
        
        Args:
            prompt: Input prompt
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
            
        Returns:
            Generated text
        """
        from langchain.schema import HumanMessage
        response = self._llm.invoke([HumanMessage(content=prompt)], **kwargs)
        return response.content

    def generate_chat(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> str:
        """
        Generate chat completion
        
        Args:
            messages: List of message dictionaries (role, content)
            **kwargs: Additional parameters
            
        Returns:
            Generated response
        """
        from langchain.schema import HumanMessage, SystemMessage, AIMessage
        
        lc_messages = []
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content")
            if role == "system":
                lc_messages.append(SystemMessage(content=content))
            elif role == "user":
                lc_messages.append(HumanMessage(content=content))
            elif role == "assistant":
                lc_messages.append(AIMessage(content=content))
                
        response = self._llm.invoke(lc_messages, **kwargs)
        return response.content

    def get_llm(self) -> ChatOpenAI:
        """获取 LLM 实例"""
        return self._llm

    def get_model_name(self) -> str:
        """获取模型名称"""
        return self._model_name or "unknown"

    def get_provider_type(self) -> str:
        """获取提供商类型"""
        return "openai"


# 全局回调处理器
_global_callbacks: List[BaseCallbackHandler] = []


def set_llm_callbacks(callbacks: List[BaseCallbackHandler]) -> None:
    """设置全局 LLM 回调处理器"""
    global _global_callbacks
    _global_callbacks = callbacks


def get_llm_callbacks() -> List[BaseCallbackHandler]:
    """获取全局 LLM 回调处理器"""
    return _global_callbacks


def get_llm(callbacks: list = None) -> ChatOpenAI:
    """获取 LLM 实例 - 支持回调

    Args:
        callbacks: 可选的回调处理器列表，用于捕获 LLM 调用
    """
    config = get_config()
    provider = config.model.get_active_provider()

    # 合并全局回调和传入的回调
    all_callbacks = []
    all_callbacks.extend(_global_callbacks)
    if callbacks:
        all_callbacks.extend(callbacks)

    return ChatOpenAI(
        model=provider.model_name,
        api_key=provider.api_key,
        base_url=provider.base_url if provider.base_url else None,
        temperature=provider.temperature,
        max_tokens=provider.max_tokens,
        callbacks=all_callbacks if all_callbacks else None,
        model_kwargs=provider.model_kwargs,
    )


def create_llm_provider() -> ILLMProvider:
    """创建 LLM 提供商实例"""
    config = get_config()
    provider = config.model.get_active_provider()

    return OpenAILLMProvider(
        model_name=provider.model_name,
        api_key=provider.api_key,
        base_url=provider.base_url,
        temperature=provider.temperature,
        max_tokens=provider.max_tokens,
        model_kwargs=provider.model_kwargs,
    )
