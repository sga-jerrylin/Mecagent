# -*- coding: utf-8 -*-
"""
 V2.0
AgentJSON
"""

import json
from typing import Dict, List
from pathlib import Path


class ManualIntegratorV2:
    """ V2.0"""
    
    def __init__(self):
        """"""
        pass
    
    def integrate(
        self,
        planning_result: Dict,
        component_assembly_results: List[Dict],
        product_assembly_result: Dict,
        welding_result: Dict = None,
        safety_faq_result: Dict = None,
        bom_to_mesh_mapping: Dict = None,
        component_to_glb_mapping: Dict = None
    ) -> Dict:
        """
        Agent
        
        Args:
            planning_result: Agent 1
            component_assembly_results: Agent 3
            product_assembly_result: Agent 4
            welding_result: Agent 5
            safety_faq_result: Agent 6FAQ
            bom_to_mesh_mapping: BOMmesh_id
            component_to_glb_mapping: GLB
            
        Returns:
            JSON
        """
        print(f"\n{'='*80}")
        print(f"  V2.0 - ")
        print(f"{'='*80}")
        
        # 
        manual = {
            "metadata": self._build_metadata(planning_result),
            "component_assembly": self._build_component_assembly(
                component_assembly_results,
                component_to_glb_mapping
            ),
            "product_assembly": self._build_product_assembly(
                product_assembly_result
            ),
            "welding_requirements": self._build_welding(welding_result),
            "safety_and_faq": self._build_safety_faq(safety_faq_result),
            "3d_resources": self._build_3d_resources(
                bom_to_mesh_mapping,
                component_to_glb_mapping
            )
        }
        
        print(f"\n :")
        print(f"   - : {len(manual['component_assembly'])} ")
        print(f"   - : {len(manual['product_assembly']['steps'])} ")
        print(f"   - : {len(manual['welding_requirements'])} ")
        print(f"   - : {len(manual['safety_and_faq']['safety_warnings'])} ")
        print(f"   - FAQ: {len(manual['safety_and_faq']['faq_items'])} ")
        
        return manual
    
    def _build_metadata(self, planning_result: Dict) -> Dict:
        """"""
        product_plan = planning_result.get("product_assembly_plan", {})
        component_plans = planning_result.get("component_assembly_plan", [])
        
        return {
            "product_name": product_plan.get("product_name", ""),
            "total_components": len(component_plans),
            "base_component": {
                "code": product_plan.get("base_component_code", ""),
                "name": product_plan.get("base_component_name", "")
            },
            "generated_at": self._get_timestamp()
        }
    
    def _build_component_assembly(
        self,
        component_results: List[Dict],
        component_to_glb_mapping: Dict = None
    ) -> List[Dict]:
        """
        
        
        Args:
            component_results: 
            component_to_glb_mapping: GLB
            
        Returns:
            
        """
        chapters = []
        
        for result in component_results:
            if not result.get("success"):
                continue
            
            component_code = result.get("component_code", "")
            component_name = result.get("component_name", "")
            
            # GLB
            glb_file = None
            if component_to_glb_mapping and component_code in component_to_glb_mapping:
                glb_file = component_to_glb_mapping[component_code]
            
            chapter = {
                "chapter_type": "component_assembly",
                "component_code": component_code,
                "component_name": component_name,
                "glb_file": glb_file,  #  GLB
                "steps": result.get("assembly_steps", []),
                "3d_display_mode": "part_level_explosion"  # 
            }
            
            chapters.append(chapter)
        
        return chapters
    
    def _build_product_assembly(self, product_result: Dict) -> Dict:
        """
        
        
        Args:
            product_result: 
            
        Returns:
            
        """
        return {
            "chapter_type": "product_assembly",
            "product_name": product_result.get("product_name", ""),
            "glb_file": "product_total.glb",  #  GLB
            "steps": product_result.get("assembly_steps", []),
            "3d_display_mode": "component_level_explosion"  # 
        }
    
    def _build_welding(self, welding_result: Dict = None) -> List[Dict]:
        """"""
        if not welding_result or not welding_result.get("success"):
            return []
        
        return welding_result.get("welding_requirements", [])
    
    def _build_safety_faq(self, safety_faq_result: Dict = None) -> Dict:
        """FAQ"""
        if not safety_faq_result or not safety_faq_result.get("success"):
            return {
                "safety_warnings": [],
                "faq_items": []
            }
        
        return {
            "safety_warnings": safety_faq_result.get("safety_warnings", []),
            "faq_items": safety_faq_result.get("faq_items", [])
        }
    
    def _build_3d_resources(
        self,
        bom_to_mesh_mapping: Dict = None,
        component_to_glb_mapping: Dict = None
    ) -> Dict:
        """
        3D
        
        Args:
            bom_to_mesh_mapping: BOMmesh_id
            component_to_glb_mapping: GLB
            
        Returns:
            3D
        """
        return {
            "bom_to_mesh": bom_to_mesh_mapping or {},
            "component_to_glb": component_to_glb_mapping or {},
            "product_glb": "product_total.glb"
        }
    
    def _get_timestamp(self) -> str:
        """"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def save_to_file(self, manual: Dict, output_path: str):
        """
        
        
        Args:
            manual: 
            output_path: 
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(manual, f, ensure_ascii=False, indent=2)
        
        print(f"\n : {output_path}")

