import logging
import tempfile
import zipfile
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import ezdxf
from vsdx import VisioFile

logger = logging.getLogger(__name__)


@dataclass
class ImportedDevice:
    name: str
    x: int
    y: int
    device_type_name: str | None = None
    attributes: dict[str, Any] = None

    def __post_init__(self):
        if self.attributes is None:
            self.attributes = {}


@dataclass
class ImportResult:
    success: bool
    devices: list[ImportedDevice]
    errors: list[str]
    warnings: list[str]
    total_shapes: int
    imported_count: int


class FileParser(ABC):
    @abstractmethod
    def parse(self, file_path: Path) -> ImportResult:
        pass

    @abstractmethod
    def supports_format(self, filename: str) -> bool:
        pass


class DXFParser(FileParser):
    def supports_format(self, filename: str) -> bool:
        return filename.lower().endswith(".dxf")

    def parse(self, file_path: Path) -> ImportResult:
        devices: list[ImportedDevice] = []
        errors: list[str] = []
        warnings: list[str] = []
        total_shapes = 0

        try:
            doc = ezdxf.readfile(str(file_path))
            msp = doc.modelspace()

            for entity in msp:
                total_shapes += 1
                try:
                    device = self._parse_entity(entity)
                    if device:
                        devices.append(device)
                except Exception as e:
                    warnings.append(f"解析实体 {entity.dxftype()} 时出错: {str(e)}")

        except ezdxf.DXFError as e:
            errors.append(f"DXF文件解析错误: {str(e)}")
            return ImportResult(
                success=False,
                devices=[],
                errors=errors,
                warnings=warnings,
                total_shapes=total_shapes,
                imported_count=0,
            )

        return ImportResult(
            success=True,
            devices=devices,
            errors=errors,
            warnings=warnings,
            total_shapes=total_shapes,
            imported_count=len(devices),
        )

    def _parse_entity(self, entity) -> ImportedDevice | None:
        dxftype = entity.dxftype()

        if dxftype == "INSERT":
            return self._parse_insert(entity)
        elif dxftype in ("CIRCLE", "LWPOLYLINE", "POLYLINE", "LINE"):
            return self._parse_shape(entity, dxftype)
        elif dxftype == "TEXT" or dxftype == "MTEXT":
            return self._parse_text(entity)

        return None

    def _parse_insert(self, entity) -> ImportedDevice | None:
        name = entity.dxf.name or f"Block_{entity.dxf.handle}"
        x = int(getattr(entity.dxf, "insert", (0, 0, 0))[0])
        y = int(getattr(entity.dxf, "insert", (0, 0, 0))[1])

        attributes = {}
        if hasattr(entity, "attribs"):
            for attrib in entity.attribs:
                if hasattr(attrib, "dxf") and hasattr(attrib.dxf, "tag"):
                    attributes[attrib.dxf.tag] = attrib.dxf.text

        return ImportedDevice(
            name=name,
            x=x,
            y=y,
            device_type_name=name.split("_")[0] if "_" in name else None,
            attributes=attributes,
        )

    def _parse_shape(self, entity, dxftype: str) -> ImportedDevice | None:
        if dxftype == "CIRCLE":
            x = int(entity.dxf.center[0])
            y = int(entity.dxf.center[1])
        else:
            points = list(entity.get_points())
            if not points:
                return None
            x = int(points[0][0])
            y = int(points[0][1])

        name = f"{dxftype}_{entity.dxf.handle}"

        return ImportedDevice(
            name=name,
            x=x,
            y=y,
            device_type_name=dxftype,
            attributes={"original_type": dxftype},
        )

    def _parse_text(self, entity) -> ImportedDevice | None:
        text = entity.dxf.text if hasattr(entity.dxf, "text") else ""
        if not text.strip():
            return None

        if hasattr(entity.dxf, "insert"):
            x = int(entity.dxf.insert[0])
            y = int(entity.dxf.insert[1])
        elif hasattr(entity.dxf, "insert_point"):
            x = int(entity.dxf.insert_point[0])
            y = int(entity.dxf.insert_point[1])
        else:
            x, y = 0, 0

        return ImportedDevice(
            name=text.strip()[:64],
            x=x,
            y=y,
            device_type_name="Text",
            attributes={"original_type": "TEXT"},
        )


