# -*- coding: utf-8 -*-
"""
Gemini 6-Agent工作流（生产级）
基于Gemini 2.5 Flash的装配说明书自动生成系统

架构说明：
- 支路1（PDF处理）：文件分类 → BOM提取 → Agent 1视觉规划
- 支路2（3D处理）：STEP转GLB → Agent 2 BOM-3D匹配
- 主线路：Agent 3组件装配 → Agent 4产品总装 → Agent 5焊接 → Agent 6安全FAQ → 整合输出

复用的Core组件：
- file_classifier.py - 文件分类
- hierarchical_bom_matcher_v2.py - 分层级BOM-3D匹配
- manual_integrator_v2.py - 手册整合
"""

import os
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# 添加项目根目录到路径
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Windows平台设置UTF-8编码（支持emoji显示）
if sys.platform == 'win32':
    import io
    # 强制设置stdout和stderr为UTF-8编码
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    os.environ['PYTHONIOENCODING'] = 'utf-8'

# 复用Core组件
from core.file_classifier import FileClassifier
from core.hierarchical_bom_matcher_v2 import HierarchicalBOMMatcher
from core.manual_integrator_v2 import ManualIntegratorV2

# 6个Gemini Agent
from agents.vision_planning_agent import VisionPlanningAgent
from agents.component_assembly_agent import ComponentAssemblyAgent
from agents.product_assembly_agent import ProductAssemblyAgent
from agents.welding_agent import WeldingAgent
from agents.safety_faq_agent import SafetyFAQAgent

# 日志工具
from utils.logger import (
    print_step, print_substep, print_info,
    print_success, print_error, print_warning
)


