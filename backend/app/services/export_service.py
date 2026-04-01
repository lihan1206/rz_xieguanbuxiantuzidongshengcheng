from __future__ import annotations

import io
import json

import ezdxf
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from sqlalchemy.orm import Session, joinedload

from app.models import Cable, Device, Project


def build_project_payload(db: Session, project_id: int) -> dict:
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

    return {
        "id": project.id,
        "name": project.name,
        "location": project.location,
        "purpose": project.purpose,
        "status": project.status,
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


def export_json(payload: dict) -> bytes:
    return json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")


def export_svg(payload: dict) -> bytes:
    device_map = {device["id"]: device for device in payload["devices"]}
    width = 800
    height = 500

    lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="800" height="500" viewBox="0 0 800 500">',
        '<rect width="800" height="500" fill="#f8fafc"/>',
        '<text x="24" y="36" font-size="22" fill="#1e293b">布线图：%s</text>' % payload["name"],
    ]

    for cable in payload["cables"]:
        path = cable["path"]
        points = " ".join(f"{24 + x * 7},{460 - y * 4}" for x, y in path)
        lines.append(f'<polyline points="{points}" fill="none" stroke="#2563eb" stroke-width="2"/>')

    for device in payload["devices"]:
        cx = 24 + device["x"] * 7
        cy = 460 - device["y"] * 4
        lines.append(f'<circle cx="{cx}" cy="{cy}" r="8" fill="#0ea5e9" />')
        lines.append(f'<text x="{cx + 10}" y="{cy - 10}" font-size="12" fill="#0f172a">{device["name"]}</text>')

    lines.append("</svg>")
    return "\n".join(lines).encode("utf-8")


def export_pdf(payload: dict) -> bytes:
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    c.setTitle(f"{payload['name']}-布线图")
    c.drawString(40, 800, f"项目名称：{payload['name']}")
    c.drawString(40, 780, f"项目地点：{payload['location']}")
    c.drawString(40, 760, f"项目用途：{payload['purpose']}")

    y = 730
    c.drawString(40, y, "线缆信息：")
    y -= 20
    for cable in payload["cables"][:20]:
        c.drawString(
            40,
            y,
            f"线缆#{cable['id']} {cable['type']} 设备{cable['start_device_id']} -> 设备{cable['end_device_id']} 长度 {cable['length']:.1f}",
        )
        y -= 18
        if y < 60:
            c.showPage()
            y = 800

    c.save()
    return buffer.getvalue()


def export_dxf(payload: dict) -> bytes:
    doc = ezdxf.new("R2010")
    msp = doc.modelspace()

    for device in payload["devices"]:
        x, y = device["x"] * 10, device["y"] * 10
        msp.add_circle((x, y), radius=3)
        msp.add_text(device["name"], dxfattribs={"height": 2.5}).set_placement((x + 2, y + 2))

    for cable in payload["cables"]:
        points = [(x * 10, y * 10) for x, y in cable["path"]]
        if len(points) >= 2:
            msp.add_lwpolyline(points)

    stream = io.StringIO()
    doc.write(stream)
    return stream.getvalue().encode("utf-8")
