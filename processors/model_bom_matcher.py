#!/usr/bin/env python3
"""
3D模型与BOM表匹配模块

功能：
1. 从STEP文件中提取零件层级结构
2. 将3D模型中的零件与BOM表进行匹配
3. 生成带有BOM信息的GLB元数据
4. 为爆炸图动画提供零件映射
"""

import re
import json
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import trimesh
from difflib import SequenceMatcher


class ModelBOMMatcher:
    """3D模型与BOM表匹配器"""
    
    def __init__(self):
        self.bom_items = []
        self.model_parts = []
        self.matched_pairs = []
        
    def load_bom(self, bom_items: List[Dict]) -> None:
        """
        加载BOM表数据
        
        Args:
            bom_items: BOM项目列表，每项包含 seq, code, name, qty, weight
        """
        self.bom_items = bom_items
        print(f"📦 已加载 {len(bom_items)} 个BOM项目")
        
    def extract_parts_from_step(self, step_path: str) -> List[Dict]:
        """
        从STEP文件中提取零件信息
        
        Args:
            step_path: STEP文件路径
            
        Returns:
            零件列表，每项包含 node_name, geometry_name, transform
        """
        try:
            # 使用trimesh加载STEP文件
            scene = trimesh.load(step_path, force='scene')
            
            if not isinstance(scene, trimesh.Scene):
                print("⚠️  STEP文件只包含单个网格，无装配层级")
                return [{
                    "node_name": "single_mesh",
                    "geometry_name": "mesh_0",
                    "transform": None,
                    "bounds": scene.bounds.tolist() if hasattr(scene, 'bounds') else None
                }]
            
            # 提取所有节点
            parts = []
            node_names = list(scene.graph.nodes_geometry)
            
            print(f"🔍 从STEP文件中提取到 {len(node_names)} 个零件节点")
            
            for node_name in node_names:
                transform, geometry_name = scene.graph[node_name]
                geometry = scene.geometry.get(geometry_name)
                
                part_info = {
                    "node_name": node_name,
                    "geometry_name": geometry_name,
                    "transform": transform.tolist() if transform is not None else None,
                    "bounds": geometry.bounds.tolist() if geometry and hasattr(geometry, 'bounds') else None,
                    "centroid": geometry.centroid.tolist() if geometry and hasattr(geometry, 'centroid') else None
                }
                
                parts.append(part_info)
                print(f"   📌 节点: {node_name} → 几何体: {geometry_name}")
            
            self.model_parts = parts
            return parts
            
        except Exception as e:
            print(f"❌ 提取STEP零件失败: {e}")
            return []
    
    def match_parts_to_bom(
        self, 
        parts: Optional[List[Dict]] = None,
        bom_items: Optional[List[Dict]] = None
    ) -> List[Dict]:
        """
        将3D模型零件与BOM表进行匹配
        
        Args:
            parts: 零件列表（如果为None，使用self.model_parts）
            bom_items: BOM项目列表（如果为None，使用self.bom_items）
            
        Returns:
            匹配结果列表，每项包含 part, bom_item, confidence, match_reason
        """
        if parts is None:
            parts = self.model_parts
        if bom_items is None:
            bom_items = self.bom_items
            
        if not parts or not bom_items:
            print("⚠️  零件列表或BOM表为空，无法匹配")
            return []
        
        matched_pairs = []
        
        print(f"\n🔗 开始匹配 {len(parts)} 个零件与 {len(bom_items)} 个BOM项目...")
        
        for part in parts:
            node_name = part.get("node_name", "")
            geometry_name = part.get("geometry_name", "")
            
            # 尝试多种匹配策略
            best_match = None
            best_confidence = 0.0
            match_reason = ""
            
            for bom_item in bom_items:
                bom_code = bom_item.get("code", "")
                bom_name = bom_item.get("name", "")
                
                # 策略1: 零件代号完全匹配
                if bom_code and (bom_code in node_name or bom_code in geometry_name):
                    confidence = 1.0
                    reason = f"零件代号完全匹配: {bom_code}"
                    if confidence > best_confidence:
                        best_match = bom_item
                        best_confidence = confidence
                        match_reason = reason
                    continue
                
                # 策略2: 零件代号部分匹配（去除特殊字符）
                clean_code = re.sub(r'[^a-zA-Z0-9]', '', bom_code)
                clean_node = re.sub(r'[^a-zA-Z0-9]', '', node_name)
                if clean_code and clean_code in clean_node:
                    confidence = 0.9
                    reason = f"零件代号部分匹配: {bom_code}"
                    if confidence > best_confidence:
                        best_match = bom_item
                        best_confidence = confidence
                        match_reason = reason
                    continue
                
                # 策略3: 零件名称相似度匹配
                if bom_name:
                    similarity = SequenceMatcher(None, node_name.lower(), bom_name.lower()).ratio()
                    if similarity > 0.6:
                        confidence = similarity * 0.8  # 降低权重
                        reason = f"名称相似度匹配: {similarity:.2f}"
                        if confidence > best_confidence:
                            best_match = bom_item
                            best_confidence = confidence
                            match_reason = reason
            
            # 记录匹配结果
            if best_match:
                matched_pairs.append({
                    "part": part,
                    "bom_item": best_match,
                    "confidence": best_confidence,
                    "match_reason": match_reason
                })
                print(f"   ✅ {node_name} → {best_match.get('code')} ({best_confidence:.2f}) - {match_reason}")
            else:
                # 未匹配的零件
                matched_pairs.append({
                    "part": part,
                    "bom_item": None,
                    "confidence": 0.0,
                    "match_reason": "未找到匹配的BOM项目"
                })
                print(f"   ⚠️  {node_name} → 未匹配")
        
        self.matched_pairs = matched_pairs
        
        # 统计匹配结果
        matched_count = sum(1 for pair in matched_pairs if pair["bom_item"] is not None)
        print(f"\n📊 匹配完成: {matched_count}/{len(parts)} 个零件成功匹配")
        
        return matched_pairs
    
    def generate_glb_metadata(
        self,
        glb_path: str,
        matched_pairs: Optional[List[Dict]] = None,
        vision_result: Optional[Dict] = None
    ) -> Dict:
        """
        生成GLB元数据，包含BOM信息和装配指导
        
        Args:
            glb_path: GLB文件路径
            matched_pairs: 匹配结果（如果为None，使用self.matched_pairs）
            vision_result: 视觉模型的分析结果
            
        Returns:
            元数据字典
        """
        if matched_pairs is None:
            matched_pairs = self.matched_pairs
            
        metadata = {
            "glb_file": glb_path,
            "total_parts": len(matched_pairs),
            "matched_parts": sum(1 for p in matched_pairs if p["bom_item"] is not None),
            "parts": []
        }
        
        for i, pair in enumerate(matched_pairs):
            part = pair["part"]
            bom_item = pair["bom_item"]
            
            part_metadata = {
                "part_id": f"part_{i:03d}",
                "node_name": part.get("node_name"),
                "geometry_name": part.get("geometry_name"),
                "match_confidence": pair["confidence"],
                "match_reason": pair["match_reason"]
            }
            
            # 添加BOM信息
            if bom_item:
                part_metadata["bom"] = {
                    "seq": bom_item.get("seq"),
                    "code": bom_item.get("code"),
                    "name": bom_item.get("name"),
                    "qty": bom_item.get("qty"),
                    "weight": bom_item.get("weight")
                }
                
                # 如果有视觉模型的结果，添加装配指导
                if vision_result and "part_assembly_guide" in vision_result:
                    for guide in vision_result["part_assembly_guide"]:
                        if guide.get("part_code") == bom_item.get("code"):
                            part_metadata["assembly_guide"] = {
                                "sequence": guide.get("assembly_sequence"),
                                "process_requirements": guide.get("process_requirements"),
                                "key_points": guide.get("key_points"),
                                "tools_needed": guide.get("tools_needed"),
                                "fasteners_used": guide.get("fasteners_used"),
                                "safety_notes": guide.get("safety_notes")
                            }
                            break
            
            metadata["parts"].append(part_metadata)
        
        return metadata
    
    def save_metadata(self, metadata: Dict, output_path: str) -> None:
        """
        保存元数据到JSON文件
        
        Args:
            metadata: 元数据字典
            output_path: 输出文件路径
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        print(f"💾 元数据已保存: {output_path}")

