# -*- coding: utf-8 -*-
"""
Agent 4: 

"""

from typing import Dict, List
from agents.base_gemini_agent import BaseGeminiAgent
from prompts.agent_4_product_assembly import build_product_assembly_prompt


class ProductAssemblyAgent(BaseGeminiAgent):
    """"""
    
    def __init__(self, api_key: str = None):
        super().__init__(
            agent_name="Agent4_",
            api_key=api_key,
            temperature=0.1
        )
    
    def process(
        self,
        product_plan: Dict,
        product_images: List[str],
        components_list: List[Dict],
        product_bom: List[Dict] = None,  # ✅ 新增：产品级BOM
        bom_to_mesh_mapping: Dict = None  # ✅ 新增：BOM-3D映射
    ) -> Dict:
        """
        生成产品总装步骤

        Args:
            product_plan: Agent 1的规划结果
            product_images: 产品总图图片
            components_list: 组件列表
            product_bom: 产品级BOM列表（从产品总图提取的零件）
            bom_to_mesh_mapping: BOM到mesh_id的映射表

        Returns:
            {
                "success": bool,
                "product_name": str,
                "assembly_steps": [...]  # 装配步骤
            }
        """
        product_name = product_plan.get("product_name", "")

        print(f"\n{'='*80}")
        print(f" Agent 4:  - {product_name}")
        print(f"{'='*80}")
        print(f" : {len(product_images)}")
        print(f" : {len(components_list)}")
        if product_bom:
            print(f" BOM: {len(product_bom)}")

        # 构建提示词
        system_prompt, user_query = build_product_assembly_prompt(
            product_plan=product_plan,
            components_list=components_list,
            product_bom=product_bom or []  # ✅ 传入产品级BOM
        )
        
        # Gemini
        result = self.call_gemini(
            system_prompt=system_prompt,
            user_query=user_query,
            images=product_images
        )
        
        if result["success"]:
            parsed = result["result"]
            
            # 
            assembly_steps = parsed.get("assembly_steps", [])
            
            print(f"\n :")
            print(f"   - : {len(assembly_steps)}")
            
            return {
                "success": True,
                "product_name": product_name,
                "assembly_steps": assembly_steps,
                "raw_result": parsed
            }
        else:
            print(f"\n : {result.get('error')}")
            return {
                "success": False,
                "error": result.get("error"),
                "product_name": product_name,
                "assembly_steps": []
            }

