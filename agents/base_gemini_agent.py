# -*- coding: utf-8 -*-
"""
Gemini Agent 
Gemini 2.5 FlashAgent
"""

import os
import json
import base64
from typing import Dict, List, Optional, Union
from openai import OpenAI
import datetime


class BaseGeminiAgent:
    """Gemini 2.5 Flash Agent"""
    
    def __init__(
        self,
        agent_name: str,
        api_key: Optional[str] = None,
        temperature: float = 0.1
    ):
        """
        Gemini Agent
        
        Args:
            agent_name: Agent
            api_key: OpenRouter API Key
            temperature: 0-1
        """
        self.agent_name = agent_name
        self.temperature = temperature
        
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEYapi_key")
        
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.api_key
        )
        
        self.model_name = "google/gemini-2.5-flash-preview-09-2025"
    
    def encode_image_to_base64(self, image_path: str) -> str:
        """
        base64

        Args:
            image_path: 

        Returns:
            base64URL
        """
        try:
            with open(image_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode('ascii')
                # 
                if image_path.lower().endswith('.png'):
                    return f"data:image/png;base64,{encoded_string}"
                elif image_path.lower().endswith(('.jpg', '.jpeg')):
                    return f"data:image/jpeg;base64,{encoded_string}"
                else:
                    return f"data:image/png;base64,{encoded_string}"
        except Exception as e:
            print(f"  : {image_path}")
            print(f"   : {str(e)}")
            raise
    
    def call_gemini(
        self,
        system_prompt: str,
        user_query: str,
        images: Optional[Union[str, List[str]]] = None
    ) -> Dict:
        """
        Gemini 2.5 Flash
        
        Args:
            system_prompt: 
            user_query: 
            images: 
            
        Returns:
            {
                "success": bool,
                "result": dict,  # JSON
                "raw_response": str  # 
            }
        """
        # 
        image_paths = []
        if images:
            if isinstance(images, str):
                image_paths = [images]
            else:
                image_paths = images
        
        # 
        user_content = []
        
        # 
        user_content.append({
            "type": "text",
            "text": user_query
        })
        
        # 
        for img_path in image_paths:
            if img_path.startswith('http'):
                image_url = img_path
            else:
                image_url = self.encode_image_to_base64(img_path)
            
            user_content.append({
                "type": "image_url",
                "image_url": {"url": image_url}
            })
        
        # 
        messages = [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_content
            }
        ]
        
        try:
            print(f"\n[{self.agent_name}] Calling Gemini 2.5 Flash")
            print(f"   Images: {len(image_paths)}")
            print(f"   Temperature: {self.temperature}")

            # API
            completion = self.client.chat.completions.create(
                extra_headers={
                    "HTTP-Referer": "https://mecagent.com",
                    "X-Title": "MecAgent"  # 
                },
                model=self.model_name,
                messages=messages,
                temperature=self.temperature
            )
            
            # 
            response_content = completion.choices[0].message.content
            
            print(f"[{self.agent_name}] Success")
            
            # JSON
            parsed_result = self._parse_json_response(response_content)
            
            # 
            self._save_debug_output(
                system_prompt=system_prompt,
                user_query=user_query,
                image_count=len(image_paths),
                response=response_content,
                parsed=parsed_result
            )
            
            return {
                "success": True,
                "result": parsed_result,
                "raw_response": response_content
            }
            
        except Exception as e:
            print(f"[{self.agent_name}] Failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "result": None
            }
    
    def _parse_json_response(self, response_content: str) -> Dict:
        """
        JSON
        
        Args:
            response_content: 
            
        Returns:
            JSON
        """
        try:
            # 
            json_start = response_content.find('{')
            json_end = response_content.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response_content[json_start:json_end]
                return json.loads(json_str)
            else:
                return {"raw_content": response_content}
        except json.JSONDecodeError as e:
            # JSON```json
            if "```json" in response_content:
                json_start = response_content.find("```json") + 7
                json_end = response_content.find("```", json_start)
                if json_end > json_start:
                    json_str = response_content[json_start:json_end].strip()
                    try:
                        return json.loads(json_str)
                    except:
                        return {"raw_content": response_content, "parse_error": str(e)}
                else:
                    return {"raw_content": response_content, "parse_error": str(e)}
            else:
                return {"raw_content": response_content, "parse_error": str(e)}
    
    def _save_debug_output(
        self,
        system_prompt: str,
        user_query: str,
        image_count: int,
        response: str,
        parsed: Dict
    ):
        """
        
        
        Args:
            system_prompt: 
            user_query: 
            image_count: 
            response: 
            parsed: 
        """
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = "debug_output"
        os.makedirs(output_dir, exist_ok=True)
        
        # agent
        safe_name = self.agent_name.replace(" ", "_").replace("/", "_")
        output_file = os.path.join(output_dir, f"{safe_name}_{timestamp}.json")
        
        result_data = {
            "agent_name": self.agent_name,
            "model": self.model_name,
            "timestamp": timestamp,
            "image_count": image_count,
            "temperature": self.temperature,
            "system_prompt": system_prompt,
            "user_query": user_query,
            "raw_response": response,
            "parsed_result": parsed
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)
        
        print(f" [{self.agent_name}] : {output_file}")
    
    def process(self, **kwargs) -> Dict:
        """
        
        
        Args:
            **kwargs: 
            
        Returns:
            
        """
        raise NotImplementedError("process")

