# -*- coding: utf-8 -*-
"""
Agent 3: 

"""

from typing import Dict, List
from agents.base_gemini_agent import BaseGeminiAgent
from prompts.agent_3_component_assembly import build_component_assembly_prompt


class ComponentAssemblyAgent(BaseGeminiAgent):
    """"""
    
    def __init__(self, api_key: str = None):
        super().__init__(
            agent_name="Agent3_",
            api_key=api_key,
            temperature=0.1
        )
    
    def process(
        self,
        component_plan: Dict,
        component_images: List[str],
        parts_list: List[Dict],
        bom_to_mesh_mapping: Dict = None
    ) -> Dict:
        """
        
        
        Args:
            component_plan: Agent 1
            component_images: 
            parts_list: 
            bom_to_mesh_mapping: BOMmesh_id
            
        Returns:
            {
                "success": bool,
                "component_code": str,
                "component_name": str,
                "assembly_steps": [...]  # 
            }
        """
        component_name = component_plan.get("component_name", "")
        
        print(f"\n{'='*80}")
        print(f" Agent 3:  - {component_name}")
        print(f"{'='*80}")
        print(f" : {len(component_images)}")
        print(f" : {len(parts_list)}")
        
        # 
        system_prompt, user_query = build_component_assembly_prompt(
            component_plan=component_plan,
            parts_list=parts_list
        )
        
        # Gemini
        result = self.call_gemini(
            system_prompt=system_prompt,
            user_query=user_query,
            images=component_images
        )
        
        if result["success"]:
            parsed = result["result"]
            
            # 
            assembly_steps = parsed.get("assembly_steps", [])
            
            # BOM-3Dmesh_id
            if bom_to_mesh_mapping:
                assembly_steps = self._add_mesh_ids(assembly_steps, bom_to_mesh_mapping)
            
            print(f"\n :")
            print(f"   - : {len(assembly_steps)}")
            
            return {
                "success": True,
                "component_code": component_plan.get("component_code"),
                "component_name": component_name,
                "assembly_steps": assembly_steps,
                "raw_result": parsed
            }
        else:
            print(f"\n : {result.get('error')}")
            return {
                "success": False,
                "error": result.get("error"),
                "component_code": component_plan.get("component_code"),
                "component_name": component_name,
                "assembly_steps": []
            }
    
    def _add_mesh_ids(
        self,
        assembly_steps: List[Dict],
        bom_to_mesh_mapping: Dict
    ) -> List[Dict]:
        """
        mesh_id
        
        Args:
            assembly_steps: 
            bom_to_mesh_mapping: BOMmesh_id
            
        Returns:
            mesh_id
        """
        for step in assembly_steps:
            parts_used = step.get("parts_used", [])
            for part in parts_used:
                bom_code = part.get("bom_code", "")
                if bom_code in bom_to_mesh_mapping:
                    part["mesh_id"] = bom_to_mesh_mapping[bom_code]
        
        return assembly_steps

