from __future__ import annotations

import io
import json
import xmltodict
import vsdx
from sqlalchemy.orm import Session
from ezdxf import readfile as read_dxf

from app.models import Device, DeviceType, Project, Cable, CableType


def parse_dxf_file(file_content: bytes) -> dict:
    """
    解析DXF文件，提取设备位置和连接信息
    """
    result = {
        "devices": [],
        "connections": [],
        "metadata": {}
    }
    
    try:
        doc = read_dxf(io.BytesIO(file_content))
        msp = doc.modelspace()
        
        # 提取圆形作为设备
        device_id = 1
        device_map = {}
        
        for entity in msp.query("CIRCLE"):
            x, y, _ = entity.dxf.center
            radius = entity.dxf.radius
            name = f"Device_{device_id}"
            
            # 尝试查找关联的文本
            for text in msp.query("TEXT"):
                tx, ty, _ = text.dxf.insert
                if abs(tx - x) < radius * 2 and abs(ty - y) < radius * 2:
                    name = text.dxf.text
                    break
            
            device_info = {
                "name": name,
                "x": int(max(0, min(100, x / 10))),
                "y": int(max(0, min(100, y / 10))),
                "device_type": "网络设备",
                "radius": radius
            }
            result["devices"].append(device_info)
            device_map[(int(x), int(y))] = device_id
            device_id += 1
        
        # 提取多段线和直线作为连接
        for entity in msp.query("LWPOLYLINE LINE"):
            if entity.dxftype() == "LWPOLYLINE":
                points = entity.get_points()
            else:  # LINE
                start = entity.dxf.start
                end = entity.dxf.end
                points = [(start.x, start.y), (end.x, end.y)]
            
            if len(points) >= 2:
                start_x, start_y = points[0]
                end_x, end_y = points[-1]
                
                start_id = _find_nearest_device(device_map, start_x, start_y)
                end_id = _find_nearest_device(device_map, end_x, end_y)
                
                if start_id and end_id and start_id != end_id:
                    result["connections"].append({
                        "start_device_id": start_id,
                        "end_device_id": end_id,
                        "points": [(int(x / 10), int(y / 10)) for x, y in points]
                    })
        
        result["metadata"]["format"] = "DXF"
        result["metadata"]["entity_count"] = len(list(msp))
        
    except Exception as e:
        raise ValueError(f"DXF解析失败: {str(e)}")
    
    return result


def parse_vsdx_file(file_content: bytes) -> dict:
    """
    解析Visio VSDX文件，提取设备位置和连接信息
    """
    result = {
        "devices": [],
        "connections": [],
        "metadata": {}
    }
    
    try:
        vsd = vsdx.VisioFile(io.BytesIO(file_content))
        
        device_id = 1
        shape_device_map = {}
        
        # 遍历所有页面
        for page in vsd.pages:
            # 提取形状（设备）
            for shape in page.all_shapes:
                if shape.shape_type == "Shape" and shape.text:
                    try:
                        x = float(shape.x) if hasattr(shape, 'x') else 0
                        y = float(shape.y) if hasattr(shape, 'y') else 0
                        
                        device_info = {
                            "name": shape.text.strip() or f"Device_{device_id}",
                            "x": int(max(0, min(100, x / 10))),
                            "y": int(max(0, min(100, y / 10))),
                            "device_type": shape.type or "网络设备",
                            "shape_id": shape.ID
                        }
                        result["devices"].append(device_info)
                        shape_device_map[shape.ID] = device_id
                        device_id += 1
                    except (ValueError, TypeError):
                        continue
            
            # 提取连接器
            for connect in page.connectors:
                try:
                    if hasattr(connect, 'from_shape') and hasattr(connect, 'to_shape'):
                        from_id = shape_device_map.get(connect.from_shape.ID)
                        to_id = shape_device_map.get(connect.to_shape.ID)
                        
                        if from_id and to_id:
                            result["connections"].append({
                                "start_device_id": from_id,
                                "end_device_id": to_id,
                                "connector_id": connect.ID
                            })
                except Exception:
                    continue
        
        result["metadata"]["format"] = "VSDX"
        result["metadata"]["page_count"] = len(vsd.pages)
        
    except Exception as e:
        raise ValueError(f"Visio解析失败: {str(e)}")
    
    return result


