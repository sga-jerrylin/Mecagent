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

        # ✅ 调试：打印前3个BOM和3D零件的数据
        if bom_data:
            print(f"\n📝 BOM数据示例（前3个）:")
            for i, bom in enumerate(bom_data[:3]):
                print(f"   {i+1}. code: {bom.get('code')}, name: {bom.get('name')}, product_code: {bom.get('product_code')}")

        if parts_list:
            print(f"\n📝 3D零件示例（前3个）:")
            for i, part in enumerate(parts_list[:3]):
                print(f"   {i+1}. node_name: {part.get('node_name')}, geometry_name: {part.get('geometry_name')}")

        # 构建BOM索引（按代号、产品代号和规格）
        bom_by_code = {}
        bom_by_product_code = {}  # ✅ 新增：按产品代号索引
        bom_by_spec = {}

        for bom_item in bom_data:
            code = bom_item.get("code", "")
            name = bom_item.get("name", "")
            product_code = bom_item.get("product_code", "")

            # 按代号索引
            if code:
                bom_by_code[code] = bom_item

            # ✅ 新增：按产品代号索引
            if product_code:
                bom_by_product_code[product_code] = bom_item

            # 按规格索引（用于标准件）
            # 优先从product_code提取规格，其次从name提取
            spec = self.extract_spec_from_name(product_code) or self.extract_spec_from_name(name)
            if spec:
                if spec not in bom_by_spec:
                    bom_by_spec[spec] = []
                bom_by_spec[spec].append(bom_item)

        print(f"✅ BOM索引构建完成: {len(bom_by_code)} 个代号, {len(bom_by_product_code)} 个产品代号, {len(bom_by_spec)} 个规格")
        
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
            
            # 方法1: 通过BOM代号匹配（01.09.2549格式）
            code = self.extract_code_from_name(fixed_name)
            if code and code in bom_by_code:
                matched_bom = bom_by_code[code]
                match_method = "代号匹配"
                confidence = 0.95
                matched_count += 1

            # ✅ 方法2: 通过产品代号匹配（T-SPV250-Z602-01-01-Q355B格式）
            if not matched_bom:
                # 尝试从geometry_name中提取产品代号
                # 策略：检查geometry_name是否包含BOM的product_code
                # 或者BOM的product_code是否包含在geometry_name中
                best_match = None
                best_match_length = 0

                for product_code, bom_item in bom_by_product_code.items():
                    # 跳过太短的product_code（如M8*80）
                    if len(product_code) < 5:
                        continue

                    # 检查是否匹配（不区分大小写）
                    if product_code.upper() in geometry_name.upper() or product_code.upper() in fixed_name.upper():
                        # 选择最长的匹配（更精确）
                        if len(product_code) > best_match_length:
                            best_match = bom_item
                            best_match_length = len(product_code)

                if best_match:
                    matched_bom = best_match
                    match_method = "产品代号匹配"
                    confidence = 0.90
                    matched_count += 1

            # 方法3: 通过规格匹配（标准件，如M8*20）
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
        
        # ========== 统计（显示两个匹配率） ==========

        # 生成BOM到mesh_id的映射表
        bom_to_mesh_mapping = self.generate_bom_to_mesh_mapping(cleaned_parts)

        # ✅ 分离已匹配和未匹配的零件（用于AI匹配）
        matched_parts = [part for part in cleaned_parts if part.get("bom_code")]
        unmatched_parts = [part for part in cleaned_parts if not part.get("bom_code")]

        # 计算两个匹配率
        total_3d_parts = len(parts_list)
        matched_3d_count = len(matched_parts)  # 匹配成功的3D零件数
        parts_matching_rate = matched_3d_count / total_3d_parts if total_3d_parts else 0

        total_bom_count = len(bom_data)
        bom_matched_count = len(bom_to_mesh_mapping)  # 匹配成功的BOM数
        bom_matching_rate = bom_matched_count / total_bom_count if total_bom_count else 0

        # ✅ 显示两个匹配率
        print(f"\n📊 匹配结果统计:")
        print(f"   (1) BOM匹配率: {bom_matched_count}/{total_bom_count} ({bom_matching_rate*100:.1f}%)")
        print(f"   (2) 3D零件匹配率: {matched_3d_count}/{total_3d_parts} ({parts_matching_rate*100:.1f}%)")

        # ✅ 显示一对多映射统计
        one_to_many_count = sum(1 for meshes in bom_to_mesh_mapping.values() if len(meshes) > 1)
        total_mapped_parts = sum(len(meshes) for meshes in bom_to_mesh_mapping.values())
        avg_parts_per_bom = total_mapped_parts / bom_matched_count if bom_matched_count else 0

        print(f"\n📋 一对多映射统计:")
        print(f"   - 一对多BOM数: {one_to_many_count}/{bom_matched_count}")
        print(f"   - 平均每个BOM对应: {avg_parts_per_bom:.1f} 个3D零件")

        # ✅ 显示数量验证（检查BOM qty与实际匹配的3D零件数是否一致）
        qty_mismatch_count = 0
        for bom_code, mesh_ids in bom_to_mesh_mapping.items():
            bom_item = bom_by_code.get(bom_code)
            if bom_item:
                expected_qty = bom_item.get('quantity', 1)
                actual_qty = len(mesh_ids)
                if expected_qty != actual_qty:
                    qty_mismatch_count += 1

        if qty_mismatch_count > 0:
            print(f"   ⚠️  数量不一致的BOM: {qty_mismatch_count}/{bom_matched_count}")
        else:
            print(f"   ✅ 所有BOM数量验证通过")

        # ✅ 新增：生成BOM映射宽表（包含完整的映射链条）
        bom_mapping_table = self.generate_bom_mapping_table(bom_data, cleaned_parts)

        return {
            "summary": {
                "total_3d_parts": total_3d_parts,
                "matched_3d_count": matched_3d_count,  # ✅ 匹配成功的3D零件数
                "unmatched_3d_count": total_3d_parts - matched_3d_count,
                "parts_matching_rate": parts_matching_rate,  # ✅ 3D零件匹配率
                # ✅ BOM匹配统计
                "total_bom_count": total_bom_count,
                "bom_matched_count": bom_matched_count,  # ✅ 匹配成功的BOM数
                "bom_matching_rate": bom_matching_rate,  # ✅ BOM匹配率
                # ✅ 一对多映射统计
                "one_to_many_count": one_to_many_count,
                "avg_parts_per_bom": avg_parts_per_bom,
                "qty_mismatch_count": qty_mismatch_count,
                # ✅ 兼容旧代码的字段
                "matched_count": matched_3d_count,
                "matching_rate": parts_matching_rate
            },
            "cleaned_parts": cleaned_parts,
            "matched_parts": matched_parts,  # ✅ 已匹配的零件
            "unmatched_parts": unmatched_parts,  # ✅ 未匹配的零件
            "bom_to_mesh_mapping": bom_to_mesh_mapping,
            "bom_mapping_table": bom_mapping_table  # ✅ 新增：BOM映射宽表
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

    def generate_bom_mapping_table(self, bom_data: List[Dict], cleaned_parts: List[Dict]) -> List[Dict]:
        """
        生成BOM映射宽表（包含完整的映射链条）

        映射链条：
        BOM序号(seq) → BOM代号(code) → 产品代号(product_code)
                    → STEP几何体名称(geometry_name) → GLB节点(mesh_id)

        Args:
            bom_data: BOM表数据
            cleaned_parts: 清洗后的零件列表

        Returns:
            宽表列表，每个元素包含完整的映射信息
        """
        # 按BOM代号分组cleaned_parts
        parts_by_bom_code = {}
        for part in cleaned_parts:
            bom_code = part.get("bom_code")
            if bom_code:
                if bom_code not in parts_by_bom_code:
                    parts_by_bom_code[bom_code] = []
                parts_by_bom_code[bom_code].append(part)

        # 构建宽表
        mapping_table = []

        for bom_item in bom_data:
            seq = bom_item.get("seq", "")
            code = bom_item.get("code", "")
            product_code = bom_item.get("product_code", "")
            name = bom_item.get("name", "")
            quantity = bom_item.get("quantity", 1)

            # 查找匹配的3D零件
            matched_parts = parts_by_bom_code.get(code, [])

            if matched_parts:
                # 提取几何体名称和mesh_id
                geometry_names = [p.get("fixed_name", p.get("geometry_name", "")) for p in matched_parts]
                mesh_ids = [p.get("mesh_id") for p in matched_parts]
                node_names = [p.get("node_name") for p in matched_parts]

                mapping_table.append({
                    "seq": seq,
                    "code": code,
                    "product_code": product_code,
                    "name": name,
                    "quantity": quantity,
                    "geometry_names": geometry_names,
                    "mesh_ids": mesh_ids,
                    "node_names": node_names,
                    "matched": True
                })
            else:
                # 未匹配的BOM项
                mapping_table.append({
                    "seq": seq,
                    "code": code,
                    "product_code": product_code,
                    "name": name,
                    "quantity": quantity,
                    "geometry_names": [],
                    "mesh_ids": [],
                    "node_names": [],
                    "matched": False
                })

        return mapping_table


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