class VSDXParser(FileParser):
    def supports_format(self, filename: str) -> bool:
        return filename.lower().endswith(".vsdx")

    def parse(self, file_path: Path) -> ImportResult:
        devices: list[ImportedDevice] = []
        errors: list[str] = []
        warnings: list[str] = []
        total_shapes = 0

        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                with zipfile.ZipFile(file_path, "r") as zip_ref:
                    zip_ref.extractall(temp_dir)

                visio = VisioFile(str(file_path))

                for page in visio.pages:
                    page_devices, page_warnings = self._parse_page(page)
                    total_shapes += len(page_devices)
                    devices.extend(page_devices)
                    warnings.extend(page_warnings)

                visio.close_vsdx()

        except Exception as e:
            errors.append(f"VSDX文件解析错误: {str(e)}")
            return ImportResult(
                success=False,
                devices=[],
                errors=errors,
                warnings=warnings,
                total_shapes=total_shapes,
                imported_count=0,
            )

        return ImportResult(
            success=True,
            devices=devices,
            errors=errors,
            warnings=warnings,
            total_shapes=total_shapes,
            imported_count=len(devices),
        )

    def _parse_page(self, page) -> tuple[list[ImportedDevice], list[str]]:
        devices: list[ImportedDevice] = []
        warnings: list[str] = []

        try:
            for shape in page.shapes:
                device = self._parse_shape(shape)
                if device:
                    devices.append(device)
        except Exception as e:
            warnings.append(f"解析页面时出错: {str(e)}")

        return devices, warnings

    def _parse_shape(self, shape) -> ImportedDevice | None:
        try:
            name = shape.text or shape.shape_name or f"Shape_{shape.ID}"
            name = name.strip()[:64] if name else f"Shape_{shape.ID}"

            x = int(getattr(shape, "pin_x", 0) or 0)
            y = int(getattr(shape, "pin_y", 0) or 0)

            device_type = None
            if hasattr(shape, "master_shape") and shape.master_shape:
                device_type = shape.master_shape.shape_name

            attributes = {}
            if hasattr(shape, "cells") and shape.cells:
                for cell_name, cell in shape.cells.items():
                    attributes[cell_name] = cell.value if hasattr(cell, "value") else str(cell)

            return ImportedDevice(
                name=name,
                x=x,
                y=y,
                device_type_name=device_type,
                attributes=attributes,
            )
        except Exception:
            return None


class ImportService:
    def __init__(self):
        self._parsers: list[FileParser] = [DXFParser(), VSDXParser()]

    def get_supported_formats(self) -> list[str]:
        return [".dxf", ".vsdx"]

    def parse_file(self, file_path: Path) -> ImportResult:
        filename = file_path.name

        for parser in self._parsers:
            if parser.supports_format(filename):
                logger.info(f"使用 {parser.__class__.__name__} 解析文件: {filename}")
                return parser.parse(file_path)

        return ImportResult(
            success=False,
            devices=[],
            errors=[f"不支持的文件格式: {filename}"],
            warnings=[],
            total_shapes=0,
            imported_count=0,
        )

    def validate_file(self, file_path: Path, max_size_mb: int = 50) -> tuple[bool, str]:
        if not file_path.exists():
            return False, "文件不存在"

        file_size = file_path.stat().st_size
        max_size_bytes = max_size_mb * 1024 * 1024
        if file_size > max_size_bytes:
            return False, f"文件大小超过限制 ({max_size_mb}MB)"

        supported = any(parser.supports_format(file_path.name) for parser in self._parsers)
        if not supported:
            return False, f"不支持的文件格式，支持: {', '.join(self.get_supported_formats())}"

        return True, "文件验证通过"
