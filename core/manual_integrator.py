"""
装配说明书数据整合模块
职责：整合所有子智能体的输出，生成最终的完整JSON
"""

import json
from typing import Dict, List, Any
from datetime import datetime


def generate_3d_params(assembly_steps: List[Dict], bom_to_mesh_mapping: Dict[str, List[str]]) -> List[Dict]:
    """
    为每个装配步骤自动生成3D参数
    
    Args:
        assembly_steps: 装配步骤列表
        bom_to_mesh_mapping: BOM代号到mesh_id的映射
        
    Returns:
        带3D参数的装配步骤列表
    """
    # 预定义的相机角度
    CAMERA_ANGLES = {
        'front': {'position': [0, 0, 10], 'target': [0, 0, 0]},
        'top': {'position': [0, 10, 0], 'target': [0, 0, 0]},
        'side': {'position': [10, 0, 0], 'target': [0, 0, 0]},
        'isometric': {'position': [7, 7, 7], 'target': [0, 0, 0]}
    }
    
    for idx, step in enumerate(assembly_steps):
        # 1. 自动查找mesh_id
        mesh_ids = []
        for part in step.get('parts_used', []):
            bom_code = part.get('bom_code')
            if bom_code and bom_code in bom_to_mesh_mapping:
                mesh_ids.extend(bom_to_mesh_mapping[bom_code])
        
        # 去重
        mesh_ids = list(set(mesh_ids))
        step['3d_highlight'] = mesh_ids
        
        # 2. 自动设置相机角度（简单规则）
        if idx == 0:
            step['camera_angle'] = 'front'  # 第一步：正面
        elif idx == len(assembly_steps) - 1:
            step['camera_angle'] = 'isometric'  # 最后一步：等轴测（看整体）
        else:
            step['camera_angle'] = 'isometric'  # 中间步骤：等轴测
        
        # 3. 自动设置爆炸偏移（用于爆炸图动画）
        step['explosion_offset'] = [0, idx * 0.8, 0]  # 每步向上偏移0.8个单位
    
    return assembly_steps


def generate_product_overview(bom_data: List[Dict], vision_result: Dict) -> Dict:
    """
    生成产品总览
    
    Args:
        bom_data: BOM表数据
        vision_result: 视觉分析结果
        
    Returns:
        产品总览字典
    """
    vision_overview = vision_result.get('product_overview', {})
    
    # 统计零件数量
    total_parts = len(bom_data)
    main_parts = len([item for item in bom_data if str(item.get('code', '')).startswith('01.')])
    standard_parts = total_parts - main_parts
    
    # 计算总重量
    total_weight = sum(item.get('weight', 0) * item.get('qty', 1) for item in bom_data)
    
    return {
        "product_name": vision_overview.get('product_name', '未知产品'),
        "product_type": vision_overview.get('product_type', '机械装配'),
        "drawing_number": "待补充",  # 可以从PDF文件名提取
        "version": "1.0",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_parts": total_parts,
        "main_parts": main_parts,
        "standard_parts": standard_parts,
        "total_weight_kg": round(total_weight, 2),
        "complexity": vision_overview.get('complexity', '中等'),
        "estimated_time_hours": estimate_assembly_time(bom_data),
        "main_structure": vision_overview.get('main_structure', ''),
        "working_principle": vision_overview.get('working_principle', '')
    }


def estimate_assembly_time(bom_data: List[Dict]) -> float:
    """
    估算装配时间（小时）
    
    简单规则：
    - 主要结构件：每个30分钟
    - 标准件：每个5分钟
    """
    main_parts = [item for item in bom_data if str(item.get('code', '')).startswith('01.')]
    standard_parts = [item for item in bom_data if not str(item.get('code', '')).startswith('01.')]
    
    main_time = len(main_parts) * 0.5  # 30分钟 = 0.5小时
    standard_time = len(standard_parts) * 0.08  # 5分钟 = 0.08小时
    
    total_hours = main_time + standard_time
    return round(total_hours, 1)


def generate_bom_with_3d(bom_data: List[Dict], bom_to_mesh_mapping: Dict[str, List[str]]) -> List[Dict]:
    """
    生成带3D映射的BOM表
    
    Args:
        bom_data: BOM表数据
        bom_to_mesh_mapping: BOM代号到mesh_id的映射
        
    Returns:
        带mesh_ids字段的BOM表
    """
    bom_with_3d = []
    
    for item in bom_data:
        bom_code = item.get('code')
        bom_item = {
            "id": item.get('seq', ''),
            "seq": item.get('seq', ''),
            "code": bom_code,
            "name": item.get('name', ''),
            "specification": item.get('specification', ''),
            "quantity": item.get('qty', 1),
            "weight": item.get('weight', 0),
            "material": item.get('material', ''),
            "mesh_ids": bom_to_mesh_mapping.get(bom_code, [])
        }
        bom_with_3d.append(bom_item)
    
    return bom_with_3d


