"""
Agent 3-2: 焊接工艺翻译专家（Qwen-VL视觉版本）
直接从图纸识别焊接符号，翻译为工人友好的焊接指导
"""

import os
import json
from typing import List, Dict
from models.vision_model import Qwen3VLModel


class WeldingVisionAgent:
    """焊接工艺翻译专家（视觉版本）"""
    
    def __init__(self, api_key: str = None):
        """
        初始化焊接视觉Agent
        
        Args:
            api_key: Qwen-VL API密钥
        """
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        self.vision_model = Qwen3VLModel(api_key=self.api_key)
    
    def analyze_welding(
        self,
        pdf_images: List[str],
        assembly_steps: List[Dict] = None,
        vision_context: Dict = None
    ) -> Dict:
        """
        从图纸中识别焊接符号并生成焊接要求
        
        Args:
            pdf_images: PDF图片路径列表
            assembly_steps: 装配步骤（可选，用于关联焊接位置）
            vision_context: 视觉上下文（可选，来自Agent 1的焊接信息）
            
        Returns:
            焊接要求结果
        """
        print("\n🔥 Agent 3-2: 焊接工艺翻译专家（视觉识别）")
        print(f"   图片数量: {len(pdf_images)}")
        
        # 构建prompt
        prompt = self._build_welding_prompt(assembly_steps, vision_context)
        
        # 调用Qwen-VL（处理多张图片）
        print("   🤖 调用Qwen-VL识别焊接符号...")

        all_welding_requirements = []

        for i, image_path in enumerate(pdf_images, 1):
            print(f"   📄 分析第 {i}/{len(pdf_images)} 张图片...")

            try:
                # 调用Qwen-VL分析单张图片
                result = self.vision_model.analyze_engineering_drawing(
                    image_path=image_path,
                    focus_areas=['welding'],
                    drawing_type="工程图纸",
                    enable_thinking=True,
                    custom_user_query=prompt
                )

                # 解析结果（analyze_engineering_drawing返回的是字典，包含result字段）
                if result.get('success') and result.get('result'):
                    parsed_result = result['result']

                    # 合并焊接要求
                    if parsed_result and parsed_result.get('welding_requirements'):
                        all_welding_requirements.extend(parsed_result['welding_requirements'])
                        print(f"      ✅ 识别到 {len(parsed_result['welding_requirements'])} 个焊接要求")
                    else:
                        print(f"      ⚠️  未识别到焊接要求")
                else:
                    print(f"      ⚠️  分析失败或无结果")

            except Exception as e:
                print(f"      ❌ 分析失败: {e}")
                continue

        # 合并结果
        welding_result = {"welding_requirements": all_welding_requirements}
        
        print(f"   ✅ 识别到 {len(welding_result.get('welding_requirements', []))} 个焊接要求")
        
        return welding_result
    
    def _build_welding_prompt(
        self,
        assembly_steps: List[Dict] = None,
        vision_context: Dict = None
    ) -> str:
        """构建焊接识别的prompt"""
        
        prompt = """你是一位经验丰富的焊接工艺专家，请从工程图纸中识别焊接符号和焊接要求。

## 任务目标
1. 识别图纸中的所有焊接符号（焊缝符号、焊接方法代号等）
2. 将专业的焊接符号翻译为一线焊工能理解的简单语言
3. 生成3-5个最关键的焊接要求

## 焊接符号识别要点
- 焊缝类型：对接焊、角焊、塞焊等
- 焊脚高度：如 6mm、8mm
- 焊接方法代号：如 111（手工电弧焊）、135（MAG焊）
- 焊接位置：平焊、立焊、横焊、仰焊
- 焊接质量等级：如 II级、III级

## 输出要求
只输出JSON格式，包含以下字段：
```json
{
  "welding_requirements": [
    {
      "requirement_id": "焊接要求编号（如WR-001）",
      "welding_location": "焊接位置描述（工人能理解的语言）",
      "welding_type": "焊接类型（如：角焊、对接焊）",
      "welding_method": "焊接方法（如：手工电弧焊、气保焊）",
      "weld_size": "焊缝尺寸（如：焊脚高度6mm）",
      "quality_requirement": "质量要求（简单描述）",
      "worker_instruction": "给焊工的简单指导（3-5句话）",
      "inspection_method": "检查方法（如：目视检查、渗透检测）",
      "importance": "重要程度（关键/重要/一般）"
    }
  ]
}
```

## 注意事项
1. 语言必须简单直白，避免专业术语
2. 每个焊接要求都要有具体的检查方法
3. 优先识别关键焊缝（承重部位、密封部位）
4. 如果图纸上没有焊接符号，返回空数组

"""
        
        # 添加装配步骤上下文
        if assembly_steps:
            prompt += f"\n## 装配步骤上下文\n"
            prompt += f"装配步骤数量: {len(assembly_steps)}\n"
            for i, step in enumerate(assembly_steps[:3], 1):
                prompt += f"{i}. {step.get('title', '')}\n"
        
        # 添加视觉上下文
        if vision_context and vision_context.get('welding_info'):
            prompt += f"\n## 已识别的焊接信息（参考）\n"
            prompt += json.dumps(vision_context['welding_info'], ensure_ascii=False, indent=2)
        
        prompt += "\n\n请开始识别图纸中的焊接符号，只返回JSON格式的结果。"
        
        return prompt
    
    def _parse_welding_result(self, result: str) -> Dict:
        """解析Qwen-VL返回的焊接结果"""
        
        try:
            # 提取JSON
            if "```json" in result:
                json_start = result.find("```json") + 7
                json_end = result.find("```", json_start)
                json_str = result[json_start:json_end].strip()
            elif "```" in result:
                json_start = result.find("```") + 3
                json_end = result.find("```", json_start)
                json_str = result[json_start:json_end].strip()
            else:
                json_str = result.strip()
            
            # 解析JSON
            welding_data = json.loads(json_str)
            
            # 验证格式
            if "welding_requirements" not in welding_data:
                print("   ⚠️  返回格式不正确，使用空结果")
                return {"welding_requirements": []}
            
            return welding_data
            
        except json.JSONDecodeError as e:
            print(f"   ⚠️  JSON解析失败: {e}")
            print(f"   原始响应: {result[:200]}...")
            return {"welding_requirements": []}
        except Exception as e:
            print(f"   ⚠️  解析失败: {e}")
            return {"welding_requirements": []}


def test_welding_vision_agent():
    """测试焊接视觉Agent"""
    
    # 准备测试数据
    pdf_images = [
        "test_output_three_agents/pdf_images/page_1.png",
        "test_output_three_agents/pdf_images/page_2.png"
    ]
    
    # 检查图片是否存在
    for img in pdf_images:
        if not os.path.exists(img):
            print(f"❌ 图片不存在: {img}")
            return
    
    # 创建Agent
    agent = WeldingVisionAgent()
    
    # 执行分析
    result = agent.analyze_welding(pdf_images)
    
    # 打印结果
    print("\n" + "="*80)
    print("焊接识别结果")
    print("="*80)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # 保存结果
    output_file = "test_output_three_agents/welding_vision_result.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n💾 结果已保存: {output_file}")


if __name__ == "__main__":
    test_welding_vision_agent()

