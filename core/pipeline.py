# -*- coding: utf-8 -*-
"""
核心处理流水线
整合PDF解析、3D模型处理和AI分析
"""

import os
import json
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from processors.file_processor import PDFProcessor, ModelProcessor
from models.vision_model import Qwen3VLModel
from models.assembly_expert import AssemblyExpertModel


class AssemblyManualPipeline:
    """装配说明书生成流水线"""
    
    def __init__(
        self,
        dashscope_api_key: Optional[str] = None,
        deepseek_api_key: Optional[str] = None,
        blender_path: Optional[str] = None
    ):
        """
        初始化处理流水线
        
        Args:
            dashscope_api_key: 阿里云DashScope API Key
            deepseek_api_key: DeepSeek API Key  
            blender_path: Blender可执行文件路径
        """
        self.pdf_processor = PDFProcessor(dpi=300)
        self.model_processor = ModelProcessor(blender_path)
        self.vision_model = Qwen3VLModel(dashscope_api_key)
        self.assembly_expert = AssemblyExpertModel(deepseek_api_key)
        
        self.temp_dir = None
    
    def process_files(
        self,
        pdf_files: List[str],
        model_files: List[str],
        output_dir: str,
        focus_type: str = "general",
        special_requirements: str = "无特殊要求"
    ) -> Dict:
        """
        处理输入文件并生成装配说明书
        
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
            
            # 第一步：处理PDF文件
            print("🔍 正在处理PDF文件...")
            pdf_results = self._process_pdf_files(pdf_files)
            
            # 第二步：处理3D模型文件
            print("🎯 正在处理3D模型文件...")
            model_results = self._process_model_files(model_files, output_path)
            
            # 第三步：AI分析生成装配规程
            print("🤖 正在生成装配规程...")
            assembly_spec = self._generate_assembly_specification(
                pdf_results, model_results, focus_type, special_requirements
            )
            
            # 第四步：生成HTML说明书
            print("📖 正在生成HTML装配说明书...")
            html_result = self._generate_html_manual(
                assembly_spec, model_results, output_path
            )
            
            # 保存完整结果
            result = {
                "success": True,
                "pdf_analysis": pdf_results,
                "model_analysis": model_results,
                "assembly_specification": assembly_spec,
                "html_manual": html_result,
                "output_directory": str(output_path)
            }
            
            # 保存结果到JSON文件
            result_file = output_path / "processing_result.json"
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 处理完成！结果保存在: {output_path}")
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "stage": "pipeline_execution"
            }
        
        finally:
            # 清理临时目录
            if self.temp_dir and os.path.exists(self.temp_dir):
                import shutil
                shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _process_pdf_files(self, pdf_files: List[str]) -> List[Dict]:
        """处理PDF文件"""
        all_results = []
        
        for pdf_file in pdf_files:
            print(f"  📄 处理文件: {os.path.basename(pdf_file)}")
            
            # 转换PDF为图片
            images_dir = os.path.join(self.temp_dir, f"pdf_{len(all_results)}")
            os.makedirs(images_dir, exist_ok=True)
            
            image_paths = self.pdf_processor.pdf_to_images(pdf_file, images_dir)
            
            # 视觉模型分析
            focus_areas = ['welding', 'assembly', 'quality']
            vision_results = self.vision_model.batch_analyze_pdf_pages(
                image_paths, focus_areas
            )
            
            # 提取文本内容
            text_content = self.pdf_processor.extract_text_content(pdf_file)
            
            all_results.append({
                "pdf_file": pdf_file,
                "vision_analysis": vision_results,
                "text_content": text_content,
                "image_paths": image_paths
            })
        
        return all_results
    
    def _process_model_files(self, model_files: List[str], output_dir: Path) -> List[Dict]:
        """处理3D模型文件"""
        model_results = []
        
        models_dir = output_dir / "models"
        models_dir.mkdir(exist_ok=True)
        
        for i, model_file in enumerate(model_files):
            print(f"  🎯 处理模型: {os.path.basename(model_file)}")
            
            # 转换为GLB格式
            glb_filename = f"model_{i:03d}.glb"
            glb_path = models_dir / glb_filename
            
            conversion_result = self.model_processor.step_to_glb(
                model_file, str(glb_path)
            )
            
            if conversion_result["success"]:
                # 分析模型结构
                analysis_result = self.model_processor.analyze_model_structure(
                    str(glb_path)
                )
                
                model_results.append({
                    "original_file": model_file,
                    "glb_file": str(glb_path),
                    "glb_filename": glb_filename,
                    "conversion": conversion_result,
                    "analysis": analysis_result
                })
            else:
                model_results.append({
                    "original_file": model_file,
                    "glb_file": None,
                    "conversion": conversion_result,
                    "analysis": {"success": False, "error": "转换失败"}
                })
        
        return model_results
    
    def _generate_assembly_specification(
        self,
        pdf_results: List[Dict],
        model_results: List[Dict],
        focus_type: str,
        special_requirements: str
    ) -> Dict:
        """生成装配规程"""
        
        # 整理视觉分析结果
        vision_analysis = []
        for pdf_result in pdf_results:
            vision_analysis.extend(pdf_result["vision_analysis"])
        
        # 整理模型分析结果
        model_analysis = {
            "models": model_results,
            "total_models": len(model_results),
            "successful_conversions": sum(1 for r in model_results if r.get("glb_file"))
        }
        
        # 调用装配专家模型
        return self.assembly_expert.generate_assembly_specification(
            vision_analysis_results=vision_analysis,
            model_analysis_results=model_analysis,
            focus_type=focus_type,
            special_requirements=special_requirements
        )
    
    def _generate_html_manual(
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


# 便捷函数
def generate_assembly_manual(
    pdf_files: List[str],
    model_files: List[str],
    output_dir: str,
    focus_type: str = "general",
    dashscope_api_key: Optional[str] = None,
    deepseek_api_key: Optional[str] = None
) -> Dict:
    """
    生成装配说明书的便捷函数
    
    Args:
        pdf_files: PDF文件路径列表
        model_files: 3D模型文件路径列表
        output_dir: 输出目录
        focus_type: 专业重点类型
        dashscope_api_key: DashScope API Key
        deepseek_api_key: DeepSeek API Key
        
    Returns:
        处理结果
    """
    pipeline = AssemblyManualPipeline(
        dashscope_api_key=dashscope_api_key,
        deepseek_api_key=deepseek_api_key
    )
    
    return pipeline.process_files(
        pdf_files=pdf_files,
        model_files=model_files,
        output_dir=output_dir,
        focus_type=focus_type
    )
