# -*- coding: utf-8 -*-
"""
分层级的BOM-3D匹配器 V2
处理组件级别和产品级别的分开匹配
"""

from typing import Dict, List
from pathlib import Path
from processors.file_processor import ModelProcessor
from core.bom_3d_matcher import match_bom_to_3d
from utils.logger import print_step, print_substep, print_info, print_success, print_error, print_warning


class HierarchicalBOMMatcher:
    """分层级的BOM-3D匹配器"""
    
    def __init__(self):
        """初始化匹配器"""
        self.model_processor = ModelProcessor()
    
    def process_hierarchical_matching(
        self,
        step_dir: str,
        bom_data: List[Dict],
        component_plans: List[Dict],
        output_dir: str
    ) -> Dict:
        """
        分层级处理STEP文件和BOM匹配
        
        Args:
            step_dir: STEP文件目录
            bom_data: 完整的BOM数据
            component_plans: 组件规划列表（来自Agent 1）
            output_dir: GLB输出目录
            
        Returns:
            {
                "component_level_mappings": {...},  # 组件级别的映射
                "product_level_mapping": {...},     # 产品级别的映射
                "glb_files": {...}                  # 所有GLB文件路径
            }
        """
        print_step("分层级BOM-3D匹配")
        
        step_path = Path(step_dir)
        glb_output = Path(output_dir)
        glb_output.mkdir(parents=True, exist_ok=True)
        
        print_info(f"STEP文件目录: {step_dir}")
        print_info(f"GLB输出目录: {output_dir}")
        print_info(f"组件数量: {len(component_plans)}")
        
        # 结果容器
        component_level_mappings = {}
        product_level_mapping = {}
        glb_files = {}
        
        # ========== 1. 处理组件级别 ==========
        print_substep("步骤1：处理组件级别的STEP文件")
        
        for comp_plan in component_plans:
            comp_code = comp_plan.get("component_code", "")
            comp_name = comp_plan.get("component_name", "")
            comp_order = comp_plan.get("assembly_order", 0)
            
            print_info(f"\n处理组件{comp_order}: {comp_name}")
            
            # 查找对应的STEP文件
            step_file = step_path / f"组件图{comp_order}.STEP"
            if not step_file.exists():
                step_file = step_path / f"组件图{comp_order}.step"
            
            if not step_file.exists():
                print_warning(f"组件{comp_order}的STEP文件不存在", indent=1)
                continue
            
            print_info(f"STEP文件: {step_file.name}", indent=1)

            # 转换为GLB
            glb_file = glb_output / f"component_{comp_code.replace('.', '_')}.glb"
            print_info(f"开始转换STEP -> GLB: {glb_file.name}", indent=1)

            import sys
            sys.stdout.flush()

            convert_result = self.model_processor.step_to_glb(
                step_path=str(step_file),
                output_path=str(glb_file),
                scale_factor=0.001  # mm -> m
            )

            sys.stdout.flush()
            
            if not convert_result["success"]:
                print_error(f"GLB转换失败: {convert_result.get('error')}", indent=1)
                continue
            
            parts_list = convert_result.get("parts_info", [])
            print_success(f"GLB转换成功: {len(parts_list)} 个零件", indent=1)
            
            # 获取组件的BOM数据（只包含组件内部的零件）
            component_bom = self._get_component_bom(bom_data, comp_plan)
            print_info(f"组件BOM: {len(component_bom)} 个零件", indent=1)
            
            # BOM-3D匹配（双匹配策略：代码匹配 + AI跟进匹配）
            if parts_list and component_bom:
                # 步骤1：代码匹配
                code_matching_result = match_bom_to_3d(component_bom, parts_list)

                code_bom_to_mesh = code_matching_result.get("bom_to_mesh_mapping", {})
                code_summary = code_matching_result.get("summary", {})
                unmatched_parts = code_matching_result.get("unmatched_parts", [])

                code_bom_matched = code_summary.get('bom_matched_count', 0)
                total_bom = code_summary.get('total_bom_count', 0)

                print_success(f"代码匹配完成: BOM {code_bom_matched}/{total_bom} ({code_summary.get('matching_rate', 0)*100:.1f}%)", indent=1)

                # 步骤2：AI跟进匹配未匹配的零件
                ai_bom_to_mesh = {}
                ai_bom_matched_count = 0

                if unmatched_parts:
                    print_info(f"👷 AI匹配员工加入工作，他开始智能分析 {len(unmatched_parts)} 个未匹配的3D零件...", indent=1)
                    import sys
                    sys.stdout.flush()

                    # ✅ 计算未匹配的BOM（排除已经被代码匹配的BOM）
                    matched_bom_codes = set(code_bom_to_mesh.keys())
                    unmatched_bom = [bom for bom in component_bom if bom.get('code') not in matched_bom_codes]

                    from core.ai_matcher import AIBOMMatcher
                    ai_matcher = AIBOMMatcher()
                    ai_results = ai_matcher.match_unmatched_parts(unmatched_parts, unmatched_bom)

                    # 合并AI匹配结果到bom_to_mesh映射
                    for ai_result in ai_results:
                        bom_code = ai_result.get("matched_bom_code")
                        mesh_id = ai_result.get("mesh_id")
                        if bom_code and mesh_id:
                            if bom_code not in ai_bom_to_mesh:
                                ai_bom_to_mesh[bom_code] = []
                            ai_bom_to_mesh[bom_code].append(mesh_id)

                    # 计算AI新增匹配的BOM数量（不在代码匹配中的）
                    ai_bom_matched_count = len([k for k in ai_bom_to_mesh.keys() if k not in code_bom_to_mesh])

                    print_success(f"✅ AI匹配员工完成了工作，他新增匹配了 {ai_bom_matched_count} 个BOM", indent=1)
                    import sys
                    sys.stdout.flush()

                # 合并代码匹配和AI匹配的结果
                final_bom_to_mesh = {**code_bom_to_mesh, **ai_bom_to_mesh}
                total_bom_matched = len(final_bom_to_mesh)  # 最终匹配的BOM数量
                final_matching_rate = total_bom_matched / total_bom if total_bom else 0

                print_success(f"总匹配率: BOM {total_bom_matched}/{total_bom} ({final_matching_rate*100:.1f}%) [代码: {code_bom_matched}, AI: {ai_bom_matched_count}]", indent=1)

                # 保存组件级别的映射
                component_level_mappings[comp_code] = {
                    "component_name": comp_name,
                    "glb_file": str(glb_file),
                    "bom_to_mesh": final_bom_to_mesh,
                    "total_bom_count": total_bom,
                    "bom_matched_count": total_bom_matched,
                    "total_3d_parts": len(parts_list),
                    "code_matched": code_bom_matched,
                    "ai_matched": ai_bom_matched_count,
                    "matching_rate": final_matching_rate
                }

                glb_files[f"component_{comp_order}"] = str(glb_file)
            else:
                if not parts_list:
                    print_warning("没有提取到零件信息", indent=1)
                if not component_bom:
                    print_warning("没有组件BOM数据", indent=1)
        
        print_success(f"组件级别处理完成: {len(component_level_mappings)} 个组件")
        
        # ========== 2. 处理产品级别 ==========
        print_substep("步骤2：处理产品级别的STEP文件")
        
        # 查找产品总图的STEP文件
        product_step = step_path / "产品测试.STEP"
        if not product_step.exists():
            product_step = step_path / "产品总图.STEP"
        if not product_step.exists():
            product_step = step_path / "产品测试.step"
        if not product_step.exists():
            product_step = step_path / "产品总图.step"
        
        if product_step.exists():
            print_info(f"处理产品总图: {product_step.name}")
            
            # 转换为GLB
            product_glb = glb_output / "product_total.glb"
            convert_result = self.model_processor.step_to_glb(
                step_path=str(product_step),
                output_path=str(product_glb),
                scale_factor=0.001
            )
            
            if convert_result["success"]:
                parts_list = convert_result.get("parts_info", [])
                print_success(f"GLB转换成功: {len(parts_list)} 个零件", indent=1)
                
                # ✅ 产品级别的BOM数据（从产品总图PDF提取的零件）
                # ⚠️  排除组件：产品级3D模型中，组件是整体，不会有单独的零件名称
                product_bom_all = [
                    item for item in bom_data
                    if item.get("source_pdf", "").startswith("产品总图")
                ]

                # 筛选出真正的零件（排除组件）
                product_bom = [
                    item for item in product_bom_all
                    if '组件' not in item.get('name', '')
                ]

                component_count = len(product_bom_all) - len(product_bom)
                print(f"  产品BOM: {len(product_bom)} 个零件（排除了 {component_count} 个组件）", flush=True)
                
                # BOM-3D匹配（双匹配策略：代码匹配 + AI跟进匹配）
                # 步骤1：代码匹配
                code_matching_result = match_bom_to_3d(product_bom, parts_list)

                code_bom_to_mesh = code_matching_result.get("bom_to_mesh_mapping", {})
                code_summary = code_matching_result.get("summary", {})
                unmatched_parts = code_matching_result.get("unmatched_parts", [])

                code_bom_matched = code_summary.get('bom_matched_count', 0)
                total_bom = code_summary.get('total_bom_count', 0)

                print_success(f"代码匹配完成: BOM {code_bom_matched}/{total_bom} ({code_summary.get('matching_rate', 0)*100:.1f}%)", indent=1)

                # 步骤2：AI跟进匹配未匹配的零件
                ai_bom_to_mesh = {}
                ai_bom_matched_count = 0

                if unmatched_parts:
                    print_info(f"👷 AI匹配员工加入工作，他开始智能分析 {len(unmatched_parts)} 个未匹配的3D零件...", indent=1)
                    import sys
                    sys.stdout.flush()

                    # ✅ 计算未匹配的BOM（排除已经被代码匹配的BOM）
                    matched_bom_codes = set(code_bom_to_mesh.keys())
                    unmatched_bom = [bom for bom in product_bom if bom.get('code') not in matched_bom_codes]

                    from core.ai_matcher import AIBOMMatcher
                    ai_matcher = AIBOMMatcher()
                    ai_results = ai_matcher.match_unmatched_parts(unmatched_parts, unmatched_bom)

                    # 合并AI匹配结果到bom_to_mesh映射
                    for ai_result in ai_results:
                        bom_code = ai_result.get("matched_bom_code")
                        mesh_id = ai_result.get("mesh_id")
                        if bom_code and mesh_id:
                            if bom_code not in ai_bom_to_mesh:
                                ai_bom_to_mesh[bom_code] = []
                            ai_bom_to_mesh[bom_code].append(mesh_id)

                    # 计算AI新增匹配的BOM数量（不在代码匹配中的）
                    ai_bom_matched_count = len([k for k in ai_bom_to_mesh.keys() if k not in code_bom_to_mesh])

                    print_success(f"✅ AI匹配员工完成了工作，他新增匹配了 {ai_bom_matched_count} 个BOM", indent=1)
                    import sys
                    sys.stdout.flush()

                # 合并代码匹配和AI匹配的结果
                final_bom_to_mesh = {**code_bom_to_mesh, **ai_bom_to_mesh}
                total_bom_matched = len(final_bom_to_mesh)  # 最终匹配的BOM数量
                final_matching_rate = total_bom_matched / total_bom if total_bom else 0

                print_success(f"总匹配率: BOM {total_bom_matched}/{total_bom} ({final_matching_rate*100:.1f}%) [代码: {code_bom_matched}, AI: {ai_bom_matched_count}]", indent=1)

                product_level_mapping = {
                    "glb_file": str(product_glb),
                    "bom_to_mesh": final_bom_to_mesh,
                    "total_bom_count": total_bom,
                    "bom_matched_count": total_bom_matched,
                    "total_3d_parts": len(parts_list),
                    "code_matched": code_bom_matched,
                    "ai_matched": ai_bom_matched_count,
                    "matching_rate": final_matching_rate
                }

                glb_files["product_total"] = str(product_glb)
            else:
                print_error(f"GLB转换失败: {convert_result.get('error')}", indent=1)
        else:
            print_warning("未找到产品总图的STEP文件")
        
        # ========== 3. 汇总结果 ==========
        print_substep("分层级匹配汇总")
        print_info(f"组件级别: {len(component_level_mappings)} 个组件")
        for comp_code, mapping in component_level_mappings.items():
            print_info(f"  {comp_code}: BOM {mapping['bom_matched_count']}/{mapping['total_bom_count']} ({mapping['matching_rate']*100:.1f}%)", indent=1)

        if product_level_mapping:
            print_info(f"产品级别: BOM {product_level_mapping['bom_matched_count']}/{product_level_mapping['total_bom_count']} ({product_level_mapping['matching_rate']*100:.1f}%)")
        
        return {
            "success": True,
            "component_level_mappings": component_level_mappings,
            "product_level_mapping": product_level_mapping,
            "glb_files": glb_files
        }
    
    def _get_component_bom(self, bom_data: List[Dict], comp_plan: Dict) -> List[Dict]:
        """
        获取组件的BOM数据（只包含组件内部的零件）

        根据source_pdf字段来区分：
        - 组件图1.pdf -> 组件1的BOM
        - 组件图2.pdf -> 组件2的BOM
        - 组件图3.pdf -> 组件3的BOM

        Args:
            bom_data: 完整的BOM数据
            comp_plan: 组件规划（包含assembly_order）

        Returns:
            组件的BOM数据列表
        """
        # 获取组件序号
        comp_order = comp_plan.get("assembly_order", 0)

        # 根据source_pdf过滤BOM数据
        component_bom = []
        target_pdf = f"组件图{comp_order}.pdf"

        for bom_item in bom_data:
            source_pdf = bom_item.get("source_pdf", "")
            if source_pdf == target_pdf:
                component_bom.append(bom_item)

        return component_bom

