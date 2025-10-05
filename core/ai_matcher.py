"""
AI智能匹配器
用于处理代码匹配失败的零件
"""

import json
import re
from typing import List, Dict
from openai import OpenAI
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入提示词
from prompts.agent_2_bom_3d_matching import (
    build_ai_matching_prompt,
    AI_MATCHING_SYSTEM_PROMPT
)


class AIBOMMatcher:
    """AI智能BOM匹配器（使用Gemini 2.5 Flash）"""

    def __init__(self, api_key: str = None):
        # 使用Gemini 2.5 Flash（通过OpenRouter）
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("需要设置OPENROUTER_API_KEY环境变量或传入api_key参数")

        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://openrouter.ai/api/v1"
        )
        self.model = "google/gemini-2.5-flash-preview-09-2025"  # 和其他agent使用相同的模型
    
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
        print(f"\n   🤖 AI员工开始工作...")
        print(f"      📊 他看到了 {len(unmatched_parts)} 个未匹配的3D零件")
        print(f"      📋 他参考了 {len(bom_data)} 个BOM项")
        print(f"      🎯 他准备用智能算法进行匹配...")
        import sys
        sys.stdout.flush()

        # 一次性处理所有零件
        all_results = self._match_all_at_once(unmatched_parts, bom_data)

        # 统计（降低阈值到0.6，追求100%匹配率）
        matched_count = sum(1 for r in all_results if r.get('matched_bom_code'))
        high_confidence_count = sum(1 for r in all_results if r.get('confidence', 0) >= 0.6)

        print(f"\n      ✅ AI员工分析完成:")
        print(f"         成功匹配: {matched_count}/{len(all_results)}")
        print(f"         高置信度(≥0.6): {high_confidence_count}/{len(all_results)}")
        import sys
        sys.stdout.flush()

        return all_results
    
    def _match_all_at_once(self, parts: List[Dict], bom_data: List[Dict]) -> List[Dict]:
        """
        一次性匹配所有零件

        Args:
            parts: 未匹配的3D零件列表
            bom_data: 未匹配的BOM列表（已经在调用方计算好了）
        """

        print(f"      📝 他正在准备分析资料...")
        import sys
        sys.stdout.flush()

        # ✅ bom_data已经是未匹配的BOM了，不需要再次计算
        unmatched_bom = bom_data

        print(f"      📊 他发现还有 {len(unmatched_bom)} 个BOM未匹配")
        sys.stdout.flush()

        # 使用提示词文件构建prompt
        system_prompt, user_query = build_ai_matching_prompt(parts, unmatched_bom)

        print(f"      🤖 他开始调用Gemini 2.5 Flash进行深度分析...")
        print(f"      ⏱️  请稍候，Gemini速度很快...")
        sys.stdout.flush()

        # 调用AI
        try:
            import time
            start_time = time.time()

            response = self.client.chat.completions.create(
                model=self.model,  # 使用Gemini 2.5 Flash
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_query}
                ],
                temperature=0.4,  # ✅ 提高到0.4，使用COT推理，追求100%匹配率
                # ✅ 不限制max_tokens，Gemini 2.5 Flash支持65.5K输出（COT需要更多token）
                stream=False,
                timeout=60
            )

            elapsed = time.time() - start_time
            result_text = response.choices[0].message.content

            print(f"      📊 AI大脑返回了分析结果 ({len(result_text)} 字符, 耗时: {elapsed:.1f}秒)")
            import sys
            sys.stdout.flush()

            # 调试：保存AI原始响应
            debug_file = f"debug_output/ai_matching_response_{int(time.time())}.txt"
            os.makedirs("debug_output", exist_ok=True)
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(result_text)
            print(f"      💾 AI响应已保存到: {debug_file}")

            # 解析JSON
            ai_results = self._parse_response(result_text)

            if not ai_results:
                print(f"   ⚠️  JSON解析失败，返回空结果")
                return self._create_empty_results(parts)

            # 将AI结果映射回原始零件
            # AI返回格式：{"mesh_id": "...", "geometry_name": "...", "bom_code": "...", "confidence": 0.85, "reasoning": "..."}
            results = []
            for part in parts:
                # 查找对应的AI结果（通过mesh_id或geometry_name匹配）
                ai_result = None
                part_mesh_id = part.get('mesh_id', '')
                part_geometry = part.get('geometry_name', '')

                for ar in ai_results:
                    # 尝试通过mesh_id匹配
                    if ar.get('mesh_id') == part_mesh_id:
                        ai_result = ar
                        break
                    # 尝试通过geometry_name匹配
                    elif ar.get('geometry_name') == part_geometry:
                        ai_result = ar
                        break

                if ai_result:
                    results.append({
                        'mesh_id': part.get('mesh_id'),
                        'geometry_name': part.get('geometry_name'),
                        'node_name': part.get('node_name'),
                        'matched_bom_code': ai_result.get('bom_code'),  # AI返回的是bom_code
                        'confidence': ai_result.get('confidence', 0.0),
                        'reason': ai_result.get('reasoning', '')  # AI返回的是reasoning
                    })
                else:
                    # 如果没找到对应结果，返回空匹配
                    results.append({
                        'mesh_id': part.get('mesh_id'),
                        'geometry_name': part.get('geometry_name'),
                        'node_name': part.get('node_name'),
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
                "mesh_id": p.get('mesh_id'),
                "geometry_name": p.get('geometry_name'),
                "node_name": p.get('node_name'),
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
- bom_code: 匹配到的BOM代号（如"01.09.2556"），如果无法匹配则为null
- confidence: 匹配置信度（0-1）
- reasoning: 匹配理由（简短说明）

请只返回JSON数组，不要其他解释。

示例输出：
[
  {
    "geometry_name": "T-SPV1830-EURO-09-Q235",
    "bom_code": "01.09.2556",
    "confidence": 0.95,
    "reasoning": "产品代号完全匹配"
  },
  {
    "geometry_name": "M16x60-GB/T5782-2000",
    "bom_code": "02.03.0088",
    "confidence": 0.85,
    "reasoning": "规格M16匹配"
  }
]
"""
        return prompt
    
    def _parse_response(self, response_text: str) -> List[Dict]:
        """解析AI响应（参考dual_channel_parser的成熟方案）"""

        # 移除markdown代码块标记（参考dual_channel_parser）
        content = response_text.strip()

        if content.startswith('```json'):
            content = content[7:]  # 移除 ```json

        if content.startswith('```'):
            content = content[3:]  # 移除 ```

        if content.endswith('```'):
            content = content[:-3]  # 移除结尾的 ```

        content = content.strip()

        # 查找JSON的开始和结束
        json_start = content.find('{')
        json_end = content.rfind('}') + 1

        if json_start >= 0 and json_end > json_start:
            json_str = content[json_start:json_end]

            # ✅ 自动修复常见的JSON格式错误
            # 1. 移除数组/对象最后一个元素后的逗号（如 },\n] 或 },\n}）
            json_str = re.sub(r',(\s*[\]}])', r'\1', json_str)

            # 2. 移除控制字符
            json_str = ''.join(char for char in json_str if ord(char) >= 32 or char in '\n\r\t')

            # 尝试解析JSON
            try:
                parsed_result = json.loads(json_str)
                print(f"      ✅ JSON解析成功")

                # 如果返回的是对象，提取ai_matched_pairs字段
                if isinstance(parsed_result, dict):
                    if 'ai_matched_pairs' in parsed_result:
                        return parsed_result['ai_matched_pairs']
                    else:
                        print(f"      ⚠️  JSON格式错误：缺少'ai_matched_pairs'字段")
                        return []
                # 如果直接返回数组
                elif isinstance(parsed_result, list):
                    return parsed_result
                else:
                    print(f"      ⚠️  JSON格式错误：期望对象或数组，得到 {type(parsed_result)}")
                    return []

            except json.JSONDecodeError as e:
                error_msg = f"JSON解析失败: line {e.lineno} column {e.colno} (char {e.pos})"
                print(f"      ⚠️  {error_msg}")
                return []
            except Exception as e:
                print(f"      ⚠️  解析错误: {e}")
                return []
        else:
            print(f"      ⚠️  未找到有效的JSON数据")
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

