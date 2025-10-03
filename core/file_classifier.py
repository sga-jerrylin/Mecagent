# -*- coding: utf-8 -*-
"""

 vs 
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Tuple
import fitz  # PyMuPDF


class FileClassifier:
    """"""
    
    def __init__(self):
        """初始化文件分类器"""
        # 产品总图的匹配模式：包含"产品"、"总图"、"总装"等关键词
        self.product_pattern = re.compile(r'(产品|总图|总装|product|total)', re.IGNORECASE)
        # 组件图的匹配模式："组件图1"、"组件1"、"component_1"等
        self.component_pattern = re.compile(r'(组件图?|component)[_\s]?(\d+)', re.IGNORECASE)
    
    def classify_files(
        self,
        pdf_files: List[str],
        step_files: List[str] = None
    ) -> Dict:
        """
        
        
        Args:
            pdf_files: PDF
            step_files: STEP
            
        Returns:
            {
                "product": {
                    "pdf": ".pdf",
                    "step": ".step",
                    "product_code": "T-SPV1830-EURO"
                },
                "components": [
                    {
                        "index": 1,
                        "name": "",
                        "bom_code": "01.09.2549",
                        "pdf": "1__01.09.2549.pdf",
                        "step": "1__01.09.2549.step"
                    },
                    ...
                ]
            }
        """
        result = {
            "product": None,
            "components": []
        }
        
        # PDF
        for pdf_file in pdf_files:
            filename = Path(pdf_file).stem  # 
            
            # 
            if self.product_pattern.search(filename):
                result["product"] = {
                    "pdf": pdf_file,
                    "step": None,
                    "product_code": self._extract_product_code(filename)
                }
            
            # 匹配组件图
            match = self.component_pattern.search(filename)
            if match:
                component_index = int(match.group(2))  # 第2个分组是数字
                component_info = self._parse_component_filename(filename)
                component_info["index"] = component_index
                component_info["pdf"] = pdf_file
                component_info["step"] = None
                result["components"].append(component_info)
        
        # STEP
        if step_files:
            for step_file in step_files:
                filename = Path(step_file).stem
                
                # 
                if self.product_pattern.search(filename):
                    if result["product"]:
                        result["product"]["step"] = step_file
                
                # 匹配组件STEP
                match = self.component_pattern.search(filename)
                if match:
                    component_index = int(match.group(2))  # 第2个分组是数字
                    # 找到对应的组件并关联STEP文件
                    for comp in result["components"]:
                        if comp["index"] == component_index:
                            comp["step"] = step_file
                            break
        
        # 
        result["components"].sort(key=lambda x: x["index"])
        
        return result
    
    def _extract_product_code(self, filename: str) -> str:
        """
        
        
        Args:
            filename: 
            
        Returns:
            
        """
        #  "T-SPV1830-EURO" 
        pattern = re.compile(r'[A-Z0-9]+-[A-Z0-9]+-[A-Z0-9]+', re.IGNORECASE)
        match = pattern.search(filename)
        if match:
            return match.group(0)
        return ""
    
    def _parse_component_filename(self, filename: str) -> Dict:
        """
        
        
        Args:
            filename: 1__01.09.2549
            
        Returns:
            {
                "name": "",
                "bom_code": "01.09.2549"
            }
        """
        # 
        parts = filename.split('_')
        
        result = {
            "name": "",
            "bom_code": ""
        }
        
        # 
        if len(parts) >= 2:
            result["name"] = parts[1]
        
        # BOM01.09.xxxx
        bom_pattern = re.compile(r'\d{2}\.\d{2}\.\d+')
        for part in parts:
            match = bom_pattern.search(part)
            if match:
                result["bom_code"] = match.group(0)
                break
        
        return result
    
    def convert_pdfs_to_images(
        self,
        file_hierarchy: Dict,
        output_base_dir: str,
        dpi: int = 300
    ) -> Dict:
        """
        PDF
        
        Args:
            file_hierarchy: classify_files
            output_base_dir: 
            dpi: DPI
            
        Returns:
            {
                "product_images": ["/page_001.png", ...],
                "component_images": {
                    1: ["1/page_001.png", ...],
                    2: ["2/page_001.png", ...],
                    ...
                }
            }
        """
        result = {
            "product_images": [],
            "component_images": {}
        }
        
        output_base = Path(output_base_dir)
        output_base.mkdir(parents=True, exist_ok=True)
        
        # 
        if file_hierarchy["product"] and file_hierarchy["product"]["pdf"]:
            product_pdf = file_hierarchy["product"]["pdf"]
            product_dir = output_base / ""
            product_dir.mkdir(exist_ok=True)
            
            print(f"\n : {Path(product_pdf).name}")
            images = self._pdf_to_images(product_pdf, str(product_dir), dpi)
            result["product_images"] = images
            print(f"     {len(images)} ")
        
        # 
        for component in file_hierarchy["components"]:
            if component["pdf"]:
                comp_index = component["index"]
                comp_pdf = component["pdf"]
                comp_dir = output_base / f"{comp_index}"
                comp_dir.mkdir(exist_ok=True)
                
                print(f"\n {comp_index}: {Path(comp_pdf).name}")
                images = self._pdf_to_images(comp_pdf, str(comp_dir), dpi)
                # ✅ 使用字符串key，保持与JSON序列化后的一致性
                result["component_images"][str(comp_index)] = images
                print(f"     {len(images)} ")
        
        return result
    
    def _pdf_to_images(
        self,
        pdf_path: str,
        output_dir: str,
        dpi: int = 300
    ) -> List[str]:
        """
        PDF
        
        Args:
            pdf_path: PDF
            output_dir: 
            dpi: DPI
            
        Returns:
            
        """
        pdf_document = fitz.open(pdf_path)
        image_paths = []
        
        try:
            for page_num in range(len(pdf_document)):
                page = pdf_document[page_num]
                
                # 
                mat = fitz.Matrix(dpi / 72, dpi / 72)
                pix = page.get_pixmap(matrix=mat)
                
                # 
                image_path = Path(output_dir) / f"page_{page_num + 1:03d}.png"
                pix.save(str(image_path))
                image_paths.append(str(image_path))
        
        finally:
            pdf_document.close()
        
        return image_paths