def integrate_manual_data(
    vision_result: Dict,
    bom_data: List[Dict],
    bom_to_mesh_mapping: Dict[str, List[str]],
    assembly_steps: List[Dict] = None,
    welding_requirements: List[Dict] = None,
    quality_checkpoints: List[Dict] = None,
    safety_warnings: List[Dict] = None,
    faq_items: List[Dict] = None
) -> Dict:
    """
    整合所有数据，生成最终的装配说明书JSON

    Args:
        vision_result: 视觉分析结果
        bom_data: BOM表数据
        bom_to_mesh_mapping: BOM代号到mesh_id的映射
        assembly_steps: 装配步骤（来自智能体3-1）
        welding_requirements: 焊接要求（来自智能体3-2）
        quality_checkpoints: 质量检验点（来自智能体3-3）
        safety_warnings: 安全警告（来自智能体3-4）
        faq_items: 常见问题（来自智能体3-4）

    Returns:
        完整的装配说明书JSON
    """
    # 1. 生成产品总览
    product_overview = generate_product_overview(bom_data, vision_result)
    
    # 2. 生成带3D映射的BOM表
    bom_with_3d = generate_bom_with_3d(bom_data, bom_to_mesh_mapping)
    
    # 3. 为装配步骤添加3D参数
    if assembly_steps:
        assembly_steps = generate_3d_params(assembly_steps, bom_to_mesh_mapping)
    else:
        assembly_steps = []
    
    # 4. 整合所有数据
    manual_data = {
        "product_overview": product_overview,
        "bom_items": bom_with_3d,
        "assembly_steps": assembly_steps,
        "welding_requirements": welding_requirements or [],
        "quality_checkpoints": quality_checkpoints or [],
        "safety_warnings": safety_warnings or [],
        "faq_items": faq_items or [],
        "technical_drawings": [],  # 可以从PDF提取缩略图
        "3d_model": {
            "glb_path": "待补充",  # 需要传入GLB文件路径
            "total_meshes": len(set([mesh for meshes in bom_to_mesh_mapping.values() for mesh in meshes])),
            "camera_angles": {
                'front': {'position': [0, 0, 10], 'target': [0, 0, 0]},
                'top': {'position': [0, 10, 0], 'target': [0, 0, 0]},
                'side': {'position': [10, 0, 0], 'target': [0, 0, 0]},
                'isometric': {'position': [7, 7, 7], 'target': [0, 0, 0]}
            }
        },
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "generator_version": "1.0",
            "data_sources": {
                "vision_analysis": "Qwen-VL",
                "assembly_planning": "DeepSeek" if assembly_steps else "未生成",
                "welding_translation": "DeepSeek" if welding_requirements else "未生成",
                "quality_control": "DeepSeek" if quality_checkpoints else "未生成",
                "safety_faq": "DeepSeek" if safety_warnings or faq_items else "未生成"
            }
        }
    }
    
    return manual_data


def save_manual_json(manual_data: Dict, output_path: str):
    """
    保存装配说明书JSON到文件
    
    Args:
        manual_data: 装配说明书数据
        output_path: 输出文件路径
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(manual_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 装配说明书已保存到: {output_path}")
    print(f"   - 产品名称: {manual_data['product_overview']['product_name']}")
    print(f"   - 零件总数: {manual_data['product_overview']['total_parts']}")
    print(f"   - 装配步骤: {len(manual_data['assembly_steps'])} 步")
    print(f"   - 焊接要求: {len(manual_data['welding_requirements'])} 项")
    print(f"   - 安全警告: {len(manual_data['safety_warnings'])} 条")
    print(f"   - 常见问题: {len(manual_data['faq'])} 个")


# 测试函数
if __name__ == "__main__":
    # 测试数据
    test_bom = [
        {"seq": "1", "code": "01.09.2549", "name": "后座组件", "qty": 1, "weight": 77.27},
        {"seq": "2", "code": "01.09.2550", "name": "连接架组件", "qty": 1, "weight": 59.64}
    ]
    
    test_mapping = {
        "01.09.2549": ["mesh_001", "mesh_002"],
        "01.09.2550": ["mesh_003"]
    }
    
    test_vision = {
        "product_overview": {
            "product_name": "推雪板",
            "product_type": "工程机械",
            "complexity": "中等"
        }
    }
    
    test_steps = [
        {
            "step_number": 1,
            "title": "安装后座组件",
            "parts_used": [{"bom_code": "01.09.2549", "bom_name": "后座组件"}]
        }
    ]
    
    # 整合数据
    manual = integrate_manual_data(
        vision_result=test_vision,
        bom_data=test_bom,
        bom_to_mesh_mapping=test_mapping,
        assembly_steps=test_steps
    )
    
    print(json.dumps(manual, ensure_ascii=False, indent=2))