class GeminiAssemblyPipeline:
    """基于Gemini 2.5 Flash的6-Agent装配说明书生成工作流"""
    
    def __init__(self, api_key: str, output_dir: str = "pipeline_output"):
        """
        初始化工作流
        
        Args:
            api_key: OpenRouter API密钥
            output_dir: 输出目录
        """
        self.api_key = api_key
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 设置API密钥
        os.environ["OPENROUTER_API_KEY"] = api_key
        
        # 初始化复用的Core组件
        self.file_classifier = FileClassifier()
        self.bom_matcher = HierarchicalBOMMatcher()
        self.integrator = ManualIntegratorV2()
        
        # 初始化6个Agent
        self.vision_agent = VisionPlanningAgent()
        self.component_agent = ComponentAssemblyAgent()
        self.product_agent = ProductAssemblyAgent()
        self.welding_agent = WeldingAgent()
        self.safety_agent = SafetyFAQAgent()
        
        # 工作流状态
        self.start_time = None
        self.current_step = 0
        self.total_steps = 8
        
    def log_agent_call(self, agent_name: str, action: str, status: str = "running"):
        """记录Agent调用日志（生动的AI员工工作描述）"""
        timestamp = datetime.now().strftime("%H:%M:%S")

        if status == "running":
            print_info(f"[{timestamp}] 👷 {agent_name}AI员工加入工作，他开始{action}...")
            import sys
            sys.stdout.flush()  # 强制刷新输出
        elif status == "success":
            print_success(f"[{timestamp}] ✅ {agent_name}AI员工完成了工作，他{action}", indent=1)
            import sys
            sys.stdout.flush()
        elif status == "error":
            print_error(f"[{timestamp}] ❌ {agent_name}AI员工遇到了问题，{action}失败了", indent=1)
            import sys
            sys.stdout.flush()
    
    def run(self, pdf_dir: str, step_dir: str) -> Dict:
        """
        运行完整的工作流

        Args:
            pdf_dir: PDF文件目录
            step_dir: STEP文件目录

        Returns:
            工作流结果字典
        """
        self.start_time = time.time()

        print_step("🚀 Gemini 6-Agent装配说明书生成工作流启动")
        print_info(f"📁 输出目录: {self.output_dir}")
        print_info(f"📋 总步骤数: {self.total_steps}")
        print_info("")

        try:
            # ========== 支路1: PDF处理 ==========
            # 步骤1: 文件分类 + PDF转图片
            self.current_step = 1
            file_hierarchy, image_hierarchy = self._step1_classify_and_convert(pdf_dir)

            # 步骤2: 从PDF提取BOM数据
            self.current_step = 2
            bom_data = self._step2_extract_bom_from_pdfs(file_hierarchy)

            # 步骤3: Agent 1 - 视觉规划
            self.current_step = 3
            planning_result = self._step3_vision_planning(image_hierarchy, bom_data)
            
            # ========== 支路2: 3D处理 ==========
            # 步骤4: Agent 2 - BOM-3D匹配
            self.current_step = 4
            matching_result = self._step4_bom_3d_matching(
                step_dir, bom_data, planning_result
            )
            
            # ========== 主线路: Agent 3-6 ==========
            # 步骤5: Agent 3 - 组件装配（可复用）
            self.current_step = 5
            component_results = self._step5_component_assembly(
                file_hierarchy, image_hierarchy, planning_result, matching_result
            )
            
            # 步骤6: Agent 4 - 产品总装
            self.current_step = 6
            product_result = self._step6_product_assembly(
                file_hierarchy, image_hierarchy, planning_result, matching_result
            )

            # 步骤7: Agent 5 & 6 - 焊接和安全（增强装配步骤）
            self.current_step = 7
            enhanced_component_results, enhanced_product_result = self._step7_welding_and_safety(
                file_hierarchy, image_hierarchy, component_results, product_result
            )

            # 步骤8: 整合最终手册
            self.current_step = 8
            final_manual = self._step8_integrate_manual(
                planning_result, enhanced_component_results, enhanced_product_result,
                matching_result
            )
            
            # 计算总耗时
            elapsed_time = time.time() - self.start_time
            
            print_step("🎉 工作流完成")
            print_success(f"⏱️  总耗时: {elapsed_time:.1f}秒")
            print_success(f"📄 输出文件: {self.output_dir / 'assembly_manual.json'}")
            
            return {
                "success": True,
                "output_file": str(self.output_dir / "assembly_manual.json"),
                "elapsed_time": elapsed_time,
                "manual": final_manual
            }
            
        except Exception as e:
            print_error(f"工作流失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e)
            }
    
    def _step1_classify_and_convert(self, pdf_dir: str) -> tuple:
        """步骤1: 文件分类 + PDF转图片"""
        print_substep(f"[{self.current_step}/{self.total_steps}] 📂 文件管理员")

        self.log_agent_call("文件管理", "查看文件夹里有哪些图纸", "running")

        pdf_path = Path(pdf_dir)
        pdf_files = [str(f) for f in pdf_path.glob("*.pdf")]

        print_info(f"📄 他发现了 {len(pdf_files)} 个PDF图纸", indent=1)
        import sys
        sys.stdout.flush()

        self.log_agent_call("文件管理", "分辨哪些是产品总图，哪些是组件图", "running")
        file_hierarchy = self.file_classifier.classify_files(pdf_files)

        product_name = Path(file_hierarchy['product']['pdf']).name if file_hierarchy['product'] else 'N/A'
        print_success(f"📋 他找到了产品总图: {product_name}", indent=1)
        print_success(f"🔧 他找到了 {len(file_hierarchy['components'])} 个组件图:", indent=1)

        for comp in file_hierarchy['components']:
            print_info(f"   • {comp['name']} (代号: {comp['bom_code']})", indent=2)

        sys.stdout.flush()

        # PDF转图片
        self.log_agent_call("文件管理", "把PDF转换成图片（AI需要看图片）", "running")

        images_dir = self.output_dir / "pdf_images"
        image_hierarchy = self.file_classifier.convert_pdfs_to_images(
            file_hierarchy=file_hierarchy,
            output_base_dir=str(images_dir),
            dpi=200  # 降低DPI加快速度
        )

        total_images = len(image_hierarchy.get("product_images", []))
        for comp_images in image_hierarchy.get("component_images", {}).values():
            total_images += len(comp_images)

        print_success(f"🖼️  他转换了 {total_images} 张图片", indent=1)
        sys.stdout.flush()

        self.log_agent_call("文件管理", "整理好了所有图纸和图片", "success")

        # 保存结果
        with open(self.output_dir / "step1_file_hierarchy.json", "w", encoding="utf-8") as f:
            json.dump(file_hierarchy, f, ensure_ascii=False, indent=2)

        with open(self.output_dir / "step1_image_hierarchy.json", "w", encoding="utf-8") as f:
            json.dump(image_hierarchy, f, ensure_ascii=False, indent=2)

        return file_hierarchy, image_hierarchy
    
    def _step2_extract_bom_from_pdfs(self, file_hierarchy: Dict) -> List[Dict]:
        """步骤2: 从PDF提取BOM数据"""
        print_substep(f"[{self.current_step}/{self.total_steps}] 📊 BOM数据分析员")

        self.log_agent_call("BOM分析", "从图纸中读取零件清单", "running")

        from pypdf import PdfReader
        import re

        all_bom_items = []
        seen_codes = set()

        # 收集所有PDF文件
        all_pdfs = []
        if file_hierarchy['product']:
            all_pdfs.append(file_hierarchy['product']['pdf'])
        for comp in file_hierarchy['components']:
            all_pdfs.append(comp['pdf'])

        print_info(f"📄 他准备从 {len(all_pdfs)} 个图纸中提取零件信息", indent=1)
        import sys
        sys.stdout.flush()

        # 统计每个PDF的BOM数量
        pdf_bom_counts = {}

        # 从每个PDF提取BOM
        for pdf_path in all_pdfs:
            pdf_name = Path(pdf_path).name
            print_info(f"   📖 正在阅读: {pdf_name}", indent=1)
            sys.stdout.flush()

            pdf_bom_count = 0

            try:
                reader = PdfReader(pdf_path)
                all_text = ""
                for page in reader.pages:
                    all_text += page.extract_text() + "\n"

                lines = all_text.split('\n')

                for line in lines:
                    if not line.strip() or '序号' in line or '物料代码' in line:
                        continue

                    parts = line.split()
                    if len(parts) < 4:
                        continue

                    # 第一个应该是序号
                    try:
                        seq = int(parts[0])
                        if not (1 <= seq <= 200):
                            continue
                    except:
                        continue

                    # 查找BOM代号
                    code = None
                    code_idx = -1
                    for j, part in enumerate(parts[1:], 1):
                        if re.match(r'^\d{2}\.\d{2}\.', part):
                            code = part
                            code_idx = j
                            break

                    if not code or code in seen_codes:
                        continue
                    seen_codes.add(code)

                    # 提取产品代号
                    product_code = ""
                    if code_idx + 1 < len(parts):
                        next_part = parts[code_idx + 1]
                        if any(c in next_part for c in ['-', '*', 'φ', 'Φ', 'M', 'T-']):
                            product_code = next_part

                    # 提取名称
                    name_start_idx = code_idx + 2 if product_code else code_idx + 1
                    name_parts = []
                    for j in range(name_start_idx, len(parts) - 2):
                        name_parts.append(parts[j])
                    name = ' '.join(name_parts) if name_parts else "未知"

                    # 提取数量和重量
                    try:
                        qty = int(parts[-2])
                        weight = float(parts[-1])
                    except:
                        try:
                            qty = int(parts[-3])
                            weight = float(parts[-1])
                        except:
                            continue

                    all_bom_items.append({
                        "seq": str(seq),
                        "code": code,
                        "product_code": product_code,
                        "name": name,
                        "quantity": qty,
                        "weight": weight,
                        "source_pdf": pdf_name
                    })

                    pdf_bom_count += 1

                # 记录这个PDF的BOM数量
                pdf_bom_counts[pdf_name] = pdf_bom_count
                print_success(f"      提取到 {pdf_bom_count} 个零件", indent=1)
                sys.stdout.flush()

            except Exception as e:
                print_warning(f"   ⚠️  {pdf_name} 读取失败: {e}", indent=1)
                sys.stdout.flush()

        # 显示详细统计
        print_success(f"📦 他整理出了 {len(all_bom_items)} 个零件的信息", indent=1)
        print_info(f"   详细统计:", indent=1)
        for pdf_name, count in pdf_bom_counts.items():
            print_info(f"      • {pdf_name}: {count} 个零件", indent=1)
        sys.stdout.flush()

        self.log_agent_call("BOM分析", "生成了完整的零件清单", "success")

        # 保存结果
        with open(self.output_dir / "step2_bom_data.json", "w", encoding="utf-8") as f:
            json.dump(all_bom_items, f, ensure_ascii=False, indent=2)

        return all_bom_items

    def _step3_vision_planning(self, image_hierarchy: Dict, bom_data: List[Dict]) -> Dict:
        """步骤3: Agent 1 - 视觉规划"""
        print_substep(f"[{self.current_step}/{self.total_steps}] 🔍 装配规划师")

        self.log_agent_call("装配规划", "研究图纸，规划装配顺序", "running")

        # 收集所有图片
        all_images = []
        all_images.extend(image_hierarchy.get("product_images", []))
        for comp_images in image_hierarchy.get("component_images", {}).values():
            all_images.extend(comp_images)

        print_info(f"🖼️  他拿到了 {len(all_images)} 张图片", indent=1)
        print_info(f"📊 他参考了 {len(bom_data)} 个零件的信息", indent=1)
        import sys
        sys.stdout.flush()

        self.log_agent_call("装配规划", "使用AI视觉分析图纸", "running")

        planning_result = self.vision_agent.process(all_images, bom_data)

        if planning_result["success"]:
            component_count = len(planning_result.get("component_assembly_plan", []))
            print_success(f"🎯 他识别出了 {component_count} 个组件", indent=1)
            print_success(f"📋 他制定了装配顺序方案", indent=1)
            sys.stdout.flush()
            self.log_agent_call("装配规划", "完成了装配规划方案", "success")
        else:
            self.log_agent_call("装配规划", "规划", "error")
            raise Exception(f"装配规划失败: {planning_result.get('error')}")

        # 保存结果
        with open(self.output_dir / "step3_planning_result.json", "w", encoding="utf-8") as f:
            json.dump(planning_result, f, ensure_ascii=False, indent=2)

        return planning_result

    def _step4_bom_3d_matching(
        self, step_dir: str, bom_data: List[Dict], planning_result: Dict
    ) -> Dict:
        """步骤4: Agent 2 - BOM-3D匹配"""
        print_substep(f"[{self.current_step}/{self.total_steps}] 🎨 3D模型工程师")

        self.log_agent_call("3D模型", "将STEP文件转换成网页能看的GLB格式", "running")

        component_plans = planning_result.get("component_assembly_plan", [])

        import sys
        sys.stdout.flush()

        self.log_agent_call("3D模型", "把零件清单和3D模型对应起来", "running")

        matching_result = self.bom_matcher.process_hierarchical_matching(
            step_dir=step_dir,
            bom_data=bom_data,
            component_plans=component_plans,
            output_dir=str(self.output_dir / "glb_files")
        )

        if matching_result["success"]:
            comp_count = len(matching_result.get("component_level_mappings", {}))
            print_success(f"🔧 他处理了 {comp_count} 个组件的3D模型", indent=1)

            if matching_result.get("product_level_mapping"):
                print_success("📦 他完成了产品总装的3D模型", indent=1)

            sys.stdout.flush()
            self.log_agent_call("3D模型", "生成了所有3D模型和零件的对应关系", "success")
        else:
            self.log_agent_call("3D模型", "3D模型处理", "error")

        # 保存结果
        with open(self.output_dir / "step4_matching_result.json", "w", encoding="utf-8") as f:
            json.dump(matching_result, f, ensure_ascii=False, indent=2)

        return matching_result

    def _step5_component_assembly(
        self, file_hierarchy: Dict, image_hierarchy: Dict, planning_result: Dict, matching_result: Dict
    ) -> List[Dict]:
        """步骤5: Agent 3 - 组件装配"""
        print_substep(f"[{self.current_step}/{self.total_steps}] 🔨 组件装配工程师")

        component_plans = planning_result.get("component_assembly_plan", [])
        component_level_mappings = matching_result.get("component_level_mappings", {})

        # ✅ 读取BOM数据
        bom_data = []
        bom_file = self.output_dir / "step2_bom_data.json"
        if bom_file.exists():
            import json
            with open(bom_file, 'r', encoding='utf-8') as f:
                bom_data = json.load(f)

        component_results = []

        import sys

        for i, comp_plan in enumerate(component_plans, 1):
            comp_code = comp_plan.get("component_code", "")
            comp_name = comp_plan.get("component_name", "")

            self.log_agent_call(
                f"组件装配工 #{i}",
                f"编写【{comp_name}】的装配步骤",
                "running"
            )
            sys.stdout.flush()

            # ✅ 获取组件的图纸（通过assembly_order匹配）
            comp_order = comp_plan.get("assembly_order", 0)
            component_images = image_hierarchy.get('component_images', {}).get(str(comp_order), [])

            if not component_images:
                print_warning(f"未找到组件{comp_code}的图片", indent=1)
                continue

            # ✅ 获取组件的BOM列表（从BOM数据中筛选）
            # 通过source_pdf匹配（如"组件图1.pdf"）
            comp_pdf_name = f"组件图{comp_order}.pdf"
            component_bom = [
                item for item in bom_data
                if item.get("source_pdf", "").startswith(comp_pdf_name.replace(".pdf", ""))
            ]

            # 获取组件的BOM-3D映射
            bom_to_mesh = None
            if comp_code in component_level_mappings:
                bom_to_mesh = component_level_mappings[comp_code].get("bom_to_mesh", {})

            # 调用Agent 3
            print_info(f"   📖 他正在研究【{comp_name}】的图纸", indent=1)
            print_info(f"   📋 组件BOM: {len(component_bom)} 个零件", indent=1)
            sys.stdout.flush()

            result = self.component_agent.process(
                component_plan=comp_plan,
                component_images=component_images,
                parts_list=component_bom,  # ✅ 传入组件的BOM列表
                bom_to_mesh_mapping=bom_to_mesh
            )

            if result["success"]:
                step_count = len(result.get("assembly_steps", []))

                # ✅ 验证BOM覆盖率
                assembly_steps = result.get("assembly_steps", [])
                used_bom_codes = set()
                for step in assembly_steps:
                    parts_used = step.get("parts_used", [])
                    for part in parts_used:
                        if isinstance(part, dict):
                            bom_code = part.get("bom_code")
                            if bom_code:
                                used_bom_codes.add(bom_code)

                bom_coverage = len(used_bom_codes) / len(component_bom) * 100 if component_bom else 0

                print_success(f"   ✅ 生成了 {step_count} 个装配步骤", indent=1)
                print_info(f"   📋 BOM覆盖率: {len(used_bom_codes)}/{len(component_bom)} ({bom_coverage:.1f}%)", indent=1)

                if bom_coverage < 100:
                    print_warning(f"   ⚠️  有 {len(component_bom) - len(used_bom_codes)} 个BOM未覆盖", indent=1)

                sys.stdout.flush()
                self.log_agent_call(f"组件装配工 #{i}", f"完成了【{comp_name}】的装配说明", "success")
            else:
                self.log_agent_call(f"组件装配工 #{i}", "装配步骤编写", "error")

            # ✅ 添加组件代号和装配顺序到结果中（供Agent 5和Agent 6使用）
            result["component_code"] = comp_code
            result["component_name"] = comp_name
            result["assembly_order"] = comp_order

            component_results.append(result)

        # 保存结果
        with open(self.output_dir / "step5_component_results.json", "w", encoding="utf-8") as f:
            json.dump(component_results, f, ensure_ascii=False, indent=2)

        return component_results

    def _step6_product_assembly(
        self, file_hierarchy: Dict, image_hierarchy: Dict, planning_result: Dict, matching_result: Dict
    ) -> Dict:
        """步骤6: Agent 4 - 产品总装"""
        print_substep(f"[{self.current_step}/{self.total_steps}] 🏗️ 产品总装工程师")

        self.log_agent_call("产品总装", "规划如何把组件组装成最终产品", "running")

        # ✅ 使用图片而不是PDF
        product_images = image_hierarchy.get('product_images', [])

        if not product_images:
            print_warning("⚠️  没有找到产品总图图片", indent=1)
            return {"success": False, "error": "No product images"}

        # ✅ 读取产品级BOM数据
        bom_data = []
        bom_file = self.output_dir / "step2_bom_data.json"
        if bom_file.exists():
            import json
            with open(bom_file, 'r', encoding='utf-8') as f:
                bom_data = json.load(f)

        # ✅ 筛选产品级BOM（从产品总图提取的零件）
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

        # ✅ 获取产品级BOM-3D映射
        product_bom_to_mesh = matching_result.get("product_level_mapping", {}).get("bom_to_mesh", {})

        import sys
        print_info(f"📋 他正在研究产品总图", indent=1)
        print_info(f"📋 产品级BOM: {len(product_bom)} 个零件", indent=1)
        sys.stdout.flush()

        result = self.product_agent.process(
            product_plan=planning_result,
            product_images=product_images,
            components_list=planning_result.get("component_assembly_plan", []),
            product_bom=product_bom,  # ✅ 传入产品级BOM
            bom_to_mesh_mapping=product_bom_to_mesh  # ✅ 传入BOM-3D映射
        )

        if result["success"]:
            step_count = len(result.get("assembly_steps", []))

            # ✅ 验证产品级BOM覆盖率（从fasteners字段）
            assembly_steps = result.get("assembly_steps", [])
            used_bom_codes = set()
            for step in assembly_steps:
                fasteners = step.get("fasteners", [])
                for fastener in fasteners:
                    if isinstance(fastener, dict):
                        bom_code = fastener.get("bom_code")
                        if bom_code:
                            used_bom_codes.add(bom_code)

            bom_coverage = len(used_bom_codes) / len(product_bom) * 100 if product_bom else 0

            print_success(f"✅ 生成了 {step_count} 个总装步骤", indent=1)
            print_info(f"📋 产品级BOM覆盖率: {len(used_bom_codes)}/{len(product_bom)} ({bom_coverage:.1f}%)", indent=1)

            if bom_coverage < 100:
                print_warning(f"⚠️  有 {len(product_bom) - len(used_bom_codes)} 个产品级BOM未覆盖", indent=1)

            sys.stdout.flush()
            self.log_agent_call("产品总装", "完成了产品总装说明", "success")
        else:
            self.log_agent_call("产品总装", "总装步骤编写", "error")

        # 保存结果
        with open(self.output_dir / "step6_product_result.json", "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        return result

    def _step7_welding_and_safety(
        self, file_hierarchy: Dict, image_hierarchy: Dict, component_results: List[Dict], product_result: Dict
    ) -> tuple:
        """
        步骤7: Agent 5 & 6 - 焊接和安全

        新逻辑：
        1. Agent 5接收装配步骤+图片，为每个步骤添加焊接要点
        2. Agent 6接收增强后的步骤，为每个步骤添加安全警告
        3. 返回增强后的组件和产品装配步骤
        """
        print_substep(f"[{self.current_step}/{self.total_steps}] ⚡ 焊接工程师 & 🛡️ 安全专员")

        # ✅ 使用图片而不是PDF
        all_images = []
        all_images.extend(image_hierarchy.get('product_images', []))
        for comp_images in image_hierarchy.get('component_images', {}).values():
            all_images.extend(comp_images)

        import sys
        sys.stdout.flush()

        # ========== Agent 5: 焊接工程师 ==========
        self.log_agent_call("焊接工程师", "为每个装配步骤添加焊接要点", "running")

        # 处理组件装配步骤
        enhanced_component_results = []
        for comp_result in component_results:
            if not comp_result.get("success"):
                enhanced_component_results.append(comp_result)
                continue

            assembly_steps = comp_result.get("assembly_steps", [])

            # ✅ 使用assembly_order来获取组件图片
            assembly_order = comp_result.get("assembly_order", "")
            component_images = image_hierarchy.get('component_images', {}).get(str(assembly_order), [])

            welding_result = self.welding_agent.process(
                all_images=component_images,
                assembly_steps=assembly_steps
            )

            # 将焊接要点嵌入到步骤中
            if welding_result.get("success"):
                enhanced_steps = welding_result.get("enhanced_steps", assembly_steps)
                comp_result["assembly_steps"] = enhanced_steps

            enhanced_component_results.append(comp_result)

        # 处理产品装配步骤
        enhanced_product_result = product_result.copy()
        if product_result.get("success"):
            product_steps = product_result.get("assembly_steps", [])
            product_images = image_hierarchy.get('product_images', [])

            welding_result = self.welding_agent.process(
                all_images=product_images,
                assembly_steps=product_steps
            )

            if welding_result.get("success"):
                enhanced_steps = welding_result.get("enhanced_steps", product_steps)
                enhanced_product_result["assembly_steps"] = enhanced_steps

        print_success(f"⚡ 焊接要点已嵌入到装配步骤中", indent=1)
        sys.stdout.flush()
        self.log_agent_call("焊接工程师", "完成焊接要点标注", "success")

        # ========== Agent 6: 安全专员 ==========
        self.log_agent_call("安全专员", "为每个装配步骤添加安全警告", "running")

        # 处理组件装配步骤
        final_component_results = []
        for comp_result in enhanced_component_results:
            if not comp_result.get("success"):
                final_component_results.append(comp_result)
                continue

            assembly_steps = comp_result.get("assembly_steps", [])

            safety_result = self.safety_agent.process(
                assembly_steps=assembly_steps
            )

            # 将安全警告嵌入到步骤中
            if safety_result.get("success"):
                enhanced_steps = safety_result.get("enhanced_steps", assembly_steps)
                comp_result["assembly_steps"] = enhanced_steps

            final_component_results.append(comp_result)

        # 处理产品装配步骤
        final_product_result = enhanced_product_result.copy()
        if enhanced_product_result.get("success"):
            product_steps = enhanced_product_result.get("assembly_steps", [])

            safety_result = self.safety_agent.process(
                assembly_steps=product_steps
            )

            if safety_result.get("success"):
                enhanced_steps = safety_result.get("enhanced_steps", product_steps)
                final_product_result["assembly_steps"] = enhanced_steps

        print_success(f"🛡️ 安全警告已嵌入到装配步骤中", indent=1)
        sys.stdout.flush()
        self.log_agent_call("安全专员", "完成安全警告标注", "success")

        # 保存增强后的结果
        with open(self.output_dir / "step7_enhanced_component_results.json", "w", encoding="utf-8") as f:
            json.dump(final_component_results, f, ensure_ascii=False, indent=2)

        with open(self.output_dir / "step7_enhanced_product_result.json", "w", encoding="utf-8") as f:
            json.dump(final_product_result, f, ensure_ascii=False, indent=2)

        return final_component_results, final_product_result

    def _step8_integrate_manual(
        self,
        planning_result: Dict,
        component_results: List[Dict],
        product_result: Dict,
        matching_result: Dict
    ) -> Dict:
        """
        步骤8: 整合最终手册

        注意：component_results和product_result已经包含了焊接和安全信息
        """
        print_substep(f"[{self.current_step}/{self.total_steps}] 📚 手册编辑员")

        self.log_agent_call("手册编辑", "把所有工程师的成果整合成一本完整的说明书", "running")

        import sys
        sys.stdout.flush()

        # 构建组件到GLB的映射
        component_to_glb_mapping = {}
        component_level_mappings = matching_result.get("component_level_mappings", {})

        for comp_code, mapping in component_level_mappings.items():
            glb_file = mapping.get("glb_file", "")
            if glb_file:
                component_to_glb_mapping[comp_code] = Path(glb_file).name

        print_info("📝 他正在整理所有内容...", indent=1)
        sys.stdout.flush()

        final_manual = self.integrator.integrate(
            planning_result=planning_result,
            component_assembly_results=component_results,
            product_assembly_result=product_result,
            welding_result={},  # 焊接信息已经在步骤中了
            safety_faq_result={},  # 安全信息已经在步骤中了
            component_to_glb_mapping=component_to_glb_mapping,
            bom_to_mesh_mapping=matching_result.get("product_level_mapping", {}).get("bom_to_mesh", {})
        )

        print_success("📖 装配说明书编辑完成", indent=1)
        sys.stdout.flush()
        self.log_agent_call("手册编辑", "生成了最终的装配说明书", "success")

        # 保存最终手册
        output_file = self.output_dir / "assembly_manual.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(final_manual, f, ensure_ascii=False, indent=2)

        print_success(f"💾 保存到: {output_file}", indent=1)
        sys.stdout.flush()

        return final_manual


# ========== 测试入口 ==========
def test_gemini_pipeline():
    """测试Gemini 6-Agent工作流"""

    # 配置
    api_key = "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"
    pdf_dir = "测试-pdf"
    step_dir = "step-stl文件"
    output_dir = "pipeline_output"

    # 创建工作流实例
    pipeline = GeminiAssemblyPipeline(
        api_key=api_key,
        output_dir=output_dir
    )

    # 运行工作流
    result = pipeline.run(
        pdf_dir=pdf_dir,
        step_dir=step_dir
    )

    # 输出结果
    if result["success"]:
        print("\n" + "=" * 80)
        print("工作流执行成功！")
        print("=" * 80)
        print(f"输出文件: {result['output_file']}")
        print(f"总耗时: {result['elapsed_time']:.1f}秒")
    else:
        print("\n" + "=" * 80)
        print("工作流执行失败！")
        print("=" * 80)
        print(f"错误: {result.get('error')}")


if __name__ == "__main__":
    test_gemini_pipeline()


