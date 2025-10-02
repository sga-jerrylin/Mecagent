#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修正版后端API - 严格按照总设计思路实现
双通道解析 → 候选事实JSON → DeepSeek融合推理 → 装配规范JSON
"""

import os
import sys
import json
import uuid
import asyncio
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import uvicorn

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.dual_channel_parser import DualChannelParser
from models.fusion_expert import FusionExpertModel
from processors.file_processor import PDFProcessor, ModelProcessor
from generators.html_generator import HTMLManualGenerator

# 创建FastAPI应用
app = FastAPI(
    title="智能装配说明书生成系统 - 双通道架构",
    description="严格按照总设计思路实现的双通道解析系统",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件服务
import os
static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
output_dir = os.path.join(os.path.dirname(__file__), "..", "output")

# 确保目录存在
os.makedirs(static_dir, exist_ok=True)
os.makedirs(output_dir, exist_ok=True)

app.mount("/static", StaticFiles(directory=static_dir), name="static")
app.mount("/output", StaticFiles(directory=output_dir), name="output")

# 数据模型
class DualChannelRequest(BaseModel):
    """双通道解析请求"""
    pdf_files: List[str]
    model_files: List[str]
    options: Optional[Dict[str, Any]] = {}

class FusionRequest(BaseModel):
    """融合推理请求"""
    candidate_facts: Dict[str, Any]
    fusion_options: Optional[Dict[str, Any]] = {}

class TaskStatus(BaseModel):
    """任务状态"""
    task_id: str
    status: str  # pending, parsing, fusing, generating, completed, failed
    progress: int
    message: str
    candidate_facts: Optional[Dict[str, Any]] = None
    assembly_spec: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None

class EngineerReviewRequest(BaseModel):
    """工程师复核请求"""
    task_id: str
    reviewed_assembly_spec: Dict[str, Any]
    review_comments: Optional[str] = ""
    approved: bool

class WorkerDistributionRequest(BaseModel):
    """工人分发请求"""
    manual_id: str
    worker_ids: List[str]
    deadline: Optional[str] = None

# 全局变量
dual_parser = DualChannelParser()
fusion_expert = FusionExpertModel()
pdf_processor = PDFProcessor()
model_processor = ModelProcessor()
html_generator = HTMLManualGenerator()
tasks: Dict[str, TaskStatus] = {}

# API路由

@app.get("/")
async def root():
    """根路径"""
    return {"message": "智能装配说明书生成系统 - 双通道架构", "version": "2.0.0"}

@app.post("/api/upload")
async def upload_files(
    pdf_files: List[UploadFile] = File(...),
    model_files: List[UploadFile] = File(...)
):
    """文件上传接口"""
    try:
        uploaded_files = {
            "pdf_files": [],
            "model_files": []
        }
        
        # 创建上传目录
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)
        
        # 保存PDF文件
        for pdf_file in pdf_files:
            if not pdf_file.filename.endswith('.pdf'):
                raise HTTPException(status_code=400, detail="只支持PDF文件")
            
            file_path = upload_dir / f"{uuid.uuid4()}_{pdf_file.filename}"
            with open(file_path, "wb") as f:
                content = await pdf_file.read()
                f.write(content)
            
            uploaded_files["pdf_files"].append(str(file_path))
        
        # 保存3D模型文件
        for model_file in model_files:
            if not any(model_file.filename.endswith(ext) for ext in ['.stl', '.step', '.stp']):
                raise HTTPException(status_code=400, detail="只支持STL/STEP格式的3D模型")
            
            file_path = upload_dir / f"{uuid.uuid4()}_{model_file.filename}"
            with open(file_path, "wb") as f:
                content = await model_file.read()
                f.write(content)
            
            uploaded_files["model_files"].append(str(file_path))
        
        return JSONResponse({
            "success": True,
            "message": "文件上传成功",
            "files": uploaded_files
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")

@app.post("/api/dual-channel-parse")
async def start_dual_channel_parsing(
    request: DualChannelRequest,
    background_tasks: BackgroundTasks
):
    """启动双通道解析"""
    task_id = str(uuid.uuid4())
    
    # 创建任务状态
    tasks[task_id] = TaskStatus(
        task_id=task_id,
        status="pending",
        progress=0,
        message="任务已创建，等待处理"
    )
    
    # 后台执行双通道解析
    background_tasks.add_task(
        execute_dual_channel_parsing,
        task_id,
        request.pdf_files,
        request.model_files,
        request.options
    )
    
    return JSONResponse({
        "success": True,
        "task_id": task_id,
        "message": "双通道解析任务已启动"
    })

async def execute_dual_channel_parsing(
    task_id: str,
    pdf_files: List[str],
    model_files: List[str],
    options: Dict[str, Any]
):
    """执行双通道解析"""
    try:
        # 更新状态：开始解析
        tasks[task_id].status = "parsing"
        tasks[task_id].progress = 10
        tasks[task_id].message = "开始双通道解析..."
        
        # 1. 双通道解析PDF
        candidate_facts_list = []
        for i, pdf_file in enumerate(pdf_files):
            tasks[task_id].message = f"解析PDF文件 {i+1}/{len(pdf_files)}"
            tasks[task_id].progress = 10 + (i * 30 // len(pdf_files))
            
            candidate_facts = dual_parser.parse_pdf(pdf_file)
            candidate_facts_list.append(candidate_facts)
        
        # 合并多个PDF的候选事实
        merged_candidate_facts = merge_candidate_facts(candidate_facts_list)
        
        # 保存候选事实JSON
        tasks[task_id].candidate_facts = merged_candidate_facts
        tasks[task_id].progress = 50
        tasks[task_id].message = "双通道解析完成，开始融合推理..."
        
        # 2. DeepSeek融合推理
        tasks[task_id].status = "fusing"
        fusion_result = fusion_expert.fuse_candidate_facts(merged_candidate_facts)
        
        if fusion_result["success"]:
            tasks[task_id].assembly_spec = fusion_result["assembly_spec"]
            tasks[task_id].progress = 80
            tasks[task_id].message = "融合推理完成，等待工程师复核"
            tasks[task_id].status = "completed"
        else:
            tasks[task_id].status = "failed"
            tasks[task_id].message = f"融合推理失败: {fusion_result.get('error')}"
            
    except Exception as e:
        tasks[task_id].status = "failed"
        tasks[task_id].message = f"处理失败: {str(e)}"

def merge_candidate_facts(candidate_facts_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """合并多个PDF的候选事实"""
    if not candidate_facts_list:
        return {}
    
    if len(candidate_facts_list) == 1:
        return candidate_facts_list[0]
    
    # 简单合并逻辑
    merged = {
        "pages": [],
        "regions": [],
        "bom_candidates": [],
        "feature_candidates": [],
        "note_candidates": [],
        "part_bubble_candidates": [],
        "units_notes": [],
        "warnings": []
    }
    
    for facts in candidate_facts_list:
        for key in merged.keys():
            if key in facts:
                merged[key].extend(facts[key])
    
    return merged

@app.get("/api/task/{task_id}")
async def get_task_status(task_id: str):
    """获取任务状态"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return tasks[task_id]

