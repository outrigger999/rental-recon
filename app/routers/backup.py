"""
Backup management routes
"""
from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import List
import os
from app.services.backup_service import BackupService

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# Initialize backup service
backup_service = BackupService()

@router.get("/backup", response_class=HTMLResponse)
async def backup_page(request: Request):
    """Display backup management page"""
    config = backup_service.get_backup_config()
    backups = backup_service.get_backup_files()
    last_backup_time = backup_service.get_last_backup_time()
    
    backup_config = {
        "backup_directory": os.path.abspath(backup_service.backup_dir),
        "database_path": os.path.abspath(backup_service.db_path),
        "max_backups": config["max_backups"],
        "auto_backup": config["auto_backup"],
        "backup_interval": config["backup_interval"]
    }
    
    return templates.TemplateResponse("backup.html", {
        "request": request,
        "backup_config": backup_config,
        "archives": backups,
        "last_backup_time": last_backup_time
    })

@router.post("/backup/trigger")
async def trigger_backup(request: Request):
    """Trigger manual backup"""
    result = backup_service.create_backup()
    
    if result["success"]:
        # In a real app, you'd use flash messages. For now, we'll redirect with success
        return RedirectResponse(url="/backup?success=backup_created", status_code=303)
    else:
        return RedirectResponse(url="/backup?error=backup_failed", status_code=303)

@router.post("/backup/config")
async def update_backup_config(request: Request, max_backups: int = Form(...)):
    """Update backup configuration"""
    success = backup_service.update_max_backups(max_backups)
    
    if success:
        return RedirectResponse(url="/backup?success=config_updated", status_code=303)
    else:
        return RedirectResponse(url="/backup?error=invalid_config", status_code=303)

@router.post("/backup/delete")
async def delete_backups(request: Request):
    """Delete selected backup files"""
    form_data = await request.form()
    selected_backups = form_data.getlist("selected_backups")
    
    if not selected_backups:
        return RedirectResponse(url="/backup?error=no_selection", status_code=303)
    
    result = backup_service.delete_backup_files(selected_backups)
    
    if result["success"]:
        return RedirectResponse(url="/backup?success=backups_deleted", status_code=303)
    else:
        return RedirectResponse(url="/backup?error=delete_failed", status_code=303)

@router.get("/backup/download/{filename}")
async def download_backup(filename: str):
    """Download a backup file"""
    file_path = backup_service.get_backup_file_path(filename)
    
    if not file_path:
        raise HTTPException(status_code=404, detail="Backup file not found")
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/octet-stream"
    )
