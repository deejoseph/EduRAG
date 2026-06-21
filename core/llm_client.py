"""
EduRAG LLM 客户端模块
封装 Ollama API 调用，提供统一的文本生成接口
"""

import json
import logging
import time
from typing import Optional, Dict, Any, List, Generator
import requests

logger = logging.getLogger(__name__)


class OllamaClient:
    """Ollama API 客户端"""
    
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "qwen2.5:7b",
        temperature: float = 0.7,
        num_predict: int = 1024,
        timeout: int = 120,  # 增加到120秒，支持gemma3等模型的长文本生成
        max_retries: int = 1,  # 减少重试次数到1次，快速失败
        retry_delay: float = 0.3  # 减少重试间隔
    ):
        """
        初始化 Ollama 客户端
        
        Args:
            base_url: Ollama 服务地址
            model: 模型名称
            temperature: 温度参数 (0-1)，越高越随机
            num_predict: 最大生成 token 数
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
            retry_delay: 重试间隔（秒）
        """
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.temperature = temperature
        self.num_predict = num_predict
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        self._chat_endpoint = f"{self.base_url}/api/chat"
        self._generate_endpoint = f"{self.base_url}/api/generate"
        
    def _check_ollama_available(self) -> bool:
        """检查 Ollama 服务是否可用"""
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return resp.status_code == 200
        except:
            return False
    
    def _get_installed_models(self) -> List[str]:
        """获取已安装的模型列表"""
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if resp.status_code == 200:
                models = resp.json().get("models", [])
                return [m["name"] for m in models]
            return []
        except:
            return []
    
    def _ensure_model_available(self) -> bool:
        """确保模型已安装，如果未安装则尝试拉取"""
        installed = self._get_installed_models()
        if self.model in installed:
            return True
        
        logger.warning(f"模型 {self.model} 未安装，正在尝试拉取...")
        try:
            # 调用 pull API（异步，可能需要较长时间）
            pull_resp = requests.post(
                f"{self.base_url}/api/pull",
                json={"name": self.model},
                timeout=300
            )
            if pull_resp.status_code == 200:
                logger.info(f"模型 {self.model} 拉取成功")
                return True
            else:
                logger.error(f"拉取模型失败: {pull_resp.text}")
                return False
        except Exception as e:
            logger.error(f"拉取模型异常: {e}")
            return False
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        对话式生成
        
        Args:
            messages: 消息列表，格式 [{"role": "user", "content": "..."}]
            system: 系统提示词（可选）
            **kwargs: 覆盖默认参数（temperature, num_predict 等）
            
        Returns:
            响应字典，包含 message, total_duration 等信息
        """
        # 确保服务可用
        if not self._check_ollama_available():
            raise ConnectionError(f"Ollama 服务不可用，请确保已启动: ollama serve")
        
        # 确保模型已安装
        if not self._ensure_model_available():
            raise RuntimeError(f"模型 {self.model} 不可用且无法自动拉取")
        
        # 构建请求体
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": kwargs.get("temperature", self.temperature),
                "num_predict": kwargs.get("num_predict", self.num_predict),
                "think": False,  # Qwen3 thinking mode 关闭，避免 <think> 标签干扰结构化输出
            }
        }
        if system:
            payload["system"] = system
        
        # 重试机制
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    self._chat_endpoint,
                    json=payload,
                    timeout=self.timeout
                )
                if response.status_code == 200:
                    return response.json()
                else:
                    last_exception = Exception(f"Ollama 返回错误 {response.status_code}: {response.text}")
                    logger.warning(f"尝试 {attempt+1}/{self.max_retries} 失败: {last_exception}")
            except requests.exceptions.RequestException as e:
                last_exception = e
                logger.warning(f"尝试 {attempt+1}/{self.max_retries} 请求失败: {e}")
            
            if attempt < self.max_retries - 1:
                time.sleep(self.retry_delay * (2 ** attempt))  # 指数退避
        
        raise last_exception or RuntimeError("未知错误")
    
    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        生成式（非对话）调用
        
        Args:
            prompt: 用户提示词
            system: 系统提示词
            **kwargs: 覆盖默认参数
            
        Returns:
            响应字典，包含 response, total_duration 等
        """
        if not self._check_ollama_available():
            raise ConnectionError("Ollama 服务不可用")
        
        if not self._ensure_model_available():
            raise RuntimeError(f"模型 {self.model} 不可用")
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": kwargs.get("temperature", self.temperature),
                "num_predict": kwargs.get("num_predict", self.num_predict),
                "think": False,  # Qwen3 thinking mode 关闭，避免 <think> 标签干扰结构化输出
            }
        }
        if system:
            payload["system"] = system
        
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    self._generate_endpoint,
                    json=payload,
                    timeout=self.timeout
                )
                if response.status_code == 200:
                    return response.json()
                else:
                    last_exception = Exception(f"状态码 {response.status_code}: {response.text}")
            except Exception as e:
                last_exception = e
            
            if attempt < self.max_retries - 1:
                time.sleep(self.retry_delay * (2 ** attempt))
        
        raise last_exception
    
    def chat_stream(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        **kwargs
    ) -> Generator[str, None, None]:
        """
        流式对话生成，逐块返回文本
        
        Yields:
            文本块（字符串）
        """
        if not self._check_ollama_available():
            raise ConnectionError("Ollama 服务不可用")
        
        if not self._ensure_model_available():
            raise RuntimeError(f"模型 {self.model} 不可用")
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": kwargs.get("temperature", self.temperature),
                "num_predict": kwargs.get("num_predict", self.num_predict),
                "think": False,  # Qwen3 thinking mode 关闭，避免 <think> 标签干扰结构化输出
            }
        }
        if system:
            payload["system"] = system
        
        with requests.post(self._chat_endpoint, json=payload, stream=True, timeout=self.timeout) as resp:
            if resp.status_code != 200:
                raise Exception(f"请求失败: {resp.status_code}")
            
            for line in resp.iter_lines(decode_unicode=True):
                if line:
                    try:
                        chunk = json.loads(line)
                        if "message" in chunk and "content" in chunk["message"]:
                            yield chunk["message"]["content"]
                        if chunk.get("done", False):
                            break
                    except json.JSONDecodeError:
                        continue


# 简单测试
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    client = OllamaClient(model="qwen2.5:7b", temperature=0.7)
    
    # 测试非流式对话
    print("=== 测试对话 ===")
    resp = client.chat([
        {"role": "user", "content": "你好，请用一句话介绍你自己。"}
    ])
    print(resp["message"]["content"])
    
    # 测试流式
    print("\n=== 测试流式输出 ===")
    for chunk in client.chat_stream([
        {"role": "user", "content": "写一首关于春天的五言绝句"}
    ]):
        print(chunk, end="", flush=True)
    print("\n")
    
    # 测试 generate 模式
    print("=== 测试 generate ===")
    resp2 = client.generate("解释什么是RAG")
    print(resp2["response"])