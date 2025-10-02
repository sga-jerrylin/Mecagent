#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能装配说明书生成系统 - 后端API服务
基于FastAPI构建的RESTful API
支持WebSocket实时进度推送和并行处理
"""

import os
import sys
import uuid
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import uvicorn

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.pipeline import generate_assembly_manual
from core.parallel_pipeline import ParallelAssemblyPipeline
from models.vision_model import Qwen3VLModel
from models.assembly_expert import AssemblyExpertModel
from processors.file_processor import PDFProcessor, ModelProcessor
from backend.websocket_manager import ws_manager, ProgressReporter

# 创建FastAPI应用
app = FastAPI(
    title="智能装配说明书生成系统",
    description="基于AI的装配说明书自动生成API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件服务
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/output", StaticFiles(directory="output"), name="output")

# 数据模型
class GenerationConfig(BaseModel):
    focus: str = "welding"  # general, welding, precision, heavy
    quality: str = "standard"  # basic, standard, high, critical
    language: str = "zh"  # zh, en
    requirements: str = ""

class GenerationRequest(BaseModel):
    config: GenerationConfig
    pdf_files: List[str]
    model_files: List[str]

class GenerationStatus(BaseModel):
    task_id: str
    status: str  # pending, processing, completed, failed
    progress: int
    message: str
    result: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

# 全局变量
tasks: Dict[str, GenerationStatus] = {}
upload_dir = Path("uploads")
output_dir = Path("output")
api_keys: Dict[str, str] = {
    "dashscope": os.getenv("DASHSCOPE_API_KEY", ""),
    "deepseek": os.getenv("DEEPSEEK_API_KEY", "")
}

# 确保目录存在
upload_dir.mkdir(exist_ok=True)
output_dir.mkdir(exist_ok=True)

# API路由
@app.get("/")
async def root():
    """根路径，返回API信息"""
    return {
        "name": "智能装配说明书生成系统",
        "version": "1.0.0",
        "status": "running",
        "docs": "/api/docs"
    }

@app.get("/api/health")
async def health_check():
    """健康检查"""
    # ✅ 修复: 不初始化AI模型，只检查基本服务状态
    try:
        # 检查API密钥是否配置
        has_dashscope = bool(api_keys.get("dashscope"))
        has_deepseek = bool(api_keys.get("deepseek"))

        # 检查目录是否存在
        upload_dir_exists = upload_dir.exists()
        output_dir_exists = output_dir.exists()

        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "api_server": "running",
                "file_storage": "available" if (upload_dir_exists and output_dir_exists) else "unavailable",
                "dashscope_api_key": "configured" if has_dashscope else "not_configured",
                "deepseek_api_key": "configured" if has_deepseek else "not_configured"
            }
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

class SettingsRequest(BaseModel):
    dashscope_api_key: str
    deepseek_api_key: str

@app.post("/api/settings")
async def update_settings(request: SettingsRequest):
    """更新API密钥设置"""
    try:
        # 更新全局API密钥
        api_keys["dashscope"] = request.dashscope_api_key
        api_keys["deepseek"] = request.deepseek_api_key

        # 更新环境变量
        os.environ["DASHSCOPE_API_KEY"] = request.dashscope_api_key
        os.environ["DEEPSEEK_API_KEY"] = request.deepseek_api_key

        return {
            "success": True,
            "message": "API密钥已更新"
        }
    except Exception as e:
        raise HTTPException(500, f"更新设置失败: {str(e)}")

@app.get("/api/settings")
async def get_settings():
    """获取当前API密钥设置（脱敏）"""
    def mask_key(key: str) -> str:
        if not key or len(key) < 8:
            return "未设置"
        return f"{key[:4]}...{key[-4:]}"

    return {
        "dashscope_api_key": mask_key(api_keys.get("dashscope", "")),
        "deepseek_api_key": mask_key(api_keys.get("deepseek", "")),
        "has_dashscope": bool(api_keys.get("dashscope")),
        "has_deepseek": bool(api_keys.get("deepseek"))
    }

@app.post("/api/upload")
async def upload_files(
    pdf_files: List[UploadFile] = File(...),
    model_files: List[UploadFile] = File(...)
):
    """上传PDF和3D模型文件"""
    try:
        uploaded_files = {
            "pdf_files": [],
            "model_files": []
        }
        
        # 处理PDF文件
        for pdf_file in pdf_files:
            if not pdf_file.filename.lower().endswith('.pdf'):
                raise HTTPException(400, f"文件 {pdf_file.filename} 不是PDF格式")
            
            file_id = str(uuid.uuid4())
            file_path = upload_dir / f"{file_id}_{pdf_file.filename}"
            
            with open(file_path, "wb") as f:
                content = await pdf_file.read()
                f.write(content)
            
            uploaded_files["pdf_files"].append({
                "id": file_id,
                "filename": pdf_file.filename,
                "path": str(file_path),
                "size": len(content)
            })
        
        # 处理3D模型文件（仅支持STEP格式）
        for model_file in model_files:
            ext = model_file.filename.lower().split('.')[-1]
            if ext not in ['step', 'stp']:
                raise HTTPException(400, f"文件 {model_file.filename} 格式不支持，仅支持STEP格式 (.step, .stp)")

            file_id = str(uuid.uuid4())
            file_path = upload_dir / f"{file_id}_{model_file.filename}"

            with open(file_path, "wb") as f:
                content = await model_file.read()
                f.write(content)

            uploaded_files["model_files"].append({
                "id": file_id,
                "filename": model_file.filename,
                "path": str(file_path),
                "size": len(content),
                "format": "STEP"
            })
        
        return {
            "success": True,
            "message": "文件上传成功",
            "data": uploaded_files
        }
        
    except Exception as e:
        raise HTTPException(500, f"文件上传失败: {str(e)}")

@app.post("/api/generate")
async def start_generation(
    request: GenerationRequest,
    background_tasks: BackgroundTasks
):
    """开始生成装配说明书"""
    try:
        # 创建任务ID
        task_id = str(uuid.uuid4())

        # 将文件名转换为完整路径
        pdf_paths = []
        for filename in request.pdf_files:
            matching_files = list(upload_dir.glob(f"*_{filename}"))
            if matching_files:
                pdf_paths.append(str(matching_files[0]))
                print(f"✅ 找到PDF文件: {filename} -> {matching_files[0]}")
            else:
                fallback_path = upload_dir / filename
                pdf_paths.append(str(fallback_path))
                print(f"⚠️  PDF文件未找到UUID版本，使用: {fallback_path}")

        model_paths = []
        for filename in request.model_files:
            matching_files = list(upload_dir.glob(f"*_{filename}"))
            if matching_files:
                model_paths.append(str(matching_files[0]))
                print(f"✅ 找到模型文件: {filename} -> {matching_files[0]}")
            else:
                fallback_path = upload_dir / filename
                model_paths.append(str(fallback_path))
                print(f"⚠️  模型文件未找到UUID版本，使用: {fallback_path}")

        # 初始化任务状态
        task_status = GenerationStatus(
            task_id=task_id,
            status="pending",
            progress=0,
            message="任务已创建，等待处理",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        tasks[task_id] = task_status

        # 添加后台任务
        background_tasks.add_task(
            process_generation,
            task_id,
            request.config,
            pdf_paths,
            model_paths
        )
        
        return {
            "success": True,
            "task_id": task_id,
            "message": "生成任务已启动"
        }
        
    except Exception as e:
        raise HTTPException(500, f"启动生成任务失败: {str(e)}")

@app.get("/api/task/{task_id}")
async def get_task_status(task_id: str):
    """获取任务状态"""
    if task_id not in tasks:
        raise HTTPException(404, "任务不存在")
    
    return tasks[task_id]

@app.get("/api/tasks")
async def list_tasks():
    """获取所有任务列表"""
    return {
        "tasks": list(tasks.values()),
        "total": len(tasks)
    }

@app.get("/api/download/{task_id}")
async def download_result(task_id: str):
    """下载生成结果"""
    if task_id not in tasks:
        raise HTTPException(404, "任务不存在")
    
    task = tasks[task_id]
    if task.status != "completed":
        raise HTTPException(400, "任务尚未完成")
    
    if not task.result or "output_file" not in task.result:
        raise HTTPException(404, "结果文件不存在")
    
    file_path = Path(task.result["output_file"])
    if not file_path.exists():
        raise HTTPException(404, "文件不存在")
    
    return FileResponse(
        path=file_path,
        filename=f"assembly_manual_{task_id}.html",
        media_type="text/html"
    )

@app.delete("/api/task/{task_id}")
async def delete_task(task_id: str):
    """删除任务"""
    if task_id not in tasks:
        raise HTTPException(404, "任务不存在")

    # 清理相关文件
    task = tasks[task_id]
    if task.result and "output_dir" in task.result:
        output_path = Path(task.result["output_dir"])
        if output_path.exists():
            import shutil
            shutil.rmtree(output_path)

    # 删除任务记录
    del tasks[task_id]

    # 清理WebSocket数据
    ws_manager.cleanup_task(task_id)

    return {"success": True, "message": "任务已删除"}

@app.websocket("/ws/task/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str):
    """WebSocket端点 - 实时进度推送"""
    await ws_manager.connect(websocket, task_id)

    try:
        # 保持连接，接收客户端消息（如果需要）
        while True:
            data = await websocket.receive_text()
            # 可以处理客户端发送的消息
            # 例如：暂停、取消任务等

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, task_id)

@app.get("/api/files/{task_id}/{file_path:path}")
async def serve_file(task_id: str, file_path: str):
    """提供任务生成的文件"""
    try:
        # 构建完整文件路径
        full_path = output_dir / task_id / file_path

        if not full_path.exists():
            raise HTTPException(404, f"文件不存在: {file_path}")

        # 检查文件是否在允许的目录内（安全检查）
        if not str(full_path.resolve()).startswith(str(output_dir.resolve())):
            raise HTTPException(403, "访问被拒绝")

        return FileResponse(full_path)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"文件服务错误: {str(e)}")

# 后台处理函数
async def process_generation(
    task_id: str,
    config: GenerationConfig,
    pdf_files: List[str],
    model_files: List[str]
):
    """后台处理生成任务 - 使用并行流水线"""
    try:
        # 创建进度报告器，传入当前事件循环
        loop = asyncio.get_running_loop()
        reporter = ProgressReporter(task_id, ws_manager, loop)

        # 更新任务状态
        def update_progress(progress: int, message: str):
            if task_id in tasks:
                tasks[task_id].progress = progress
                tasks[task_id].message = message
                tasks[task_id].updated_at = datetime.now()

        update_progress(5, "初始化并行处理流水线...")
        reporter.log("🚀 启动生产级并行处理流水线", "info")

        # 创建输出目录
        task_output_dir = output_dir / task_id
        task_output_dir.mkdir(exist_ok=True)

        # 创建并行流水线（使用全局API密钥）
        pipeline = ParallelAssemblyPipeline(
            dashscope_api_key=api_keys.get("dashscope") or os.getenv("DASHSCOPE_API_KEY"),
            deepseek_api_key=api_keys.get("deepseek") or os.getenv("DEEPSEEK_API_KEY"),
            progress_reporter=reporter
        )

        update_progress(10, "开始并行处理...")

        # 执行并行处理
        result = await pipeline.process_files_parallel(
            pdf_files=pdf_files,
            model_files=model_files,
            output_dir=str(task_output_dir),
            focus_type=config.focus,
            special_requirements=config.requirements
        )

        if result.get("success"):
            update_progress(100, "生成完成")

            # 更新任务状态为完成
            tasks[task_id].status = "completed"
            assembly_stats = result.get("assembly_specification", {}).get("statistics", {})
            bom_items_total = sum(
                r.get("statistics", {}).get("bom_items", 0)
                for r in result.get("pdf_analysis", [])
            )

            tasks[task_id].result = {
                "output_dir": str(task_output_dir),
                "output_file": str(task_output_dir / "assembly_manual.html"),
                "statistics": {
                    "pdf_count": len(pdf_files),
                    "model_count": len(model_files),
                    "bom_items": bom_items_total,
                    **(assembly_stats or {})
                },
                "files": []
            }
            tasks[task_id].updated_at = datetime.now()

            # 发送完成消息
            await ws_manager.send_completion(task_id, True, tasks[task_id].result)
            reporter.log("✅ 装配说明书生成完成", "success")
        else:
            raise Exception(result.get("error", "未知错误"))

    except Exception as e:
        # 更新任务状态为失败
        error_msg = f"生成失败: {str(e)}"
        if task_id in tasks:
            tasks[task_id].status = "failed"
            tasks[task_id].message = error_msg
            tasks[task_id].updated_at = datetime.now()

        # 发送失败消息
        await ws_manager.send_completion(task_id, False, error=error_msg)

        # 记录错误日志
        try:
            loop = asyncio.get_running_loop()
            reporter = ProgressReporter(task_id, ws_manager, loop)
            reporter.log(f"❌ {error_msg}", "error")
        except:
            print(f"❌ {error_msg}")

# 旧的同步处理函数已被并行流水线替代

# 启动配置
if __name__ == "__main__":
    # 检查环境变量（测试模式下可选）
    dashscope_key = os.getenv("DASHSCOPE_API_KEY")
    deepseek_key = os.getenv("DEEPSEEK_API_KEY")

    if not dashscope_key or not deepseek_key:
        print("⚠️  警告: 未设置API密钥，使用测试模式（AI功能将被模拟）")
        os.environ["DASHSCOPE_API_KEY"] = "test_key"
        os.environ["DEEPSEEK_API_KEY"] = "test_key"
    
    print("🚀 启动智能装配说明书生成系统...")
    print("📖 API文档: http://localhost:8000/api/docs")
    print("🌐 前端界面: http://localhost:3000")
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
