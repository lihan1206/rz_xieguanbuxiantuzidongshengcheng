from __future__ import annotations

import io
import json
import math

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from sqlalchemy.orm import Session, joinedload

from app.models import Cable, Device, Project


def project_to_3d_payload(db: Session, project_id: int) -> dict:
    """
    转换项目数据为3D格式
    """
    project = (
        db.query(Project)
        .options(
            joinedload(Project.devices).joinedload(Device.device_type),
            joinedload(Project.cables).joinedload(Cable.cable_type),
        )
        .filter(Project.id == project_id)
        .first()
    )
    if not project:
        raise ValueError("项目不存在")

    # 计算3D边界
    all_coords = [(d.x, d.y, getattr(d, 'z', 0)) for d in project.devices]
    if not all_coords:
        all_coords = [(0, 0, 0)]
    
    min_x = min(c[0] for c in all_coords)
    max_x = max(c[0] for c in all_coords)
    min_y = min(c[1] for c in all_coords)
    max_y = max(c[1] for c in all_coords)
    min_z = min(c[2] for c in all_coords)
    max_z = max(c[2] for c in all_coords)

    return {
        "id": project.id,
        "name": project.name,
        "location": project.location,
        "purpose": project.purpose,
        "status": project.status,
        "bounds": {
            "min_x": min_x,
            "max_x": max_x,
            "min_y": min_y,
            "max_y": max_y,
            "min_z": min_z,
            "max_z": max_z
        },
        "devices": [
            {
                "id": device.id,
                "name": device.name,
                "x": device.x,
                "y": device.y,
                "z": getattr(device, 'z', 0),
                "device_type": device.device_type.name,
            }
            for device in project.devices
        ],
        "cables": [
            {
                "id": cable.id,
                "type": cable.cable_type.name,
                "start_device_id": cable.start_device_id,
                "end_device_id": cable.end_device_id,
                "length": cable.length,
                "path": cable.path_json,
            }
            for cable in project.cables
        ],
    }


def _project_3d_to_2d_isometric(
    x: int, 
    y: int, 
    z: int, 
    scale: float = 10.0,
    offset_x: float = 400,
    offset_y: float = 300
) -> tuple[float, float]:
    """
    将3D坐标转换为2D等距投影坐标
    """
    # 等距投影变换
    iso_x = (x - y) * math.cos(math.radians(30)) * scale
    iso_y = (x + y) * math.sin(math.radians(30)) * scale - z * scale
    return (iso_x + offset_x, iso_y + offset_y)


def export_3d_json(payload: dict) -> bytes:
    """
    导出3D数据为JSON格式
    """
    return json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")


