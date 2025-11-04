# -*- coding: utf-8 -*-
"""
分层级的BOM-3D匹配器 V2
处理组件级别和产品级别的分开匹配
"""

from typing import Dict, List
from pathlib import Path
from processors.file_processor import ModelProcessor
from core.bom_3d_matcher import match_bom_to_3d  # ✅ 使用完整版的匹配函数

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
            
            # 查找对应的STEP文件（支持多种命名方式）
            step_file = None
            possible_names = [
                f"组件图{comp_order}.STEP",
                f"组件图{comp_order}.step",
                f"组件{comp_order}.STEP",
                f"组件{comp_order}.step",
                f"组件图{comp_order}.stp",
                f"组件{comp_order}.stp"
            ]

            for name in possible_names:
                candidate = step_path / name
                if candidate.exists():
                    step_file = candidate
                    break

            if not step_file:
                print_warning(f"组件{comp_order}的STEP文件不存在（尝试了: {', '.join(possible_names)}）", indent=1)
                continue
            
            print_info(f"STEP文件: {step_file.name}", indent=1)

            # 转换为GLB（使用序号而不是BOM代号，确保前端能通过序号找到对应的GLB）
            glb_file = glb_output / f"component_{comp_order}.glb"
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
                total_parts = code_summary.get('total_3d_parts', 0)

                # ✅ AI匹配所有零件
                print_info(f"🤖 AI匹配员工开始工作，分析 {len(component_bom)} 个BOM和 {len(parts_list)} 个3D零件", indent=1)
                ai_bom_to_mesh = {}
                ai_bom_matched_count = 0

                if unmatched_parts:
                    import sys
                    sys.stdout.flush()

                    # ✅ 计算未匹配的BOM（排除已经被代码匹配的BOM）
                    matched_bom_codes = set(code_bom_to_mesh.keys())
                    unmatched_bom = [bom for bom in component_bom if bom.get('code') not in matched_bom_codes]

                    from core.ai_matcher import AIBOMMatcher
                    ai_matcher = AIBOMMatcher()
                    ai_results = ai_matcher.match_unmatched_parts(unmatched_parts, unmatched_bom)

                    # ✅ 将AI匹配结果应用到cleaned_parts（更新bom_code）
                    cleaned_parts = code_matching_result.get("cleaned_parts", [])
                    for ai_result in ai_results:
                        bom_code = ai_result.get("matched_bom_code")
                        node_name = ai_result.get("node_name")

                        if bom_code and node_name:
                            # 找到对应的零件并更新bom_code
                            for part in cleaned_parts:
                                if part.get("node_name") == node_name and not part.get("bom_code"):
                                    part["bom_code"] = bom_code
                                    part["match_method"] = "AI匹配"
                                    part["confidence"] = ai_result.get("confidence", 0.0)
                                    break

                            # 同时更新ai_bom_to_mesh映射（用于统计）
                            if bom_code not in ai_bom_to_mesh:
                                ai_bom_to_mesh[bom_code] = []
                            ai_bom_to_mesh[bom_code].append(node_name)

                    # 计算AI新增匹配的BOM数量（不在代码匹配中的）
                    ai_bom_matched_count = len([k for k in ai_bom_to_mesh.keys() if k not in code_bom_to_mesh])

                # ✅ 合并匹配结果
                final_bom_to_mesh = {**code_bom_to_mesh, **ai_bom_to_mesh}
                total_bom_matched = len(final_bom_to_mesh)
                final_bom_rate = total_bom_matched / total_bom if total_bom else 0

                # 计算最终的3D零件匹配数
                final_parts_matched = sum(len(meshes) for meshes in final_bom_to_mesh.values())
                final_parts_rate = final_parts_matched / total_parts if total_parts else 0

                print_success(f"✅ AI匹配完成:", indent=1)
                print_info(f"  📋 BOM匹配率: {total_bom_matched}/{total_bom} ({final_bom_rate*100:.1f}%)", indent=1)
                print_info(f"  🎨 3D零件覆盖率: {final_parts_matched}/{total_parts} ({final_parts_rate*100:.1f}%)", indent=1)

                # ✅ 列出未匹配的BOM
                if total_bom_matched < total_bom:
                    unmatched_bom_codes = [bom.get('code') for bom in component_bom if bom.get('code') not in final_bom_to_mesh]
                    print_warning(f"  ⚠️  未匹配的BOM ({len(unmatched_bom_codes)}个): {', '.join(unmatched_bom_codes[:5])}", indent=1)

                import sys
                sys.stdout.flush()

                # ✅ 重新生成BOM映射宽表（使用更新后的cleaned_parts）
                from core.bom_3d_matcher import BOM3DMatcher
                matcher = BOM3DMatcher()
                bom_mapping_table = matcher.generate_bom_mapping_table(component_bom, cleaned_parts)

                # 保存组件级别的映射
                component_level_mappings[comp_code] = {
                    "component_name": comp_name,
                    "glb_file": str(glb_file),
                    "bom_to_mesh": final_bom_to_mesh,
                    "bom_mapping_table": bom_mapping_table,  # ✅ 新增：保存BOM映射宽表
                    "total_bom_count": total_bom,
                    "bom_matched_count": total_bom_matched,
                    "bom_matching_rate": final_bom_rate,  # ✅ BOM匹配率
                    "total_3d_parts": total_parts,
                    "matched_3d_count": final_parts_matched,  # ✅ 匹配的3D零件数
                    "parts_matching_rate": final_parts_rate,  # ✅ 3D零件匹配率
                    "code_matched": code_bom_matched,
                    "ai_matched": ai_bom_matched_count,
                    "matching_rate": final_bom_rate  # ✅ 兼容旧代码
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
        # 尝试多种可能的产品STEP文件名
        possible_product_names = [
            "产品测试.STEP",
            "产品总图.STEP",
            "产品主图.STEP",  # ✅ 新增
            "产品测试.step",
            "产品总图.step",
            "产品主图.step",  # ✅ 新增
            "产品测试.stp",
            "产品总图.stp",
            "产品主图.stp",   # ✅ 新增
        ]

        product_step = None
        for name in possible_product_names:
            candidate = step_path / name
            if candidate.exists():
                product_step = candidate
                break

        if product_step and product_step.exists():
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
                # ✅ 修改：不排除组件，组件的零件也要参与匹配
                product_bom_all = [
                    item for item in bom_data
                    if item.get("source_pdf", "").startswith("产品总图")
                ]

                # ✅ 新策略：包含所有BOM项（组件+零件）
                # 原因：产品总装步骤需要高亮组件内的零件，所以组件的零件也要参与匹配
                product_bom = product_bom_all

                print(f"  产品BOM: {len(product_bom)} 个项（包含组件和零件）", flush=True)
                
                # BOM-3D匹配（双匹配策略：代码匹配 + AI跟进匹配）
                # 步骤1：代码匹配
                code_matching_result = match_bom_to_3d(product_bom, parts_list)

                code_bom_to_mesh = code_matching_result.get("bom_to_mesh_mapping", {})
                code_summary = code_matching_result.get("summary", {})
                unmatched_parts = code_matching_result.get("unmatched_parts", [])

                code_bom_matched = code_summary.get('bom_matched_count', 0)
                total_bom = code_summary.get('total_bom_count', 0)
                total_parts = code_summary.get('total_3d_parts', 0)

                # ✅ AI匹配所有零件
                print_info(f"🤖 AI匹配员工开始工作，分析 {len(product_bom)} 个BOM和 {len(parts_list)} 个3D零件", indent=1)
                ai_bom_to_mesh = {}
                ai_bom_matched_count = 0

                if unmatched_parts:
                    import sys
                    sys.stdout.flush()

                    # ✅ 计算未匹配的BOM（排除已经被代码匹配的BOM）
                    matched_bom_codes = set(code_bom_to_mesh.keys())
                    unmatched_bom = [bom for bom in product_bom if bom.get('code') not in matched_bom_codes]

                    from core.ai_matcher import AIBOMMatcher
                    ai_matcher = AIBOMMatcher()
                    ai_results = ai_matcher.match_unmatched_parts(unmatched_parts, unmatched_bom)

                    # ✅ 将AI匹配结果应用到cleaned_parts（更新bom_code）
                    cleaned_parts = code_matching_result.get("cleaned_parts", [])
                    for ai_result in ai_results:
                        bom_code = ai_result.get("matched_bom_code")
                        node_name = ai_result.get("node_name")

                        if bom_code and node_name:
                            # 找到对应的零件并更新bom_code
                            for part in cleaned_parts:
                                if part.get("node_name") == node_name and not part.get("bom_code"):
                                    part["bom_code"] = bom_code
                                    part["match_method"] = "AI匹配"
                                    part["confidence"] = ai_result.get("confidence", 0.0)
                                    break

                            # 同时更新ai_bom_to_mesh映射（用于统计）
                            if bom_code not in ai_bom_to_mesh:
                                ai_bom_to_mesh[bom_code] = []
                            ai_bom_to_mesh[bom_code].append(node_name)

                    # 计算AI新增匹配的BOM数量（不在代码匹配中的）
                    ai_bom_matched_count = len([k for k in ai_bom_to_mesh.keys() if k not in code_bom_to_mesh])

                # ✅ 合并匹配结果
                final_bom_to_mesh = {**code_bom_to_mesh, **ai_bom_to_mesh}
                total_bom_matched = len(final_bom_to_mesh)
                final_bom_rate = total_bom_matched / total_bom if total_bom else 0

                # 计算最终的3D零件匹配数
                final_parts_matched = sum(len(meshes) for meshes in final_bom_to_mesh.values())
                final_parts_rate = final_parts_matched / total_parts if total_parts else 0

                print_success(f"✅ AI匹配完成:", indent=1)
                print_info(f"  📋 BOM匹配率: {total_bom_matched}/{total_bom} ({final_bom_rate*100:.1f}%)", indent=1)
                print_info(f"  🎨 3D零件覆盖率: {final_parts_matched}/{total_parts} ({final_parts_rate*100:.1f}%)", indent=1)

                # ✅ 列出未匹配的BOM
                if total_bom_matched < total_bom:
                    unmatched_bom_codes = [bom.get('code') for bom in product_bom if bom.get('code') not in final_bom_to_mesh]
                    print_warning(f"  ⚠️  未匹配的BOM ({len(unmatched_bom_codes)}个): {', '.join(unmatched_bom_codes[:5])}", indent=1)

                import sys
                sys.stdout.flush()

                # ✅ 重新生成BOM映射宽表（使用更新后的cleaned_parts）
                from core.bom_3d_matcher import BOM3DMatcher
                matcher = BOM3DMatcher()
                product_bom_mapping_table = matcher.generate_bom_mapping_table(product_bom, cleaned_parts)

                product_level_mapping = {
                    "glb_file": str(product_glb),
                    "bom_to_mesh": final_bom_to_mesh,
                    "bom_mapping_table": product_bom_mapping_table,  # ✅ 新增：保存BOM映射宽表
                    "total_bom_count": total_bom,
                    "bom_matched_count": total_bom_matched,
                    "bom_matching_rate": final_bom_rate,  # ✅ BOM匹配率
                    "total_3d_parts": total_parts,
                    "matched_3d_count": final_parts_matched,  # ✅ 匹配的3D零件数
                    "parts_matching_rate": final_parts_rate,  # ✅ 3D零件匹配率
                    "code_matched": code_bom_matched,
                    "ai_matched": ai_bom_matched_count,
                    "matching_rate": final_bom_rate  # ✅ 兼容旧代码
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
        comp_name = comp_plan.get("component_name", "")

        # 根据source_pdf过滤BOM数据（支持多种命名方式）
        component_bom = []

        # 可能的文件名格式（不区分大小写）
        possible_names = [
            f"组件图{comp_order}.pdf",
            f"组件图{comp_order}.PDF",
            f"组件{comp_order}.pdf",
            f"组件{comp_order}.PDF"
        ]

        # ✅ 调试日志：打印查找信息
        print_info(f"🔍 查找组件{comp_order}({comp_name})的BOM数据", indent=1)
        print_info(f"   可能的文件名: {', '.join(possible_names)}", indent=1)

        # 统计所有source_pdf
        all_source_pdfs = set()
        for bom_item in bom_data:
            source_pdf = bom_item.get("source_pdf", "")
            all_source_pdfs.add(source_pdf)
            # 不区分大小写匹配
            if source_pdf in possible_names:
                component_bom.append(bom_item)

        print_info(f"   BOM数据中的所有source_pdf: {', '.join(sorted(all_source_pdfs))}", indent=1)
        print_info(f"   匹配到的BOM数量: {len(component_bom)}", indent=1)

        return component_bom

