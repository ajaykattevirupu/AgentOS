from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import openai
import anthropic
import os

class LLMProvider(ABC):
    @abstractmethod
    async def complete(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Execute completion and return response with metadata"""
        pass

class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.client = openai.AsyncOpenAI(api_key=self.api_key)
    
    async def complete(self, prompt: str, **kwargs) -> Dict[str, Any]:
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                **kwargs
            )
            
            usage = response.usage
            
            # Calculate cost (simplified - use actual pricing)
            cost = (usage.prompt_tokens * 0.00003 + 
                   usage.completion_tokens * 0.00006)
            
            return {
                "content": response.choices[0].message.content,
                "tokens_prompt": usage.prompt_tokens,
                "tokens_completion": usage.completion_tokens,
                "tokens_total": usage.total_tokens,
                "cost_usd": cost,
                "model": self.model,
                "provider": "openai"
            }
        except Exception as e:
            raise Exception(f"OpenAI error: {str(e)}")

class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-5-sonnet-20241022"):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model = model
        self.client = anthropic.AsyncAnthropic(api_key=self.api_key)
    
    async def complete(self, prompt: str, **kwargs) -> Dict[str, Any]:
        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}],
                **kwargs
            )
            
            usage = response.usage
            
            # Calculate cost (simplified)
            cost = (usage.input_tokens * 0.000003 + 
                   usage.output_tokens * 0.000015)
            
            return {
                "content": response.content[0].text,
                "tokens_prompt": usage.input_tokens,
                "tokens_completion": usage.output_tokens,
                "tokens_total": usage.input_tokens + usage.output_tokens,
                "cost_usd": cost,
                "model": self.model,
                "provider": "anthropic"
            }
        except Exception as e:
            raise Exception(f"Anthropic error: {str(e)}")

def get_provider(provider: str, api_key: Optional[str] = None, model: Optional[str] = None) -> LLMProvider:
    """Factory to get LLM provider"""
    if provider == "openai":
        return OpenAIProvider(api_key=api_key, model=model or "gpt-4")
    elif provider == "anthropic":
        return AnthropicProvider(api_key=api_key, model=model or "claude-3-5-sonnet-20241022")
    else:
        raise ValueError(f"Unknown provider: {provider}")