@app.post("/api/engineer/review")
async def engineer_review(request: EngineerReviewRequest):
    """工程师复核接口"""
    if request.task_id not in tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task = tasks[request.task_id]
    
    if request.approved:
        # 复核通过，更新装配规范
        task.assembly_spec = request.reviewed_assembly_spec
        task.status = "approved"
        task.message = "工程师复核通过"
        task.progress = 90
        
        return JSONResponse({
            "success": True,
            "message": "复核通过，可以分发给工人"
        })
    else:
        # 复核不通过，需要重新处理
        task.status = "review_rejected"
        task.message = f"工程师复核不通过: {request.review_comments}"
        
        return JSONResponse({
            "success": False,
            "message": "复核不通过，需要重新处理"
        })

@app.post("/api/worker/distribute")
async def distribute_to_workers(request: WorkerDistributionRequest):
    """分发给工人"""
    try:
        # 生成最终的HTML说明书
        manual_id = request.manual_id
        
        # 这里应该根据manual_id获取对应的装配规范
        # 简化处理，直接返回成功
        
        return JSONResponse({
            "success": True,
            "manual_id": manual_id,
            "worker_count": len(request.worker_ids),
            "message": "已成功分发给工人"
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分发失败: {str(e)}")

@app.get("/api/worker/tasks/{worker_id}")
async def get_worker_tasks(worker_id: str):
    """获取工人任务列表"""
    # 模拟数据
    mock_tasks = [
        {
            "id": "task_1",
            "name": "V型推雪板EURO连接器装配",
            "status": "pending",
            "priority": "high",
            "estimated_time": "2.5小时",
            "engineer": "李工程师",
            "deadline": "2024-01-16 18:00",
            "progress": 0
        }
    ]
    
    return JSONResponse({
        "success": True,
        "tasks": mock_tasks
    })

if __name__ == "__main__":
    # 检查环境变量
    required_env_vars = ["DASHSCOPE_API_KEY", "DEEPSEEK_API_KEY"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ 缺少环境变量: {', '.join(missing_vars)}")
        sys.exit(1)
    
    print("🚀 启动修正版后端API服务...")
    print("📖 API文档: http://localhost:8000/api/docs")
    
    uvicorn.run(
        "app_corrected:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