def parse_json_file(file_content: bytes) -> dict:
    """
    解析JSON格式的布线图文件
    """
    try:
        data = json.loads(file_content.decode('utf-8'))
        result = {
            "devices": data.get("devices", []),
            "connections": data.get("connections", []),
            "metadata": {
                "format": "JSON",
                "name": data.get("name", "")
            }
        }
        return result
    except json.JSONDecodeError:
        raise ValueError("JSON格式解析失败")


def _find_nearest_device(device_map: dict, x: float, y: float, threshold: float = 50) -> int | None:
    """
    查找最近的设备
    """
    min_dist = float('inf')
    nearest_id = None
    
    for (dx, dy), device_id in device_map.items():
        dist = ((x - dx) ** 2 + (y - dy) ** 2) ** 0.5
        if dist < min_dist and dist < threshold:
            min_dist = dist
            nearest_id = device_id
    
    return nearest_id


def import_devices_to_project(
    db: Session,
    project_id: int,
    devices_data: list[dict],
    default_device_type_id: int | None = None
) -> list[Device]:
    """
    将解析后的设备数据导入到指定项目
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise ValueError("项目不存在")
    
    # 获取默认设备类型
    if default_device_type_id is None:
        default_type = db.query(DeviceType).order_by(DeviceType.id.asc()).first()
        if not default_type:
            raise ValueError("请先配置设备类型")
        default_device_type_id = default_type.id
    
    imported_devices = []
    
    for device_data in devices_data:
        # 尝试根据名称查找设备类型
        device_type = db.query(DeviceType).filter(
            DeviceType.name.ilike(f"%{device_data.get('device_type', '')}%")
        ).first()
        
        if not device_type:
            device_type = db.query(DeviceType).get(default_device_type_id)
        
        device = Device(
            project_id=project_id,
            name=device_data.get("name", "未命名设备"),
            device_type_id=device_type.id,
            x=device_data.get("x", 0),
            y=device_data.get("y", 0),
            z=device_data.get("z", 0)
        )
        db.add(device)
        imported_devices.append(device)
    
    db.flush()
    return imported_devices


def import_cables_to_project(
    db: Session,
    project_id: int,
    connections_data: list[dict],
    default_cable_type_id: int | None = None
) -> list[Cable]:
    """
    将解析后的连接数据导入为线缆
    """
    # 获取默认线缆类型
    if default_cable_type_id is None:
        default_type = db.query(CableType).order_by(CableType.id.asc()).first()
        if not default_type:
            raise ValueError("请先配置线缆类型")
        default_cable_type_id = default_type.id
    
    # 获取项目设备映射
    devices = db.query(Device).filter(Device.project_id == project_id).all()
    device_list = [d for d in devices]
    
    imported_cables = []
    
    for conn_data in connections_data:
        start_idx = conn_data.get("start_device_id")
        end_idx = conn_data.get("end_device_id")
        
        # 处理索引（从1开始）
        if isinstance(start_idx, int) and start_idx > 0 and start_idx <= len(device_list):
            start_device = device_list[start_idx - 1]
        else:
            continue
            
        if isinstance(end_idx, int) and end_idx > 0 and end_idx <= len(device_list):
            end_device = device_list[end_idx - 1]
        else:
            continue
        
        if start_device and end_device and start_device.id != end_device.id:
            cable = Cable(
                project_id=project_id,
                cable_type_id=default_cable_type_id,
                start_device_id=start_device.id,
                end_device_id=end_device.id,
                length=0.0,
                path_json=[[start_device.x, start_device.y], [end_device.x, end_device.y]]
            )
            db.add(cable)
            imported_cables.append(cable)
    
    db.flush()
    return imported_cables