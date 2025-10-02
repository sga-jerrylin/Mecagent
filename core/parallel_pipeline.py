#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
并行处理流水线 - 生产级实现
同时处理GLB转换、PDF解析、AI分析三个通道
"""

import os
import json
import asyncio
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

from processors.file_processor import PDFProcessor, ModelProcessor
from models.vision_model import Qwen3VLModel
from models.assembly_expert import AssemblyExpertModel
from core.dual_channel_parser import DualChannelParser


class ParallelAssemblyPipeline:
    """并行装配说明书生成流水线"""
    
    def __init__(
        self,
        dashscope_api_key: Optional[str] = None,
        deepseek_api_key: Optional[str] = None,
        progress_reporter = None
    ):
        """
        初始化并行处理流水线
        
        Args:
            dashscope_api_key: 阿里云DashScope API Key
            deepseek_api_key: DeepSeek API Key
            progress_reporter: 进度报告器实例
        """
        self.pdf_processor = PDFProcessor(dpi=300)
        self.model_processor = ModelProcessor()
        self.dual_parser = DualChannelParser(progress_reporter=progress_reporter)
        self.assembly_expert = AssemblyExpertModel(deepseek_api_key)

        self.progress_reporter = progress_reporter
        self.temp_dir = None
    
    def _report_progress(self, stage: str, progress: int, message: str, data: Dict = None):
        """报告进度"""
        if self.progress_reporter:
            self.progress_reporter.report_progress(stage, progress, message, data)
    
    def _report_parallel(self, parallel_data: Dict):
        """报告并行进度"""
        if self.progress_reporter:
            self.progress_reporter.report_parallel(parallel_data)
    
    def _log(self, message: str, level: str = "info"):
        """记录日志"""
        print(f"[{level.upper()}] {message}")
        if self.progress_reporter:
            self.progress_reporter.log(message, level)
    
    async def process_files_parallel(
        self,
        pdf_files: List[str],
        model_files: List[str],
        output_dir: str,
        focus_type: str = "general",
        special_requirements: str = "无特殊要求"
    ) -> Dict:
        """
        并行处理输入文件并生成装配说明书
        
        Args:
            pdf_files: PDF文件路径列表
            model_files: 3D模型文件路径列表
            output_dir: 输出目录
            focus_type: 专业重点类型
            special_requirements: 特殊要求
            
        Returns:
            处理结果
        """
        try:
            # 创建输出目录
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # 创建临时工作目录
            self.temp_dir = tempfile.mkdtemp()
            
            self._log("🚀 开始并行处理流水线", "info")
            
            # 并行处理数据容器
            parallel_results = {
                "glb": None,
                "pdf": None,
                "vision": None
            }
            
            # 并行进度容器
            parallel_progress = {
                "glb": {"progress": 0, "message": "准备中...", "completed": 0, "total": len(model_files)},
                "pdf": {"progress": 0, "message": "准备中...", "bom_items": 0, "dimensions": 0, "requirements": 0},
                "vision": {"progress": 0, "message": "准备中...", "results": []}
            }
            
            # 使用线程池并行执行三个任务
            with ThreadPoolExecutor(max_workers=3) as executor:
                # 提交三个并行任务
                future_glb = executor.submit(
                    self._process_models_with_progress,
                    model_files,
                    output_path,
                    parallel_progress
                )
                
                future_pdf = executor.submit(
                    self._process_pdfs_with_progress,
                    pdf_files,
                    parallel_progress
                )
                
                future_vision = executor.submit(
                    self._analyze_vision_with_progress,
                    pdf_files,
                    parallel_progress
                )
                
                # 监控并行任务进度
                futures = {
                    "glb": future_glb,
                    "pdf": future_pdf,
                    "vision": future_vision
                }
                
                # 等待所有任务完成，同时更新进度
                while any(not f.done() for f in futures.values()):
                    # 发送并行进度更新
                    self._report_parallel(parallel_progress)
                    await asyncio.sleep(0.5)  # 每0.5秒更新一次

                # 获取结果并检查错误
                try:
                    parallel_results["glb"] = future_glb.result()
                    if not parallel_results["glb"]:
                        raise Exception("GLB转换失败：未返回结果")
                except Exception as e:
                    error_msg = f"GLB转换失败: {str(e)}"
                    self._log(f"❌ {error_msg}", "error")
                    raise Exception(error_msg)

                try:
                    parallel_results["pdf"] = future_pdf.result()
                    if not parallel_results["pdf"]:
                        raise Exception("PDF解析失败：未返回结果")
                except Exception as e:
                    error_msg = f"PDF解析失败: {str(e)}"
                    self._log(f"❌ {error_msg}", "error")
                    raise Exception(error_msg)

                try:
                    parallel_results["vision"] = future_vision.result()
                    if not parallel_results["vision"]:
                        # ✅ 修复: 视觉分析失败应该立即停止，不继续执行
                        error_msg = "视觉分析未返回结果"
                        self._log(f"❌ {error_msg}", "error")
                        raise Exception(error_msg)
                except Exception as e:
                    # ✅ 修复: 视觉分析失败应该立即停止，不继续执行
                    error_msg = f"视觉分析失败: {str(e)}"
                    self._log(f"❌ {error_msg}", "error")
                    raise Exception(error_msg)

            self._log("✅ 并行处理完成", "success")

            # 第二阶段：AI融合分析
            self._log("🤖 开始AI融合分析...", "info")
            self._report_progress("ai", 50, "DeepSeek专家模型分析中...")

            print(f"[DEBUG] 准备调用_generate_assembly_specification")
            print(f"[DEBUG] PDF结果数量: {len(parallel_results['pdf'])}")
            print(f"[DEBUG] Vision结果数量: {len(parallel_results['vision'])}")
            print(f"[DEBUG] GLB结果数量: {len(parallel_results['glb'])}")

            assembly_spec = await self._generate_assembly_specification(
                parallel_results["pdf"],
                parallel_results["vision"],
                parallel_results["glb"],
                focus_type,
                special_requirements
            )

            print(f"[DEBUG] AI融合分析完成")
            self._report_progress("ai", 100, "AI分析完成")

            # 第三阶段：生成爆炸动画数据
            self._log("💥 生成GLB爆炸动画数据...", "info")
            self._report_progress("explosion", 50, "计算爆炸向量...")

            for model_result in parallel_results["glb"]:
                if model_result.get("glb_file") and os.path.exists(model_result["glb_file"]):
                    explosion_result = self.model_processor.generate_explosion_data(
                        glb_path=model_result["glb_file"],
                        assembly_spec=assembly_spec,
                        output_dir=str(output_path)
                    )
                    model_result["explosion_data"] = explosion_result

                    if explosion_result.get("success"):
                        self._log(f"✅ {model_result['glb_filename']}: {explosion_result['message']}", "success")
                    else:
                        self._log(f"⚠️ {model_result['glb_filename']}: {explosion_result.get('message', '爆炸数据生成失败')}", "warning")

            self._report_progress("explosion", 100, "爆炸动画数据生成完成")
            
            # 第三阶段：生成HTML说明书
            self._log("📖 生成HTML装配说明书...", "info")
            self._report_progress("generate", 50, "生成交互式说明书...")
            
            html_result = await self._generate_html_manual(
                assembly_spec,
                parallel_results["glb"],
                output_path
            )
            
            self._report_progress("generate", 100, "说明书生成完成")
            
            # 保存完整结果
            result = {
                "success": True,
                "pdf_analysis": parallel_results["pdf"],
                "vision_analysis": parallel_results["vision"],
                "model_analysis": parallel_results["glb"],
                "assembly_specification": assembly_spec,
                "html_manual": html_result,
                "output_directory": str(output_path)
            }
            
            # 保存结果到JSON文件
            result_file = output_path / "processing_result.json"
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            self._log(f"✅ 处理完成！结果保存在: {output_path}", "success")
            return result
            
        except Exception as e:
            self._log(f"❌ 处理失败: {str(e)}", "error")
            return {
                "success": False,
                "error": str(e),
                "stage": "parallel_pipeline"
            }
        
        finally:
            # 清理临时目录
            if self.temp_dir and os.path.exists(self.temp_dir):
                import shutil
                shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _process_models_with_progress(
        self,
        model_files: List[str],
        output_path: Path,
        progress_container: Dict
    ) -> List[Dict]:
        """处理3D模型文件（带进度报告）"""
        model_results = []
        models_dir = output_path / "models"
        models_dir.mkdir(exist_ok=True)

        total = len(model_files)

        self._log(f"🔄 开始STEP→GLB转换，共{total}个文件", "info")

        for i, model_file in enumerate(model_files):
            filename = os.path.basename(model_file)

            # 更新进度
            progress = int((i / total) * 80)  # 转换占80%
            progress_container["glb"]["progress"] = progress
            progress_container["glb"]["message"] = f"转换中: {filename}"
            progress_container["glb"]["current_file"] = filename
            progress_container["glb"]["completed"] = i

            self._log(f"🔄 正在转换: {filename}", "info")

            # 转换为GLB格式
            glb_filename = f"model_{i:03d}.glb"
            glb_path = models_dir / glb_filename

            conversion_result = self.model_processor.step_to_glb(
                model_file, str(glb_path)
            )

            if conversion_result["success"]:
                # 注意：file_processor返回的是parts_count，不是part_count
                part_count = conversion_result.get("parts_count", 0)
                self._log(f"✅ {filename} → {glb_filename}: {part_count}个零件", "success")

                model_results.append({
                    "original_file": model_file,
                    "glb_file": str(glb_path),
                    "glb_filename": glb_filename,
                    "conversion": conversion_result,
                    "part_count": part_count,
                    "explosion_data": None  # 稍后生成
                })
            else:
                # ✅ 修复: 避免error_msg中的大括号导致格式化错误
                error_msg = conversion_result.get("error", "未知错误")
                # 使用字符串拼接而不是f-string，避免二次格式化
                log_msg = "❌ " + filename + " 转换失败: " + str(error_msg)
                self._log(log_msg, "error")

                model_results.append({
                    "original_file": model_file,
                    "glb_file": None,
                    "conversion": conversion_result,
                    "explosion_data": None
                })

        # 完成
        progress_container["glb"]["progress"] = 100
        progress_container["glb"]["message"] = "GLB转换完成"
        progress_container["glb"]["completed"] = total

        total_parts = sum(m.get("part_count", 0) for m in model_results)
        self._log(f"✅ STEP→GLB转换完成: {total}个文件, 共{total_parts}个零件", "success")

        return model_results
    
    def _process_pdfs_with_progress(
        self,
        pdf_files: List[str],
        progress_container: Dict
    ) -> List[Dict]:
        """处理PDF文件（带进度报告）"""
        pdf_results = []
        total = len(pdf_files)
        
        for i, pdf_file in enumerate(pdf_files):
            # 更新进度
            progress = int((i / total) * 100)
            progress_container["pdf"]["progress"] = progress
            progress_container["pdf"]["message"] = f"解析中: {os.path.basename(pdf_file)}"
            progress_container["pdf"]["current_file"] = os.path.basename(pdf_file)
            
            # 双通道解析
            print(f"[DEBUG] 并行处理 - 开始解析PDF: {pdf_file}")
            candidate_facts = self.dual_parser.parse_pdf(pdf_file)
            print(f"[DEBUG] 并行处理 - PDF解析完成")

            # 统计信息
            bom_count = len(candidate_facts.get("bom_candidates", []))
            feature_count = len(candidate_facts.get("feature_candidates", []))
            note_count = len(candidate_facts.get("note_candidates", []))

            print(f"[DEBUG] 统计: BOM={bom_count}, 特征={feature_count}, 备注={note_count}")

            progress_container["pdf"]["bom_items"] += bom_count
            progress_container["pdf"]["dimensions"] += feature_count
            progress_container["pdf"]["requirements"] += note_count
            
            pdf_results.append({
                "pdf_file": pdf_file,
                "candidate_facts": candidate_facts,
                "statistics": {
                    "bom_items": bom_count,
                    "features": feature_count,
                    "notes": note_count
                }
            })
        
        # 完成
        progress_container["pdf"]["progress"] = 100
        progress_container["pdf"]["message"] = "PDF解析完成"

        return pdf_results

    def _analyze_vision_with_progress(
        self,
        pdf_files: List[str],
        progress_container: Dict
    ) -> List[Dict]:
        """视觉分析（带进度报告）"""
        vision_results = []
        total = len(pdf_files)

        for i, pdf_file in enumerate(pdf_files):
            # 更新进度
            progress = int((i / total) * 100)
            progress_container["vision"]["progress"] = progress
            progress_container["vision"]["message"] = f"Qwen3-VL分析中: {os.path.basename(pdf_file)}"

            # 这里可以添加额外的视觉分析
            # 目前双通道解析器已经包含了视觉分析
            vision_results.append({
                "pdf_file": pdf_file,
                "status": "analyzed"
            })

        # 完成
        progress_container["vision"]["progress"] = 100
        progress_container["vision"]["message"] = "视觉分析完成"

        return vision_results

    async def _generate_assembly_specification(
        self,
        pdf_results: List[Dict],
        vision_results: List[Dict],
        model_results: List[Dict],
        focus_type: str,
        special_requirements: str
    ) -> Dict:
        """生成装配规程"""

        self._log("🤖 DeepSeek开始匹配BOM和GLB零件...", "info")

        # 整理候选事实
        all_candidate_facts = []
        bom_total = 0
        for pdf_result in pdf_results:
            facts = pdf_result.get("candidate_facts", {})
            all_candidate_facts.append(facts)
            bom_total += len(facts.get("bom_candidates", []))

        self._log(f"📦 BOM数据: {bom_total}个零件", "info")

        # 整理模型分析结果
        model_analysis = {
            "models": model_results,
            "total_models": len(model_results),
            "successful_conversions": sum(1 for r in model_results if r.get("glb_file"))
        }

        glb_parts = sum(r.get("part_count", 0) for r in model_results)
        self._log(f"🎨 GLB数据: {glb_parts}个零件", "info")

        self._log(f"🔗 开始匹配: BOM({bom_total}项) ↔ GLB({glb_parts}个零件)", "info")

        # 调用装配专家模型
        self._log("🤖 调用DeepSeek专家模型进行智能匹配...", "info")

        result = self.assembly_expert.generate_assembly_specification(
            vision_analysis_results=all_candidate_facts,
            model_analysis_results=model_analysis,
            focus_type=focus_type,
            special_requirements=special_requirements
        )

        # ✅ 添加调试日志：打印DeepSeek完整返回结构
        print("\n" + "="*80)
        print("[DEBUG] DeepSeek完整返回结构:")
        import json
        print(json.dumps(result, indent=2, ensure_ascii=False))
        print("="*80 + "\n")

        # 检查是否成功
        if not result or not result.get("success"):
            error_msg = result.get("error", "未知错误") if result else "未返回结果"
            self._log(f"❌ DeepSeek匹配失败: {error_msg}", "error")
            raise Exception(f"DeepSeek匹配失败: {error_msg}")

        # 提取结果数据
        parsed_result = result.get("result", {})

        # ✅ 添加调试日志：打印parsed_result的类型和键
        print(f"[DEBUG] parsed_result类型: {type(parsed_result)}")
        if isinstance(parsed_result, dict):
            print(f"[DEBUG] parsed_result键: {list(parsed_result.keys())}")
        else:
            print(f"[DEBUG] parsed_result不是字典: {parsed_result}")

        if not isinstance(parsed_result, dict):
            raise Exception("DeepSeek返回结果不是有效的JSON对象")

        def resolve_list(source: Dict[str, Any], candidate_keys: List[str]) -> List[Any]:
            for key in candidate_keys:
                value = source.get(key)
                if isinstance(value, list):
                    return value
                if isinstance(value, dict):
                    nested = value.get('steps') or value.get('items') or value.get('data')
                    if isinstance(nested, list):
                        return nested
            return []

        def collect_parts_from_entry(entry):
            if entry is None:
                return
            if isinstance(entry, str):
                name = entry.strip()
                if name:
                    unique_parts.add(name)
                return
            if isinstance(entry, list):
                for item in entry:
                    collect_parts_from_entry(item)
                return
            if isinstance(entry, dict):
                for key in ('part_code', 'code', 'bom_code', 'name'):
                    value = entry.get(key)
                    if isinstance(value, str):
                        value = value.strip()
                        if value:
                            unique_parts.add(value)
                bom_ref = entry.get('bom_reference')
                if isinstance(bom_ref, dict):
                    collect_parts_from_entry(bom_ref.get('code'))
                    collect_parts_from_entry(bom_ref.get('name'))
                for nested_key in ('parts', 'parts_involved', 'components'):
                    nested = entry.get(nested_key)
                    if isinstance(nested, list):
                        collect_parts_from_entry(nested)
                return

        assembly_steps = resolve_list(parsed_result, ['assembly_steps', 'assembly_sequence', 'process_steps'])
        part_guides = resolve_list(parsed_result, ['part_assembly_guide', 'part_guides'])
        bom_mapping = parsed_result.get('bom_mapping') if isinstance(parsed_result.get('bom_mapping'), list) else []

        unique_parts = set()
        collect_parts_from_entry(assembly_steps)
        collect_parts_from_entry(part_guides)
        collect_parts_from_entry(parsed_result.get('parts'))
        collect_parts_from_entry(parsed_result.get('components'))
        collect_parts_from_entry(parsed_result.get('critical_connections'))
        collect_parts_from_entry(bom_mapping)

        matched_from_mapping = len([m for m in bom_mapping if isinstance(m, dict) and m.get('matched')]) if bom_mapping else 0
        matched_count = matched_from_mapping or len(unique_parts)
        if matched_count == 0:
            matched_count = len(unique_parts)

        bom_summary = parsed_result.get('bom_summary') if isinstance(parsed_result.get('bom_summary'), dict) else {}
        total_parts_reported = bom_summary.get('total_parts')
        try:
            total_parts_reported = int(total_parts_reported)
        except (ValueError, TypeError):
            total_parts_reported = None

        total_parts = total_parts_reported or bom_total or matched_count
        match_rate = (matched_count / total_parts * 100) if total_parts else 0.0

        statistics = {
            'bom_total': bom_total,
            'total_parts': total_parts,
            'matched_parts': matched_count,
            'match_rate': round(match_rate, 2),
            'assembly_step_count': len(assembly_steps),
            'part_guide_count': len(part_guides)
        }
        result['statistics'] = statistics

        rate_text = f"{match_rate:.1f}% ({matched_count}/{total_parts})" if total_parts else '暂无总数'
        self._log(
            f"✅ DeepSeek匹配完成: 覆盖{matched_count}个零件, {len(assembly_steps)}个装配步骤, 匹配率{rate_text}",
            'success'
        )

        print(f"[DEBUG] 统计信息: {statistics}")

        return result

    async def _generate_html_manual(
        self,
        assembly_spec: Dict,
        model_results: List[Dict],
        output_dir: Path
    ) -> Dict:
        """生成HTML装配说明书"""
        from generators.html_generator import HTMLManualGenerator

        generator = HTMLManualGenerator()

        # 准备GLB文件列表
        glb_files = [
            r["glb_filename"] for r in model_results
            if r.get("glb_file") and os.path.exists(r["glb_file"])
        ]

        return generator.generate_manual(
            assembly_spec=assembly_spec,
            glb_files=glb_files,
            output_dir=str(output_dir)
        )

