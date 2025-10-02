"""
BOM-3D匹配模块
功能：将STEP文件解析出的3D零件（可能有乱码）与BOM表进行匹配
"""

import re
from typing import List, Dict, Optional


class BOM3DMatcher:
    """BOM-3D匹配器（纯代码实现，不使用AI）"""
    
    def __init__(self):
        pass
    
    def fix_encoding(self, text: str) -> str:
        """
        修复STEP文件中的中文乱码

        Args:
            text: 可能包含乱码的文本

        Returns:
            修复后的文本
        """
        if not text:
            return text

        try:
            # 尝试修复常见的编码问题
            # STEP文件通常是latin1编码，但包含GBK字符
            fixed = text.encode('latin1').decode('gbk', errors='ignore')
            return fixed
        except:
            # 如果修复失败，返回原文
            return text
    
    def extract_code_from_name(self, name: str) -> Optional[str]:
        """
        从零件名称中提取BOM代号
        
        支持的格式：
        - 01.09.2549
        - 02.03.0088
        - T-SPV1830-EURO-09-Q235
        
        Args:
            name: 零件名称
            
        Returns:
            提取到的代号，如果没有则返回None
        """
        if not name:
            return None
        
        # 模式1: 匹配 01.09.2549 格式
        pattern1 = r'\b(\d{2}\.\d{2}\.\d{4})\b'
        match = re.search(pattern1, name)
        if match:
            return match.group(1)
        
        # 模式2: 匹配 T-SPV1830-EURO-09 格式（产品代号）
        pattern2 = r'(T-[A-Z0-9]+-[A-Z0-9]+-\d+)'
        match = re.search(pattern2, name)
        if match:
            return match.group(1)
        
        return None
    
    def extract_spec_from_name(self, name: str) -> Optional[str]:
        """
        从零件名称中提取规格（用于标准件匹配）
        
        支持的格式：
        - M8×80
        - M30*60
        - Φ20×3
        - 16×3
        
        Args:
            name: 零件名称
            
        Returns:
            提取到的规格，如果没有则返回None
        """
        if not name:
            return None
        
        # 模式1: M8×80 或 M8*80
        pattern1 = r'M\d+[×*]\d+'
        match = re.search(pattern1, name, re.IGNORECASE)
        if match:
            return match.group(0).upper().replace('*', '×')
        
        # 模式2: Φ20×3 或 20×3
        pattern2 = r'[ΦФ]?\d+[×*]\d+'
        match = re.search(pattern2, name)
        if match:
            return match.group(0).replace('*', '×')
        
        # 模式3: M8 (单独的螺纹规格)
        pattern3 = r'M\d+'
        match = re.search(pattern3, name, re.IGNORECASE)
        if match:
            return match.group(0).upper()
        
        return None
    
    def match_parts(
        self,
        bom_data: List[Dict],
        parts_list: List[Dict]
    ) -> Dict:
        """
        将3D零件列表与BOM表进行匹配
        
        Args:
            bom_data: BOM表数据 [{"seq": "1", "code": "01.09.2549", "name": "后座组件", ...}]
            parts_list: 3D零件列表 [{"node_name": "NAUO001", "geometry_name": "01.09.2549-后座组件"}]
            
        Returns:
            匹配结果
        """
        print(f"\n🔧 开始BOM-3D匹配（代码实现）...")
        print(f"📊 BOM项数: {len(bom_data)}")
        print(f"📊 3D零件数: {len(parts_list)}")
        
        # 构建BOM索引（按代号和规格）
        bom_by_code = {}
        bom_by_spec = {}
        
        for bom_item in bom_data:
            code = bom_item.get("code", "")
            name = bom_item.get("name", "")
            product_code = bom_item.get("product_code", "")

            # 按代号索引
            if code:
                bom_by_code[code] = bom_item

            # 按规格索引（用于标准件）
            # 优先从product_code提取规格，其次从name提取
            spec = self.extract_spec_from_name(product_code) or self.extract_spec_from_name(name)
            if spec:
                if spec not in bom_by_spec:
                    bom_by_spec[spec] = []
                bom_by_spec[spec].append(bom_item)
        
        print(f"✅ BOM索引构建完成: {len(bom_by_code)} 个代号, {len(bom_by_spec)} 个规格")
        
        # 匹配3D零件
        cleaned_parts = []
        matched_count = 0
        
        for idx, part in enumerate(parts_list):
            node_name = part.get("node_name", "")
            geometry_name = part.get("geometry_name", "")
            
            # 修复乱码
            fixed_name = self.fix_encoding(geometry_name)
            
            # 生成mesh_id
            mesh_id = f"mesh_{idx+1:03d}"
            
            # 尝试匹配
            matched_bom = None
            match_method = None
            confidence = 0.0
            
            # 方法1: 通过BOM代号匹配
            code = self.extract_code_from_name(fixed_name)
            if code and code in bom_by_code:
                matched_bom = bom_by_code[code]
                match_method = "代号匹配"
                confidence = 0.95
                matched_count += 1
            
            # 方法2: 通过规格匹配（标准件）
            if not matched_bom:
                spec = self.extract_spec_from_name(fixed_name)
                if spec and spec in bom_by_spec:
                    # 如果有多个BOM项匹配同一规格，选择第一个
                    matched_bom = bom_by_spec[spec][0]
                    match_method = "规格匹配"
                    confidence = 0.85
                    matched_count += 1
            
            # 构建清洗后的零件记录
            cleaned_part = {
                "mesh_id": mesh_id,
                "node_name": node_name,
                "geometry_name": geometry_name,  # 原始名称（乱码）
                "fixed_name": fixed_name,  # 修复后的名称
                "bom_code": matched_bom.get("code") if matched_bom else None,
                "bom_name": matched_bom.get("name") if matched_bom else "未匹配",
                "bom_seq": matched_bom.get("seq") if matched_bom else None,
                "match_method": match_method,
                "confidence": confidence
            }
            
            cleaned_parts.append(cleaned_part)
        
        # 统计
        matching_rate = matched_count / len(parts_list) if parts_list else 0

        print(f"✅ 匹配完成: {matched_count}/{len(parts_list)} ({matching_rate*100:.1f}%)")

        # 生成BOM到mesh_id的映射表
        bom_to_mesh_mapping = self.generate_bom_to_mesh_mapping(cleaned_parts)
        print(f"✅ BOM映射表生成完成: {len(bom_to_mesh_mapping)} 个BOM代号")

        # ✅ 分离已匹配和未匹配的零件（用于AI匹配）
        matched_parts = [part for part in cleaned_parts if part.get("bom_code")]
        unmatched_parts = [part for part in cleaned_parts if not part.get("bom_code")]

        return {
            "summary": {
                "total_3d_parts": len(parts_list),
                "matched_count": matched_count,
                "unmatched_count": len(parts_list) - matched_count,
                "matching_rate": matching_rate
            },
            "cleaned_parts": cleaned_parts,
            "matched_parts": matched_parts,  # ✅ 已匹配的零件
            "unmatched_parts": unmatched_parts,  # ✅ 未匹配的零件
            "bom_to_mesh_mapping": bom_to_mesh_mapping
        }
    
    def generate_bom_to_mesh_mapping(self, cleaned_parts: List[Dict]) -> Dict[str, List[str]]:
        """
        生成BOM代号到mesh_id的映射表（用于前端3D高亮）
        
        Args:
            cleaned_parts: 清洗后的零件列表
            
        Returns:
            映射表 {"01.09.2549": ["mesh_001", "mesh_002"], ...}
        """
        mapping = {}
        
        for part in cleaned_parts:
            bom_code = part.get("bom_code")
            mesh_id = part.get("mesh_id")
            
            if bom_code and mesh_id:
                if bom_code not in mapping:
                    mapping[bom_code] = []
                mapping[bom_code].append(mesh_id)
        
        return mapping


# 便捷函数
def match_bom_to_3d(bom_data: List[Dict], parts_list: List[Dict]) -> Dict:
    """
    便捷函数：匹配BOM表和3D零件列表
    
    Args:
        bom_data: BOM表数据
        parts_list: 3D零件列表
        
    Returns:
        匹配结果
    """
    matcher = BOM3DMatcher()
    return matcher.match_parts(bom_data, parts_list)

