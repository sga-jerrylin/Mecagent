"""
分析组件STEP文件
"""

import trimesh
from pathlib import Path

def analyze_step_file(step_path):
    """分析单个STEP文件"""
    print(f"\n{'='*80}")
    print(f"分析: {step_path.name}")
    print(f"{'='*80}")
    
    try:
        # 加载STEP文件
        scene = trimesh.load(str(step_path))
        
        # 获取所有零件
        if isinstance(scene, trimesh.Scene):
            parts = []

            # 直接从geometry字典获取所有几何体
            for geometry_name in scene.geometry.keys():
                parts.append({
                    'node_name': geometry_name,  # 简化：使用几何体名称作为节点名称
                    'geometry_name': geometry_name
                })

            print(f"✅ 零件数: {len(parts)}")

            # 显示前10个零件
            print(f"\n前10个零件:")
            for i, part in enumerate(parts[:10], 1):
                print(f"{i}. {part['geometry_name'][:80]}")

            return parts
        else:
            print(f"⚠️  不是Scene对象，是单个Mesh")
            return []
    
    except Exception as e:
        print(f"❌ 加载失败: {e}")
        return []


def main():
    step_dir = Path("step-stl文件")
    
    # 分析所有STEP文件
    all_parts = {}
    
    for step_file in step_dir.glob("*.STEP"):
        parts = analyze_step_file(step_file)
        all_parts[step_file.stem] = parts
    
    # 统计
    print(f"\n{'='*80}")
    print("总结")
    print(f"{'='*80}")
    
    total_parts = sum(len(parts) for parts in all_parts.values())
    print(f"\n总零件数: {total_parts}")
    
    for name, parts in all_parts.items():
        print(f"  - {name}: {len(parts)} 个零件")
    
    # 检查是否有重复
    print(f"\n{'='*80}")
    print("重复检查")
    print(f"{'='*80}")
    
    # 收集所有零件名称
    all_part_names = []
    for name, parts in all_parts.items():
        for part in parts:
            all_part_names.append((name, part['geometry_name']))
    
    # 检查产品总装中的零件是否包含在组件中
    if '产品测试' in all_parts and len(all_parts) > 1:
        product_parts = set(p['geometry_name'] for p in all_parts['产品测试'])
        component_parts = set()
        
        for name, parts in all_parts.items():
            if name != '产品测试':
                for part in parts:
                    component_parts.add(part['geometry_name'])
        
        overlap = product_parts & component_parts
        print(f"\n产品总装零件数: {len(product_parts)}")
        print(f"组件零件总数: {len(component_parts)}")
        print(f"重复零件数: {len(overlap)}")
        
        if len(overlap) > 0:
            print(f"\n前10个重复零件:")
            for i, part_name in enumerate(list(overlap)[:10], 1):
                print(f"{i}. {part_name[:80]}")


if __name__ == "__main__":
    main()

