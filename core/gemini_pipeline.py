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

    def __init__(self, api_key: str, output_dir: str = "pipeline_output", product_name: str = "", model_name: str = None):
        """
        初始化工作流

        Args:
            api_key: OpenRouter API密钥
            output_dir: 输出目录
            product_name: 产品名称（用户输入）
            model_name: AI模型名称（可选，如果不提供则从环境变量读取）
        """
        self.api_key = api_key
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.product_name = product_name  # ✅ 保存产品名称
        self.model_name = model_name or os.getenv("OPENROUTER_MODEL") or "google/gemini-2.0-flash-exp:free"

        # 设置API密钥和模型名称到环境变量
        os.environ["OPENROUTER_API_KEY"] = api_key
        os.environ["OPENROUTER_MODEL"] = self.model_name

        print(f"🤖 Pipeline 初始化 - 使用模型: {self.model_name}")

        # 初始化复用的Core组件
        self.file_classifier = FileClassifier()
        self.bom_matcher = HierarchicalBOMMatcher()
        self.integrator = ManualIntegratorV2(product_name=product_name)  # ✅ 传入产品名称

        # 初始化6个Agent - 传入model_name确保使用正确的模型
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
            file_hierarchy, image_hierarchy = self._step1_classify_and_convert(pdf_dir, step_dir)

            # 步骤2: 从PDF提取BOM数据
            self.current_step = 2
            bom_data = self._step2_extract_bom_from_pdfs(file_hierarchy)

            # 步骤3: Agent 1 - 视觉规划
            self.current_step = 3
            planning_result = self._step3_vision_planning(image_hierarchy, bom_data, file_hierarchy)
            
            # ========== 支路2: 3D处理 ==========
            # 步骤4: Agent 2 - BOM-3D匹配
            self.current_step = 4
            matching_result = self._step4_bom_3d_matching(
                step_dir, bom_data, planning_result, file_hierarchy
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
                matching_result, image_hierarchy  # ✅ 传入图片层级结构
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
    
    def _step1_classify_and_convert(self, pdf_dir: str, step_dir: str = None) -> tuple:
        """步骤1: 文件分类 + PDF转图片"""
        print_substep(f"[{self.current_step}/{self.total_steps}] 📂 文件管理员")

        self.log_agent_call("文件管理", "查看文件夹里有哪些图纸", "running")

        pdf_path = Path(pdf_dir)
        # ✅ Bug修复：同时扫描大写和小写的PDF文件
        pdf_files = [str(f) for f in pdf_path.glob("*.pdf")] + [str(f) for f in pdf_path.glob("*.PDF")]

        print_info(f"📄 他发现了 {len(pdf_files)} 个PDF图纸", indent=1)
        import sys
        sys.stdout.flush()

        self.log_agent_call("文件管理", "分辨哪些是产品总图，哪些是组件图", "running")

        # 获取STEP文件列表
        step_files = []
        if step_dir:
            step_path = Path(step_dir)
            step_files = [str(f) for f in step_path.glob("*.STEP")] + [str(f) for f in step_path.glob("*.step")] + [str(f) for f in step_path.glob("*.stp")]

        file_hierarchy = self.file_classifier.classify_files(pdf_files, step_files)

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
        """步骤2: 从PDF提取BOM数据（使用Gemini Vision API）"""
        print_substep(f"[{self.current_step}/{self.total_steps}] 📊 BOM数据分析员")

        self.log_agent_call("BOM分析", "从图纸中读取零件清单", "running")

        all_bom_items = []

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

        # 从每个PDF提取BOM（使用Gemini Vision API）
        for pdf_path in all_pdfs:
            pdf_name = Path(pdf_path).name
            print_info(f"   📖 正在阅读: {pdf_name}", indent=1)
            sys.stdout.flush()

            try:
                # 使用Gemini Vision API提取BOM
                bom_items = self._extract_bom_with_vision(pdf_path, pdf_name)

                if bom_items:
                    all_bom_items.extend(bom_items)
                    pdf_bom_counts[pdf_name] = len(bom_items)
                    print_success(f"      提取到 {len(bom_items)} 个零件", indent=1)
                else:
                    pdf_bom_counts[pdf_name] = 0
                    print_warning(f"      未提取到零件", indent=1)

                sys.stdout.flush()

            except Exception as e:
                print_warning(f"   ⚠️  {pdf_name} 读取失败: {e}", indent=1)
                pdf_bom_counts[pdf_name] = 0
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

    def _extract_bom_with_vision(self, pdf_path: str, pdf_name: str) -> List[Dict]:
        """使用Gemini Vision API从PDF中提取BOM表"""
        import fitz
        import base64
        import io
        from PIL import Image

        # 将PDF转换为图片
        doc = fitz.open(pdf_path)
        images = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x缩放
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            # 转换为base64
            buffered = io.BytesIO()
            img.save(buffered, format="PNG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode()
            images.append(img_base64)

        doc.close()

        # 调用Gemini Vision API
        prompt = """# 任务：从工程图纸中提取BOM表（零件清单/明细表）

## 1. 如何识别BOM表

### ⚠️ 关键识别特征（必须同时满足）：

1. **必须有"代号"列**，格式为 `XX.XX.XXXX` 或 `XX.XX.XX.XXXXX`
   - 示例：`01.09.0410`, `02.03.0008`, `02.08.02.0263`
   - **如果表格中没有这种格式的代号，那就不是BOM表！**

2. **必须有"序号"列**，数字从1开始（1, 2, 3...）
   - 序号可能从上到下排列（1在上，38在下）
   - 序号也可能从下到上排列（1在下，38在上）

3. **必须有"名称"列**，包含零件名称

### ❌ 不是BOM表的例子：

**工艺路线表**（不要提取）：
```
| 序号 | 工序号 | 名称 | 设备 |
|  1   | 08.04  | 焊丸  |      |
|  2   | 01.13  | 喷漆  |      |
```
- ❌ 这个表格的"工序号"列（08.04, 01.13）**不是BOM代号**
- ❌ 工序号只有2段（XX.XX），而BOM代号至少有3段（XX.XX.XXXX）
- ❌ 这是工艺流程表，不是零件清单

**BOM表**（需要提取）：
```
| 序号 | 代号 | 产品代号 | 名称 | 数量 | 重量 |
|  1   | 01.09.0410 | T-AB1830(72IN)-EURO-01 | 挂架组件-漆后 | 1 | 4.71 |
|  2   | 01.09.0408 | ... | 主框架组件-漆后 | 1 | 3.01 |
```
- ✅ "代号"列是 `01.09.0410`（至少3段，XX.XX.XXXX格式）
- ✅ 这是零件清单

## 2. BOM表的详细特征

**表格位置**：通常在图纸的右下角、右侧或下方

**表格结构**（从左到右的列）：
```
| 序号 | 代号 | 产品代号/规格 | 名称 | 数量 | 单重 | 总重 |
```

**字段说明**：
1. **序号**：1, 2, 3, 4...（可能从下往上排列）
2. **代号**（BOM号）：
   - 标准格式：`01.09.0410`, `02.03.0008`, `01.04.0145`
   - 4段格式：`02.08.02.0263`
   - **至少3段**（XX.XX.XXXX），必须以数字开头，包含点号分隔
3. **产品代号**：可能包含：
   - 英文字母和数字：`T-AB1830(72IN)-EURO-01`, `S-RB1830-07`
   - 规格型号：`M8*60`, `M12*35`, `10*2`, `φ4.5*10`
   - 中文描述：`标准型性能8级8.8GB/T5781-2016`
4. **名称**：零件名称（可能是中文或英文），如：
   - 中文：`挂架组件-漆后`, `六角头螺栓全螺纹8.8级GB/T5781-2016`, `销轴-镀锌`
   - 英文：`WARNING-FLYING OBJECTS AND PINCH POINTS`, `WARNING-HIGH PRESSURE FLUID HAZARD`, `DANGER-PINCH POINTS`
   - ⚠️ **重要**：以`WARNING`或`DANGER`开头的也是**有效的产品名称**，必须提取！
5. **数量**：整数（1, 2, 4, 12, 38等）
6. **重量**：浮点数，单位kg（76.42, 0.29, 3.65, 0.00等）

**需要跳过的行**：
- 表头行（如：`序号`, `代号`, `名称`, `数量`, `重量`等）
- 没有代号的行（代号列为空的行）
- 没有序号的行（序号列为空的行）
- 代号格式不对的行（如：只有2段的工序号 `08.04`, `01.13`）

## 3. 提取规则

### 3.1 第一步：识别BOM表
1. **在所有页面中查找表格**（BOM表可能在任何一页）
2. **检查表格是否有"代号"列**：
   - 代号必须是 `XX.XX.XXXX` 格式（至少3段）
   - 如果只有2段（如 `08.04`, `01.13`），那是工序号，不是BOM代号
3. **确认是BOM表后，再提取数据**

### 3.2 第二步：逐行提取
1. **提取所有有效行**：
   - 必须有序号（1-200之间的数字）
   - 必须有代号（XX.XX.XXXX或XX.XX.XX.XXXXX格式，至少3段）
   - **不要跳过任何有序号和代号的行**，即使名称是英文的WARNING或DANGER

2. **字段提取**：
   - `seq`：序号（字符串）
   - `code`：代号（必须是XX.XX.XXXX格式，至少3段）
   - `product_code`：产品代号/规格（可能为空，使用空字符串""）
   - `name`：名称（中文或英文零件名称，可能为空，使用空字符串""）
   - `quantity`：数量（整数）
   - `weight`：总重（浮点数，如果有单重和总重两列，取总重；如果只有一列重量，就取那一列）

3. **完整性要求**：
   - ⚠️ **提取所有行**：如果BOM表有38行，必须提取所有38行
   - ⚠️ **不要遗漏**：即使某些字段难以识别，也要提取该行
   - ⚠️ **按序号排序**：最终结果按序号从小到大排列（1, 2, 3...）

## 4. 输出格式

直接返回JSON数组，**不要添加任何解释性文字**：

```json
[
  {
    "seq": "1",
    "code": "01.09.2154",
    "product_code": "S-AB1830(72IN)-MP1140-01",
    "name": "挂架组件-漆后",
    "quantity": 1,
    "weight": 76.42
  },
  {
    "seq": "31",
    "code": "02.21.0112",
    "product_code": "",
    "name": "WARNING-FLYING OBJECTS AND PINCH POINTS",
    "quantity": 2,
    "weight": 0.00
  },
  {
    "seq": "32",
    "code": "02.21.0109",
    "product_code": "",
    "name": "DANGER-PINCH POINTS",
    "quantity": 1,
    "weight": 0.00
  }
]
```

## 5. 关键提示

- ✅ **查看所有页面**，BOM表可能在任何一页（通常在右下角）
- ✅ **先识别BOM表**：必须有"代号"列（XX.XX.XXXX格式，至少3段）
- ✅ **不要提取工艺路线表**：工序号只有2段（XX.XX），不是BOM代号
- ✅ **注意序号可能从下往上排列**（序号1在最下面）
- ✅ **提取所有有效行**，不要遗漏任何零件
- ✅ **WARNING和DANGER开头的也是有效的产品名称**，必须提取
- ✅ **只跳过表头**，不要跳过任何有序号和代号的数据行
- ✅ **确保JSON格式正确**，可以被直接解析
- ✅ **如果图纸中没有BOM表，返回空数组** `[]`
"""

        try:
            # ✅ 将所有页面一起发送给模型（而不是逐页发送）
            print_info(f"      正在分析 {len(images)} 页图纸...", indent=1)

            # 构建包含所有页面的消息
            content = [{"type": "text", "text": prompt}]
            for img_base64 in images:
                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{img_base64}"
                    }
                })

            response = self.vision_agent.client.chat.completions.create(
                model=self.vision_agent.model_name,
                messages=[
                    {
                        "role": "user",
                        "content": content
                    }
                ],
                temperature=0.1,
                max_tokens=8000  # 增加token限制以处理多页
            )

            result_text = response.choices[0].message.content.strip()

            # 提取JSON部分
            import json
            import re

            # 尝试提取JSON数组
            json_match = re.search(r'\[.*\]', result_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)

                try:
                    bom_items = json.loads(json_str)

                    if bom_items:
                        print_info(f"         找到 {len(bom_items)} 个零件", indent=1)
                    else:
                        print_info(f"         未找到BOM表", indent=1)

                    # 添加source_pdf字段
                    for item in bom_items:
                        item["source_pdf"] = pdf_name

                    return bom_items

                except json.JSONDecodeError as json_err:
                    # JSON解析失败，尝试修复常见问题
                    print_warning(f"      JSON解析失败: {json_err}", indent=1)
                    print_warning(f"      尝试修复JSON格式...", indent=1)

                    # 保存原始响应用于调试
                    debug_file = self.output_dir / f"debug_bom_response_{pdf_name}.txt"
                    with open(debug_file, "w", encoding="utf-8") as f:
                        f.write(f"原始响应:\n{result_text}\n\n")
                        f.write(f"提取的JSON:\n{json_str}\n\n")
                        f.write(f"错误信息:\n{json_err}\n")

                    print_info(f"      调试信息已保存到: {debug_file.name}", indent=1)

                    # 尝试修复JSON（移除尾部逗号、修复引号等）
                    try:
                        fixed_json = json_str

                        # 修复1：移除对象末尾的逗号（如：{"key": "value",}）
                        fixed_json = re.sub(r',\s*}', '}', fixed_json)

                        # 修复2：移除数组末尾的逗号（如：[1, 2, 3,]）
                        fixed_json = re.sub(r',\s*\]', ']', fixed_json)

                        # 修复3：修复数字后多余的引号（如："quantity": 1"）
                        # 匹配模式：数字后面跟着引号和逗号或换行
                        fixed_json = re.sub(r':\s*(\d+)"\s*([,\n])', r': \1\2', fixed_json)

                        # 修复4：修复浮点数后多余的引号（如："weight": 32.12"）
                        fixed_json = re.sub(r':\s*(\d+\.\d+)"\s*([,\n}])', r': \1\2', fixed_json)

                        bom_items = json.loads(fixed_json)
                        print_success(f"      JSON修复成功！找到 {len(bom_items)} 个零件", indent=1)

                        # 添加source_pdf字段
                        for item in bom_items:
                            item["source_pdf"] = pdf_name

                        return bom_items
                    except Exception as fix_err:
                        print_warning(f"      JSON修复失败: {fix_err}", indent=1)
                        return []
            else:
                print_info(f"         未找到BOM表", indent=1)
                return []

        except Exception as e:
            print_warning(f"      Vision API调用失败: {e}", indent=1)
            import traceback
            traceback.print_exc()
            return []

    def _step3_vision_planning(self, image_hierarchy: Dict, bom_data: List[Dict], file_hierarchy: Dict) -> Dict:
        """步骤3: Agent 1 - 视觉规划"""
        print_substep(f"[{self.current_step}/{self.total_steps}] 🔍 装配规划师")

        self.log_agent_call("装配规划", "研究图纸，规划装配顺序", "running")

        # 收集所有图片
        all_images = []
        all_images.extend(image_hierarchy.get("product_images", []))
        for comp_images in image_hierarchy.get("component_images", {}).values():
            all_images.extend(comp_images)

        # ✅ 获取实际的组件数量（从file_hierarchy中获取）
        actual_component_count = len(file_hierarchy.get("components", []))

        print_info(f"🖼️  他拿到了 {len(all_images)} 张图片", indent=1)
        print_info(f"📊 他参考了 {len(bom_data)} 个零件的信息", indent=1)
        print_info(f"📁 系统识别出 {actual_component_count} 个组件图文件", indent=1)
        import sys
        sys.stdout.flush()

        self.log_agent_call("装配规划", "使用AI视觉分析图纸", "running")

        # ✅ 传入实际组件数量，确保AI为每个组件生成规划
        planning_result = self.vision_agent.process(all_images, bom_data, actual_component_count)

        if planning_result["success"]:
            component_count = len(planning_result.get("component_assembly_plan", []))
            print_success(f"🎯 他识别出了 {component_count} 个组件", indent=1)

            # ✅ 检查是否所有组件都被规划
            if component_count < actual_component_count:
                print_warning(f"⚠️  警告：只规划了 {component_count}/{actual_component_count} 个组件", indent=1)

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
        self, step_dir: str, bom_data: List[Dict], planning_result: Dict, file_hierarchy: Dict
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
            output_dir=str(self.output_dir / "glb_files"),
            file_hierarchy=file_hierarchy  # ✅ 传入文件层级结构
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
            comp_order = comp_plan.get("assembly_order", 0)

            # ✅ 获取实际的组件图序号（从matching_result中获取）
            drawing_index = comp_order  # 默认值
            if comp_code in component_level_mappings:
                drawing_index = component_level_mappings[comp_code].get("drawing_index", comp_order)

            self.log_agent_call(
                f"组件装配工 #{i}",
                f"编写【{comp_name}】的装配步骤 (图纸序号={drawing_index})",
                "running"
            )
            sys.stdout.flush()

            # ✅ 使用实际的组件图序号获取图纸
            component_images = image_hierarchy.get('component_images', {}).get(str(drawing_index), [])

            if not component_images:
                print_warning(f"未找到组件图{drawing_index}的图片", indent=1)
                # ✅ 标记为跳过状态，确保前端卡片能收到完成信号
                self.log_agent_call(
                    f"组件装配工 #{i}",
                    f"跳过了工作，因为缺少组件图片",
                    "skipped"
                )
                sys.stdout.flush()

                # ✅ 添加一个跳过的结果
                component_results.append({
                    "success": False,
                    "skipped": True,
                    "component_code": comp_code,
                    "component_name": comp_name,
                    "assembly_order": comp_order,
                    "drawing_index": drawing_index,
                    "reason": "缺少组件图片"
                })
                continue

            # ✅ 使用实际的组件图序号获取BOM列表
            # 从file_hierarchy中找到对应的组件图名称
            comp_pdf_name = None
            for comp in file_hierarchy.get("components", []):
                if comp.get("index") == drawing_index:
                    comp_pdf_name = comp.get("name", "")
                    break

            if not comp_pdf_name:
                comp_pdf_name = f"组件图{drawing_index}"

            component_bom = [
                item for item in bom_data
                if item.get("source_pdf", "").startswith(comp_pdf_name)
            ]

            # ✅ 获取组件的BOM-3D映射（宽表和旧格式都获取）
            bom_to_mesh = None
            bom_mapping_table = None

            if comp_code in component_level_mappings:
                bom_to_mesh = component_level_mappings[comp_code].get("bom_to_mesh", {})
                bom_mapping_table = component_level_mappings[comp_code].get("bom_mapping_table", None)

            # 调用Agent 3
            print_info(f"   📖 他正在研究【{comp_name}】的图纸", indent=1)
            print_info(f"   📋 组件BOM: {len(component_bom)} 个零件", indent=1)
            sys.stdout.flush()

            result = self.component_agent.process(
                component_plan=comp_plan,
                component_images=component_images,
                parts_list=component_bom,  # ✅ 传入组件的BOM列表
                bom_to_mesh_mapping=bom_to_mesh,  # 兼容旧代码
                bom_mapping_table=bom_mapping_table  # ✅ 新增：传入BOM映射宽表
            )

            if result["success"]:
                step_count = len(result.get("assembly_steps", []))
                print_success(f"   ✅ 生成了 {step_count} 个装配步骤", indent=1)
                sys.stdout.flush()
                self.log_agent_call(f"组件装配工 #{i}", f"完成了【{comp_name}】的装配说明", "success")
            else:
                self.log_agent_call(f"组件装配工 #{i}", "装配步骤编写", "error")

            # ✅ 添加组件代号、装配顺序和图纸序号到结果中（供后续步骤使用）
            result["component_code"] = comp_code
            result["component_name"] = comp_name
            result["assembly_order"] = comp_order
            result["drawing_index"] = drawing_index  # ✅ 新增：保存实际的组件图序号

            component_results.append(result)

        # ✅ 输出步骤总结
        total_components = len(component_plans)
        successful_components = sum(1 for r in component_results if r.get("success", False))
        skipped_components = sum(1 for r in component_results if r.get("skipped", False))

        print_info(f"\n📊 组件装配工程师工作总结:", indent=1)
        print_info(f"   总组件数: {total_components}", indent=1)
        print_info(f"   成功处理: {successful_components}", indent=1)
        print_info(f"   跳过: {skipped_components}", indent=1)
        sys.stdout.flush()

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
        # ✅ 修改：不排除组件，组件的零件也要参与匹配
        product_bom_all = [
            item for item in bom_data
            if item.get("source_pdf", "").startswith("产品总图")
        ]

        # ✅ 新策略：包含所有BOM项（组件+零件）
        # 原因：产品总装步骤需要高亮组件内的零件，所以组件的零件也要参与匹配
        product_bom = product_bom_all

        # ✅ 获取产品级BOM-3D映射（宽表和旧格式都获取）
        product_bom_to_mesh = matching_result.get("product_level_mapping", {}).get("bom_to_mesh", {})
        product_bom_mapping_table = matching_result.get("product_level_mapping", {}).get("bom_mapping_table", None)

        import sys
        print_info(f"📋 他正在研究产品总图", indent=1)
        print_info(f"📋 产品级BOM: {len(product_bom)} 个零件", indent=1)
        sys.stdout.flush()

        result = self.product_agent.process(
            product_plan=planning_result,
            product_images=product_images,
            components_list=planning_result.get("component_assembly_plan", []),
            product_bom=product_bom,  # ✅ 传入产品级BOM
            bom_to_mesh_mapping=product_bom_to_mesh,  # 兼容旧代码
            bom_mapping_table=product_bom_mapping_table  # ✅ 新增：传入BOM映射宽表
        )

        if result["success"]:
            step_count = len(result.get("assembly_steps", []))
            print_success(f"✅ 生成了 {step_count} 个总装步骤", indent=1)
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
        matching_result: Dict,
        image_hierarchy: Dict  # ✅ 新增参数
    ) -> Dict:
        """
        步骤8: 整合最终手册

        注意：component_results和product_result已经包含了焊接和安全信息
        """
        print_substep(f"[{self.current_step}/{self.total_steps}] 📚 手册编辑员")

        self.log_agent_call("手册编辑", "把所有工程师的成果整合成一本完整的说明书", "running")

        import sys
        sys.stdout.flush()

        # ✅ 构建组件到GLB的映射（使用drawing_index而不是assembly_order）
        component_to_glb_mapping = {}
        component_level_mappings = matching_result.get("component_level_mappings", {})
        glb_files = matching_result.get("glb_files", {})

        # 从component_level_mappings构建映射，使用drawing_index
        for comp_code, mapping in component_level_mappings.items():
            # 从mapping中获取drawing_index
            drawing_index = mapping.get("drawing_index")

            if not drawing_index:
                # 如果没有drawing_index，尝试从component_results中获取
                for comp_result in component_results:
                    if comp_result.get("component_code") == comp_code:
                        drawing_index = comp_result.get("drawing_index")
                        break

            if drawing_index:
                # ✅ 使用实际的组件图序号构建GLB文件名
                glb_filename = f"component_{drawing_index}.glb"
                component_to_glb_mapping[comp_code] = glb_filename

        print_info("📝 他正在整理所有内容...", indent=1)
        sys.stdout.flush()

        # ✅ 使用输出目录名作为task_id
        task_id = self.output_dir.name

        final_manual = self.integrator.integrate(
            planning_result=planning_result,
            component_assembly_results=component_results,
            product_assembly_result=product_result,
            welding_result={},  # 焊接信息已经在步骤中了
            safety_faq_result={},  # 安全信息已经在步骤中了
            component_to_glb_mapping=component_to_glb_mapping,
            component_level_mappings=component_level_mappings,  # ✅ 传入组件级别映射（包含BOM映射表）
            bom_to_mesh_mapping=matching_result.get("product_level_mapping", {}).get("bom_to_mesh", {}),
            image_hierarchy=image_hierarchy,  # ✅ 传入图片层级结构
            task_id=task_id  # ✅ 使用输出目录名作为task_id
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