def export_3d_svg(payload: dict) -> bytes:
    """
    导出3D布线图为SVG（等距投影）
    """
    device_map = {device["id"]: device for device in payload["devices"]}
    width = 800
    height = 600
    scale = 8.0

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        f'<rect width="{width}" height="{height}" fill="#f8fafc"/>',
        f'<text x="24" y="36" font-size="22" fill="#1e293b">3D布线图：{payload["name"]}</text>',
        '<text x="24" y="56" font-size="12" fill="#64748b">等距投影 / Isometric Projection</text>',
    ]

    # 绘制坐标轴指示
    axis_x1 = _project_3d_to_2d_isometric(5, 0, 0, scale, 700, 100)
    axis_x2 = _project_3d_to_2d_isometric(0, 0, 0, scale, 700, 100)
    axis_y1 = _project_3d_to_2d_isometric(0, 5, 0, scale, 700, 100)
    axis_y2 = _project_3d_to_2d_isometric(0, 0, 0, scale, 700, 100)
    axis_z1 = _project_3d_to_2d_isometric(0, 0, 5, scale, 700, 100)
    axis_z2 = _project_3d_to_2d_isometric(0, 0, 0, scale, 700, 100)
    
    lines.append(f'<line x1="{axis_x2[0]}" y1="{axis_x2[1]}" x2="{axis_x1[0]}" y2="{axis_x1[1]}" stroke="#ef4444" stroke-width="2"/>')
    lines.append(f'<text x="{axis_x1[0] + 5}" y="{axis_x1[1]}" font-size="10" fill="#ef4444">X</text>')
    lines.append(f'<line x1="{axis_y2[0]}" y1="{axis_y2[1]}" x2="{axis_y1[0]}" y2="{axis_y1[1]}" stroke="#22c55e" stroke-width="2"/>')
    lines.append(f'<text x="{axis_y1[0] + 5}" y="{axis_y1[1]}" font-size="10" fill="#22c55e">Y</text>')
    lines.append(f'<line x1="{axis_z2[0]}" y1="{axis_z2[1]}" x2="{axis_z1[0]}" y2="{axis_z1[1]}" stroke="#3b82f6" stroke-width="2"/>')
    lines.append(f'<text x="{axis_z1[0] + 5}" y="{axis_z1[1]}" font-size="10" fill="#3b82f6">Z</text>')

    # 绘制线缆（底层）
    for cable in payload.get("cables", []):
        start_dev = device_map.get(cable["start_device_id"])
        end_dev = device_map.get(cable["end_device_id"])
        
        if start_dev and end_dev:
            start_2d = _project_3d_to_2d_isometric(start_dev["x"], start_dev["y"], start_dev.get("z", 0), scale, 400, 350)
            end_2d = _project_3d_to_2d_isometric(end_dev["x"], end_dev["y"], end_dev.get("z", 0), scale, 400, 350)
            
            # 根据Z深度调整颜色深浅
            avg_z = (start_dev.get("z", 0) + end_dev.get("z", 0)) / 2
            color_intensity = max(100, min(200, 150 + avg_z * 10))
            line_color = f'rgb({37}, {99}, {color_intensity})'
            
            lines.append(f'<line x1="{start_2d[0]:.1f}" y1="{start_2d[1]:.1f}" x2="{end_2d[0]:.1f}" y2="{end_2d[1]:.1f}" stroke="{line_color}" stroke-width="2"/>')

    # 绘制设备节点
    for device in payload.get("devices", []):
        dev_2d = _project_3d_to_2d_isometric(device["x"], device["y"], device.get("z", 0), scale, 400, 350)
        
        # 根据Z坐标调整大小和颜色
        z = device.get("z", 0)
        radius = max(6, 10 - z * 0.3)
        color_intensity = max(100, min(255, 180 + z * 15))
        fill_color = f'rgb({14}, {color_intensity}, {233})'
        
        lines.append(f'<circle cx="{dev_2d[0]:.1f}" cy="{dev_2d[1]:.1f}" r="{radius:.1f}" fill="{fill_color}" stroke="#0369a1" stroke-width="1"/>')
        lines.append(f'<text x="{dev_2d[0] + 12}" y="{dev_2d[1] - 4}" font-size="11" fill="#0f172a">{device["name"]}</text>')
        lines.append(f'<text x="{dev_2d[0] + 12}" y="{dev_2d[1] + 8}" font-size="9" fill="#64748b">Z={z}</text>')

    lines.append("</svg>")
    return "\n".join(lines).encode("utf-8")


def export_3d_pdf(payload: dict) -> bytes:
    """
    导出3D布线图为PDF
    """
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    c.setTitle(f"{payload['name']}-3D布线图")
    
    # 标题
    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, 800, f"3D布线图：{payload['name']}")
    c.setFont("Helvetica", 10)
    c.drawString(40, 785, f"项目地点：{payload['location']}")
    c.drawString(40, 770, f"项目用途：{payload['purpose']}")
    
    # 统计信息
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, 745, "统计信息：")
    c.setFont("Helvetica", 10)
    c.drawString(50, 725, f"设备数量：{len(payload.get('devices', []))}")
    c.drawString(50, 710, f"线缆数量：{len(payload.get('cables', []))}")
    
    # 3D边界信息
    bounds = payload.get("bounds", {})
    c.drawString(50, 695, f"3D边界：X[{bounds.get('min_x', 0)}-{bounds.get('max_x', 0)}], Y[{bounds.get('min_y', 0)}-{bounds.get('max_y', 0)}], Z[{bounds.get('min_z', 0)}-{bounds.get('max_z', 0)}]")
    
    # 设备列表
    y = 665
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "设备列表（3D坐标）：")
    y -= 20
    
    c.setFont("Helvetica", 9)
    for device in payload.get("devices", [])[:15]:
        c.drawString(
            50, y,
            f"{device['name']} - X: {device['x']}, Y: {device['y']}, Z: {device.get('z', 0)}"
        )
        y -= 14
        if y < 60:
            c.showPage()
            y = 800
    
    c.save()
    return buffer.getvalue()