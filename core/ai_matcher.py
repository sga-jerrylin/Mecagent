"""
AI智能匹配器
用于处理代码匹配失败的零件
"""

import json
from typing import List, Dict
from openai import OpenAI
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入提示词
from prompts.agent_2_ai_bom_matcher_prompts import (
    build_ai_matching_prompt,
    AI_MATCHER_SYSTEM_PROMPT
)


class AIBOMMatcher:
    """AI智能BOM匹配器"""
    
    def __init__(self, api_key: str = "sk-ea98b5da86954ddcaa2ff10e5bbba2b4"):
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )
    
    def match_unmatched_parts(
        self,
        unmatched_parts: List[Dict],
        bom_data: List[Dict]
    ) -> List[Dict]:
        """
        用AI一次性匹配所有未匹配的零件

        Args:
            unmatched_parts: 未匹配的零件列表
            bom_data: BOM表数据

        Returns:
            AI匹配结果列表
        """
        print(f"\n🤖 启动AI智能匹配...")
        print(f"   未匹配零件数: {len(unmatched_parts)}")
        print(f"   BOM项数: {len(bom_data)}")
        print(f"   策略: 一次性处理所有未匹配零件")

        # 一次性处理所有零件
        all_results = self._match_all_at_once(unmatched_parts, bom_data)

        # 统计
        matched_count = sum(1 for r in all_results if r.get('matched_bom_code'))
        high_confidence_count = sum(1 for r in all_results if r.get('confidence', 0) >= 0.8)

        print(f"\n✅ AI匹配完成:")
        print(f"   成功匹配: {matched_count}/{len(all_results)}")
        print(f"   高置信度(≥0.8): {high_confidence_count}/{len(all_results)}")

        return all_results
    
    def _match_all_at_once(self, parts: List[Dict], bom_data: List[Dict]) -> List[Dict]:
        """一次性匹配所有零件"""

        print(f"   📝 构建prompt...")

        # 使用提示词文件构建prompt
        prompt = build_ai_matching_prompt(parts, bom_data)

        print(f"   🤖 调用DeepSeek API...")

        # 调用AI
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": AI_MATCHER_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=8000,  # 增加token限制以处理更多零件
                stream=False
            )

            result_text = response.choices[0].message.content

            print(f"   📊 AI返回了 {len(result_text)} 个字符")

            # 解析JSON
            ai_results = self._parse_response(result_text)

            if not ai_results:
                print(f"   ⚠️  JSON解析失败，返回空结果")
                return self._create_empty_results(parts)

            # 将AI结果映射回原始零件
            results = []
            for part in parts:
                # 查找对应的AI结果
                ai_result = None
                for ar in ai_results:
                    if ar.get('index') is not None:
                        # 通过index匹配
                        if ar['index'] == parts.index(part):
                            ai_result = ar
                            break

                if ai_result:
                    results.append({
                        'geometry_name': part['geometry_name'],
                        'matched_bom_code': ai_result.get('matched_bom_code'),
                        'confidence': ai_result.get('confidence', 0.0),
                        'reason': ai_result.get('reason', '')
                    })
                else:
                    # 如果没找到对应结果，返回空匹配
                    results.append({
                        'geometry_name': part['geometry_name'],
                        'matched_bom_code': None,
                        'confidence': 0.0,
                        'reason': 'AI未返回匹配结果'
                    })

            return results

        except Exception as e:
            print(f"   ❌ AI匹配失败: {e}")
            import traceback
            traceback.print_exc()
            return self._create_empty_results(parts)

    def _create_empty_results(self, parts: List[Dict]) -> List[Dict]:
        """创建空的匹配结果"""
        return [
            {
                "geometry_name": p['geometry_name'],
                "matched_bom_code": None,
                "confidence": 0.0,
                "reason": "AI匹配失败"
            }
            for p in parts
        ]
    
    def _build_prompt(self, parts: List[Dict], bom_data: List[Dict]) -> str:
        """构建AI匹配的prompt"""
        
        # 限制BOM表大小（只发送前100项）
        bom_sample = bom_data[:100] if len(bom_data) > 100 else bom_data
        
        prompt = f"""你是一个BOM-3D零件匹配专家。你的任务是将3D模型中的零件名称与BOM表中的项目进行匹配。

## 背景
- 3D零件名称可能有编码问题（乱码），但你可以通过产品代号、规格、关键词等线索进行匹配
- BOM表包含：代号（code）、产品代号（product_code）、名称（name）等信息
- 匹配依据：产品代号（优先）、规格（如M16、φ40等）、零件类型（螺栓、垫圈、方形板等）

## BOM表（{len(bom_data)}项，显示前{len(bom_sample)}项）
```json
{json.dumps(bom_sample, ensure_ascii=False, indent=2)[:2000]}
...
```

## 未匹配的3D零件（{len(parts)}个）
```json
{json.dumps([{'fixed_name': p['fixed_name'], 'geometry_name': p['geometry_name']} for p in parts], ensure_ascii=False, indent=2)}
```

## 匹配规则
1. **优先匹配产品代号**：如果3D零件名称中包含产品代号（如T-SPV1830-EURO-09），优先匹配
2. **规格匹配**：对于标准件（螺栓、垫圈等），通过规格（M16、φ40等）匹配
3. **关键词匹配**：通过零件类型关键词（方形板、垫圈、螺栓等）辅助匹配
4. **无法匹配**：如果BOM表中确实没有对应项，返回null

## 输出格式
返回JSON数组，每个元素包含：
- geometry_name: 3D零件的原始名称（必须与输入完全一致）
- matched_bom_code: 匹配到的BOM代号（如"01.09.2556"），如果无法匹配则为null
- confidence: 匹配置信度（0-1）
- reason: 匹配理由（简短说明）

请只返回JSON数组，不要其他解释。
"""
        return prompt
    
    def _parse_response(self, response_text: str) -> List[Dict]:
        """解析AI响应"""
        
        # 提取JSON部分
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()
        elif "```" in response_text:
            json_start = response_text.find("```") + 3
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()
        
        # 解析JSON
        try:
            results = json.loads(response_text)
            return results
        except Exception as e:
            print(f"   ⚠️  JSON解析失败: {e}")
            return []
    
    def apply_ai_matches(
        self,
        cleaned_parts: List[Dict],
        ai_matches: List[Dict],
        min_confidence: float = 0.8
    ) -> List[Dict]:
        """
        将AI匹配结果应用到零件列表
        
        Args:
            cleaned_parts: 清洗后的零件列表
            ai_matches: AI匹配结果
            min_confidence: 最小置信度阈值
            
        Returns:
            更新后的零件列表
        """
        print(f"\n🔧 应用AI匹配结果...")
        
        # 创建geometry_name到AI匹配的映射
        ai_match_map = {
            m['geometry_name']: m
            for m in ai_matches
            if m.get('matched_bom_code') and m.get('confidence', 0) >= min_confidence
        }
        
        # 应用AI匹配
        updated_count = 0
        for part in cleaned_parts:
            # 只更新未匹配的零件
            if not part.get('bom_code'):
                geometry_name = part['geometry_name']
                if geometry_name in ai_match_map:
                    ai_match = ai_match_map[geometry_name]
                    part['bom_code'] = ai_match['matched_bom_code']
                    part['match_method'] = f"AI匹配(置信度{ai_match['confidence']:.2f})"
                    part['confidence'] = ai_match['confidence']
                    part['ai_reason'] = ai_match.get('reason', '')
                    updated_count += 1
        
        print(f"   更新了 {updated_count} 个零件的匹配结果")
        
        return cleaned_parts

