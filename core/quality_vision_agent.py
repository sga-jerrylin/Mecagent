"""
Agent 3-3: 质量控制专家（Qwen-VL视觉版本）
直接从图纸识别尺寸标注和公差，生成质量检验清单
"""

import os
import json
from typing import List, Dict
from models.vision_model import Qwen3VLModel


class QualityVisionAgent:
    """质量控制专家（视觉版本）"""
    
    def __init__(self, api_key: str = None):
        """
        初始化质量视觉Agent
        
        Args:
            api_key: Qwen-VL API密钥
        """
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        self.vision_model = Qwen3VLModel(api_key=self.api_key)
    
    def analyze_quality(
        self,
        pdf_images: List[str],
        assembly_steps: List[Dict] = None,
        vision_context: Dict = None
    ) -> Dict:
        """
        从图纸中识别尺寸标注和公差，生成质量检验清单
        
        Args:
            pdf_images: PDF图片路径列表
            assembly_steps: 装配步骤（可选）
            vision_context: 视觉上下文（可选，来自Agent 1的尺寸信息）
            
        Returns:
            质量检验结果
        """
        print("\n📏 Agent 3-3: 质量控制专家（视觉识别）")
        print(f"   图片数量: {len(pdf_images)}")
        
        # 构建prompt
        prompt = self._build_quality_prompt(assembly_steps, vision_context)
        
        # 调用Qwen-VL（处理多张图片）
        print("   🤖 调用Qwen-VL识别尺寸标注...")

        all_quality_checkpoints = []
        all_critical_dimensions = []

        for i, image_path in enumerate(pdf_images, 1):
            print(f"   📄 分析第 {i}/{len(pdf_images)} 张图片...")

            try:
                # 调用Qwen-VL分析单张图片
                result = self.vision_model.analyze_engineering_drawing(
                    image_path=image_path,
                    focus_areas=['quality'],
                    drawing_type="工程图纸",
                    enable_thinking=True,
                    custom_user_query=prompt
                )

                # 解析结果（analyze_engineering_drawing返回的是字典，包含result字段）
                if result.get('success') and result.get('result'):
                    parsed_result = result['result']

                    # 合并质量检验点
                    if parsed_result:
                        checkpoints = parsed_result.get('quality_checkpoints', [])
                        dimensions = parsed_result.get('critical_dimensions', [])

                        all_quality_checkpoints.extend(checkpoints)
                        all_critical_dimensions.extend(dimensions)

                        print(f"      ✅ 识别到 {len(checkpoints)} 个检验点, {len(dimensions)} 个关键尺寸")
                    else:
                        print(f"      ⚠️  未识别到质量信息")
                else:
                    print(f"      ⚠️  分析失败或无结果")

            except Exception as e:
                print(f"      ❌ 分析失败: {e}")
                continue

        # 合并结果
        quality_result = {
            "quality_checkpoints": all_quality_checkpoints,
            "critical_dimensions": all_critical_dimensions
        }
        
        print(f"   ✅ 识别到 {len(quality_result.get('quality_checkpoints', []))} 个质量检验点")
        
        return quality_result
    
    def _build_quality_prompt(
        self,
        assembly_steps: List[Dict] = None,
        vision_context: Dict = None
    ) -> str:
        """构建质量检验的prompt"""
        
        prompt = """你是一位经验丰富的质量检验专家，请从工程图纸中识别关键尺寸和公差要求。

## 任务目标
1. 识别图纸中的所有关键尺寸标注（长度、直径、孔距等）
2. 识别公差要求（尺寸公差、形位公差、表面粗糙度）
3. 生成5-10个质量检验点，每个检验点包含具体的检验方法和合格标准

## 尺寸标注识别要点
- 基本尺寸：长度、宽度、高度、直径
- 尺寸公差：如 ±0.1mm、φ40H7、100±0.05
- 形位公差：平面度、垂直度、同轴度等
- 表面粗糙度：如 Ra3.2、Ra6.3
- 配合要求：如 H7/g6

## 输出要求
只输出JSON格式，包含以下字段：
```json
{
  "quality_checkpoints": [
    {
      "checkpoint_id": "检验点编号（如QC-001）",
      "checkpoint_name": "检验点名称",
      "inspection_item": "检验项目（如：底板平面度）",
      "inspection_method": "检验方法（工人能理解的语言）",
      "measurement_tool": "测量工具（如：游标卡尺、千分尺）",
      "acceptance_criteria": "合格标准（具体数值）",
      "inspection_timing": "检验时机（装配前/装配中/装配后）",
      "importance": "重要程度（关键/重要/一般）",
      "related_parts": "相关零件（BOM代号或零件名称）"
    }
  ],
  "critical_dimensions": [
    {
      "dimension_name": "尺寸名称",
      "nominal_value": "公称尺寸",
      "tolerance": "公差",
      "location": "位置描述"
    }
  ]
}
```

## 注意事项
1. 优先识别关键尺寸（影响装配、影响功能的尺寸）
2. 检验方法必须具体可操作
3. 合格标准必须有明确的数值范围
4. 每个检验点都要指定合适的测量工具
5. 如果图纸上没有尺寸标注，返回空数组

"""
        
        # 添加装配步骤上下文
        if assembly_steps:
            prompt += f"\n## 装配步骤上下文\n"
            prompt += f"装配步骤数量: {len(assembly_steps)}\n"
            for i, step in enumerate(assembly_steps[:3], 1):
                prompt += f"{i}. {step.get('title', '')}\n"
        
        # 添加视觉上下文
        if vision_context and vision_context.get('critical_dimensions'):
            prompt += f"\n## 已识别的关键尺寸（参考）\n"
            prompt += json.dumps(vision_context['critical_dimensions'], ensure_ascii=False, indent=2)
        
        prompt += "\n\n请开始识别图纸中的尺寸标注和公差要求，只返回JSON格式的结果。"
        
        return prompt
    
    def _parse_quality_result(self, result: str) -> Dict:
        """解析Qwen-VL返回的质量检验结果"""
        
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
            quality_data = json.loads(json_str)
            
            # 验证格式
            if "quality_checkpoints" not in quality_data:
                print("   ⚠️  返回格式不正确，使用空结果")
                return {
                    "quality_checkpoints": [],
                    "critical_dimensions": []
                }
            
            return quality_data
            
        except json.JSONDecodeError as e:
            print(f"   ⚠️  JSON解析失败: {e}")
            print(f"   原始响应: {result[:200]}...")
            return {
                "quality_checkpoints": [],
                "critical_dimensions": []
            }
        except Exception as e:
            print(f"   ⚠️  解析失败: {e}")
            return {
                "quality_checkpoints": [],
                "critical_dimensions": []
            }


def test_quality_vision_agent():
    """测试质量视觉Agent"""
    
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
    agent = QualityVisionAgent()
    
    # 执行分析
    result = agent.analyze_quality(pdf_images)
    
    # 打印结果
    print("\n" + "="*80)
    print("质量检验结果")
    print("="*80)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # 保存结果
    output_file = "test_output_three_agents/quality_vision_result.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n💾 结果已保存: {output_file}")


if __name__ == "__main__":
    test_quality_vision_agent()

