#!/usr/bin/env python3
"""
DeepSeek智能匹配模块
用于处理规则匹配失败的零件，通过LLM推理进行匹配
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional
from openai import OpenAI

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import API_CONFIG
from prompts.matching_prompts import (
    MATCHING_EXPERT_IDENTITY,
    build_matching_prompt
)


class DeepSeekMatcher:
    """DeepSeek智能匹配器"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化DeepSeek匹配器
        
        Args:
            api_key: DeepSeek API密钥，如果不提供则从配置文件读取
        """
        self.api_key = api_key or API_CONFIG['deepseek']['api_key']
        if not self.api_key:
            raise ValueError("DeepSeek API密钥未设置！请设置DEEPSEEK_API_KEY环境变量")
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=API_CONFIG['deepseek']['base_url']
        )
    
    def match_remaining_parts(
        self,
        matched_parts: List[Dict],
        unmatched_bom: List[Dict],
        unmatched_step: List[Dict],
        pdf_analysis: Optional[Dict] = None
    ) -> Dict:
        """
        使用DeepSeek推理匹配剩余零件
        
        Args:
            matched_parts: 已匹配的零件列表
            unmatched_bom: 未匹配的BOM项目
            unmatched_step: 未匹配的STEP零件
            pdf_analysis: PDF视觉分析结果（可选）
        
        Returns:
            {
                'new_matches': [...],  # 新匹配的零件
                'component_decomposition': [...],  # 组件拆解结果
                'still_unmatched_bom': [...],  # 仍未匹配的BOM
                'still_unmatched_step': [...],  # 仍未匹配的STEP
                'reasoning': str  # 推理过程
            }
        """
        # 构建提示词（使用统一的提示词管理）
        prompt = build_matching_prompt(
            matched_parts=matched_parts,
            unmatched_bom=unmatched_bom,
            unmatched_step=unmatched_step,
            pdf_analysis=pdf_analysis
        )
        
        # 调用DeepSeek API
        print("🤖 调用DeepSeek进行智能推理...")
        response = self.client.chat.completions.create(
            model=API_CONFIG['deepseek']['model'],
            messages=[
                {
                    "role": "system",
                    "content": MATCHING_EXPERT_IDENTITY
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=API_CONFIG['deepseek']['temperature'],
            max_tokens=API_CONFIG['deepseek']['max_tokens'],
            response_format={"type": "json_object"}  # 要求JSON格式输出
        )
        
        # 解析响应
        result_text = response.choices[0].message.content
        result = json.loads(result_text)
        
        print(f"✅ DeepSeek推理完成")
        print(f"   新匹配: {len(result.get('new_matches', []))} 个")
        print(f"   组件拆解: {len(result.get('component_decomposition', []))} 个")
        
        return result


def test_deepseek_matcher():
    """测试DeepSeek匹配器"""
    
    # 加载之前的匹配结果
    with open('test_output/step_bom_matching_v2_result.json', 'r', encoding='utf-8') as f:
        prev_result = json.load(f)
    
    matched_parts = prev_result['matched']
    unmatched_bom = prev_result['unmatched_bom']
    unmatched_step = prev_result['unmatched_step']
    
    print("="*80)
    print("DeepSeek智能匹配测试")
    print("="*80)
    print(f"已匹配: {len(matched_parts)} 个")
    print(f"未匹配BOM: {len(unmatched_bom)} 个")
    print(f"未匹配STEP: {len(unmatched_step)} 个")
    print()
    
    # 初始化匹配器
    matcher = DeepSeekMatcher()
    
    # 执行推理匹配
    result = matcher.match_remaining_parts(
        matched_parts=matched_parts,
        unmatched_bom=unmatched_bom,
        unmatched_step=unmatched_step
    )
    
    # 保存结果
    output_path = 'test_output/deepseek_matching_result.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 结果已保存到: {output_path}")
    
    # 显示摘要
    if 'summary' in result:
        summary = result['summary']
        print("\n" + "="*80)
        print("匹配摘要")
        print("="*80)
        print(f"新增匹配: {summary.get('total_new_matches', 0)} 个")
        print(f"组件拆解: {summary.get('total_components_decomposed', 0)} 个")
        print(f"最终匹配率: {summary.get('final_match_rate', 0) * 100:.1f}%")
        print(f"\n关键洞察: {summary.get('key_insights', 'N/A')}")


if __name__ == "__main__":
    test_deepseek_matcher()

