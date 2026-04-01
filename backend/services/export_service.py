"""
导出服务 - 支持PDF、SVG、DXF、Excel等多种格式导出
"""

import os
import io
import base64
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import json

# PDF导出
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, A3, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
    Image, PageBreak, Frame, PageTemplate
)
from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import Drawing, Line, Rect, String
from reportlab.graphics import renderPDF

# SVG导出
import xml.etree.ElementTree as ET

# Excel导出
import openpyxl
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.utils import get_column_letter

# 图片处理
from PIL import Image as PILImage


@dataclass
class ExportOptions:
    """导出选项"""
    format: str  # 'pdf', 'svg', 'dxf', 'excel', 'json'
    page_size: str = 'A4'  # 'A4', 'A3', 'A2', 'A1'
    orientation: str = 'landscape'  # 'portrait', 'landscape'
    scale: float = 1.0
    include_title: bool = True
    include_legend: bool = True
    include_table: bool = True
    title: str = '布线规划图'
    company_name: str = ''
    project_name: str = ''
    date: str = ''
    author: str = ''
    
    def __post_init__(self):
        if not self.date:
            self.date = datetime.now().strftime('%Y-%m-%d')


@dataclass
class DeviceData:
    """设备数据"""
    id: str
    name: str
    type: str
    x: float
    y: float
    z: float = 0
    width: float = 0
    height: float = 0
    rotation: float = 0
    properties: Dict[str, Any] = None


@dataclass
class ConnectionData:
    """连接数据"""
    id: str
    name: str
    source_id: str
    target_id: str
    type: str
    path_points: List[Tuple[float, float, float]]
    length: float
    color: str = '#0066CC'
    line_width: float = 2.0


@dataclass
class RouteData:
    """路径数据"""
    devices: List[DeviceData]
    connections: List[ConnectionData]
    bounds: Tuple[float, float, float, float]  # min_x, min_y, max_x, max_y
    grid_size: float = 10.0


class PDFExporter:
    """PDF导出器"""
    
    PAGE_SIZES = {
        'A4': A4,
        'A3': A3,
        'A4_L': landscape(A4),
        'A3_L': landscape(A3),
    }
    
    def __init__(self, options: ExportOptions):
        self.options = options
        self.styles = getSampleStyleSheet()
        self._setup_styles()
    
    def _setup_styles(self):
        """设置样式"""
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=20,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=20,
            alignment=1  # 居中
        )
        
        self.header_style = ParagraphStyle(
            'CustomHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#333333'),
            spaceAfter=10
        )
        
        self.normal_style = ParagraphStyle(
            'CustomNormal',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#333333')
        )
    
    def export(self, data: RouteData, output_path: str) -> str:
        """
        导出PDF文件
        
        Args:
            data: 路径数据
            output_path: 输出文件路径
        
        Returns:
            输出文件路径
        """
        # 确定页面大小
        page_key = f"{self.options.page_size}_{'L' if self.options.orientation == 'landscape' else 'P'}"
        page_size = self.PAGE_SIZES.get(page_key, A4)
        
        # 创建PDF文档
        doc = SimpleDocTemplate(
            output_path,
            pagesize=page_size,
            rightMargin=20*mm,
            leftMargin=20*mm,
            topMargin=20*mm,
            bottomMargin=20*mm
        )
        
        elements = []
        
        # 添加标题
        if self.options.include_title:
            elements.extend(self._create_title_section())
        
        # 添加图纸
        elements.extend(self._create_drawing_section(data))
        
        # 添加图例
        if self.options.include_legend:
            elements.extend(self._create_legend_section())
        
        # 添加表格
        if self.options.include_table:
            elements.extend(self._create_table_section(data))
        
        # 构建PDF
        doc.build(elements)
        
        return output_path
    
    def _create_title_section(self) -> List[Any]:
        """创建标题部分"""
        elements = []
        
        # 主标题
        title = Paragraph(self.options.title, self.title_style)
        elements.append(title)
        
        # 项目信息
        info_items = []
        if self.options.company_name:
            info_items.append(f"公司: {self.options.company_name}")
        if self.options.project_name:
            info_items.append(f"项目: {self.options.project_name}")
        info_items.append(f"日期: {self.options.date}")
        if self.options.author:
            info_items.append(f"制图: {self.options.author}")
        
        info_text = " | ".join(info_items)
        info = Paragraph(info_text, self.normal_style)
        elements.append(info)
        elements.append(Spacer(1, 10*mm))
        
        return elements
    
    def _create_drawing_section(self, data: RouteData) -> List[Any]:
        """创建图纸部分"""
        elements = []
        
        # 创建绘图
        drawing = Drawing(400, 300)
        
        # 计算缩放比例
        min_x, min_y, max_x, max_y = data.bounds
        width = max_x - min_x
        height = max_y - min_y
        
        if width > 0 and height > 0:
            scale_x = 380 / width
            scale_y = 280 / height
            scale = min(scale_x, scale_y) * self.options.scale
            
            offset_x = 10 + (380 - width * scale) / 2
            offset_y = 10 + (280 - height * scale) / 2
            
            # 绘制网格
            self._draw_grid(drawing, min_x, min_y, max_x, max_y, scale, offset_x, offset_y)
            
            # 绘制设备
            for device in data.devices:
                self._draw_device(drawing, device, min_x, min_y, scale, offset_x, offset_y)
            
            # 绘制连接
            for connection in data.connections:
                self._draw_connection(drawing, connection, min_x, min_y, scale, offset_x, offset_y)
        
        elements.append(drawing)
        elements.append(Spacer(1, 10*mm))
        
        return elements
    
    def _draw_grid(self, drawing: Drawing, min_x: float, min_y: float,
                   max_x: float, max_y: float, scale: float,
                   offset_x: float, offset_y: float):
        """绘制网格"""
        grid_color = colors.HexColor('#E0E0E0')
        
        # 简化网格绘制
        for i in range(0, int(max_x - min_x) + 1, 50):
            x = offset_x + i * scale
            line = Line(x, offset_y, x, offset_y + (max_y - min_y) * scale)
            line.strokeColor = grid_color
            line.strokeWidth = 0.5
            drawing.add(line)
        
        for i in range(0, int(max_y - min_y) + 1, 50):
            y = offset_y + i * scale
            line = Line(offset_x, y, offset_x + (max_x - min_x) * scale, y)
            line.strokeColor = grid_color
            line.strokeWidth = 0.5
            drawing.add(line)
    
    def _draw_device(self, drawing: Drawing, device: DeviceData,
                     min_x: float, min_y: float, scale: float,
                     offset_x: float, offset_y: float):
        """绘制设备"""
        x = offset_x + (device.x - min_x) * scale
        y = offset_y + (device.y - min_y) * scale
        w = device.width * scale
        h = device.height * scale
        
        rect = Rect(x - w/2, y - h/2, w, h)
        rect.fillColor = colors.HexColor('#E3F2FD')
        rect.strokeColor = colors.HexColor('#1976D2')
        rect.strokeWidth = 1.5
        drawing.add(rect)
        
        # 设备标签
        label = String(x, y - h/2 - 10, device.name)
        label.fontName = 'Helvetica'
        label.fontSize = 8
        label.fillColor = colors.HexColor('#333333')
        drawing.add(label)
    
    def _draw_connection(self, drawing: Drawing, connection: ConnectionData,
                         min_x: float, min_y: float, scale: float,
                         offset_x: float, offset_y: float):
        """绘制连接"""
        if len(connection.path_points) < 2:
            return
        
        color = colors.HexColor(connection.color)
        
        for i in range(len(connection.path_points) - 1):
            x1 = offset_x + (connection.path_points[i][0] - min_x) * scale
            y1 = offset_y + (connection.path_points[i][1] - min_y) * scale
            x2 = offset_x + (connection.path_points[i+1][0] - min_x) * scale
            y2 = offset_y + (connection.path_points[i+1][1] - min_y) * scale
            
            line = Line(x1, y1, x2, y2)
            line.strokeColor = color
            line.strokeWidth = connection.line_width
            drawing.add(line)
    
    def _create_legend_section(self) -> List[Any]:
        """创建图例部分"""
        elements = []
        
        legend_data = [
            ['图例', '说明'],
            ['■', '设备'],
            ['━', '电缆连接'],
            ['━', '管道连接'],
        ]
        
        legend_table = Table(legend_data, colWidths=[30*mm, 60*mm])
        legend_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1976D2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F5F5F5')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
        ]))
        
        elements.append(Paragraph("图例", self.header_style))
        elements.append(legend_table)
        elements.append(Spacer(1, 10*mm))
        
        return elements
    
    def _create_table_section(self, data: RouteData) -> List[Any]:
        """创建表格部分"""
        elements = []
        
        # 连接信息表
        table_data = [['序号', '连接名称', '类型', '起点', '终点', '长度(m)', '备注']]
        
        for i, conn in enumerate(data.connections, 1):
            # 查找设备名称
            source_name = next((d.name for d in data.devices if d.id == conn.source_id), conn.source_id)
            target_name = next((d.name for d in data.devices if d.id == conn.target_id), conn.target_id)
            
            table_data.append([
                str(i),
                conn.name,
                conn.type,
                source_name,
                target_name,
                f"{conn.length:.2f}",
                ''
            ])
        
        # 添加统计行
        total_length = sum(c.length for c in data.connections)
        table_data.append(['', '', '', '', '合计', f"{total_length:.2f}", ''])
        
        # 创建表格
        table = Table(table_data, repeatRows=1)
        table.setStyle(TableStyle([
            # 表头样式
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1976D2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            
            # 数据行样式
            ('BACKGROUND', (0, 1), (-1, -2), colors.HexColor('#FAFAFA')),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#333333')),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),
            ('ALIGN', (5, 1), (5, -1), 'RIGHT'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            
            # 合计行样式
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#E3F2FD')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ]))
        
        elements.append(Paragraph("连接清单", self.header_style))
        elements.append(table)
        
        return elements


class SVGExporter:
    """SVG导出器"""
    
    def __init__(self, options: ExportOptions):
        self.options = options
    
    def export(self, data: RouteData, output_path: str) -> str:
        """
        导出SVG文件
        
        Args:
            data: 路径数据
            output_path: 输出文件路径
        
        Returns:
            输出文件路径
        """
        min_x, min_y, max_x, max_y = data.bounds
        width = max_x - min_x
        height = max_y - min_y
        
        # 添加边距
        margin = 50
        view_width = width + margin * 2
        view_height = height + margin * 2
        
        # 创建SVG根元素
        svg = ET.Element('svg')
        svg.set('xmlns', 'http://www.w3.org/2000/svg')
        svg.set('width', str(view_width * self.options.scale))
        svg.set('height', str(view_height * self.options.scale))
        svg.set('viewBox', f'0 0 {view_width} {view_height}')
        
        # 添加样式定义
        defs = ET.SubElement(svg, 'defs')
        self._add_styles(defs)
        
        # 添加背景
        bg = ET.SubElement(svg, 'rect')
        bg.set('width', '100%')
        bg.set('height', '100%')
        bg.set('fill', '#FFFFFF')
        
        # 添加标题
        if self.options.include_title:
            self._add_title(svg, view_width, margin)
        
        # 创建主绘图组
        drawing_group = ET.SubElement(svg, 'g')
        drawing_group.set('transform', f'translate({margin}, {margin + 40})')
        
        # 绘制网格
        self._draw_grid_svg(drawing_group, width, height, data.grid_size)
        
        # 绘制设备
        for device in data.devices:
            self._draw_device_svg(drawing_group, device, min_x, min_y)
        
        # 绘制连接
        for connection in data.connections:
            self._draw_connection_svg(drawing_group, connection, min_x, min_y)
        
        # 添加图例
        if self.options.include_legend:
            self._add_legend_svg(svg, view_width, view_height, margin)
        
        # 保存文件
        tree = ET.ElementTree(svg)
        tree.write(output_path, encoding='utf-8', xml_declaration=True)
        
        return output_path
    
    def _add_styles(self, defs: ET.Element):
        """添加样式定义"""
        style = ET.SubElement(defs, 'style')
        style.text = '''
            .device { fill: #E3F2FD; stroke: #1976D2; stroke-width: 2; }
            .device-label { font-family: Arial, sans-serif; font-size: 12px; fill: #333; }
            .connection { fill: none; stroke-width: 2; }
            .grid-line { stroke: #E0E0E0; stroke-width: 0.5; }
            .title { font-family: Arial, sans-serif; font-size: 18px; font-weight: bold; fill: #1a1a1a; }
            .info { font-family: Arial, sans-serif; font-size: 10px; fill: #666; }
        '''
    
    def _add_title(self, svg: ET.Element, width: float, margin: float):
        """添加标题"""
        title = ET.SubElement(svg, 'text')
        title.set('x', str(width / 2))
        title.set('y', str(margin))
        title.set('text-anchor', 'middle')
        title.set('class', 'title')
        title.text = self.options.title
        
        # 项目信息
        info_text = f"项目: {self.options.project_name} | 日期: {self.options.date}"
        if self.options.author:
            info_text += f" | 制图: {self.options.author}"
        
        info = ET.SubElement(svg, 'text')
        info.set('x', str(width / 2))
        info.set('y', str(margin + 20))
        info.set('text-anchor', 'middle')
        info.set('class', 'info')
        info.text = info_text
    
    def _draw_grid_svg(self, parent: ET.Element, width: float, height: float, grid_size: float):
        """绘制网格"""
        grid_group = ET.SubElement(parent, 'g')
        grid_group.set('class', 'grid')
        
        # 垂直线
        for x in range(0, int(width) + 1, int(grid_size) * 5):
            line = ET.SubElement(grid_group, 'line')
            line.set('x1', str(x))
            line.set('y1', '0')
            line.set('x2', str(x))
            line.set('y2', str(height))
            line.set('class', 'grid-line')
        
        # 水平线
        for y in range(0, int(height) + 1, int(grid_size) * 5):
            line = ET.SubElement(grid_group, 'line')
            line.set('x1', '0')
            line.set('y1', str(y))
            line.set('x2', str(width))
            line.set('y2', str(y))
            line.set('class', 'grid-line')
    
    def _draw_device_svg(self, parent: ET.Element, device: DeviceData, min_x: float, min_y: float):
        """绘制设备"""
        x = device.x - min_x - device.width / 2
        y = device.y - min_y - device.height / 2
        
        rect = ET.SubElement(parent, 'rect')
        rect.set('x', str(x))
        rect.set('y', str(y))
        rect.set('width', str(device.width))
        rect.set('height', str(device.height))
        rect.set('class', 'device')
        
        # 设备名称
        label = ET.SubElement(parent, 'text')
        label.set('x', str(device.x - min_x))
        label.set('y', str(y + device.height + 15))
        label.set('text-anchor', 'middle')
        label.set('class', 'device-label')
        label.text = device.name
    
    def _draw_connection_svg(self, parent: ET.Element, connection: ConnectionData,
                             min_x: float, min_y: float):
        """绘制连接"""
        if len(connection.path_points) < 2:
            return
        
        # 构建路径
        path_d = f"M {connection.path_points[0][0] - min_x} {connection.path_points[0][1] - min_y}"
        for point in connection.path_points[1:]:
            path_d += f" L {point[0] - min_x} {point[1] - min_y}"
        
        path = ET.SubElement(parent, 'path')
        path.set('d', path_d)
        path.set('class', 'connection')
        path.set('stroke', connection.color)
    
    def _add_legend_svg(self, svg: ET.Element, width: float, height: float, margin: float):
        """添加图例"""
        legend_group = ET.SubElement(svg, 'g')
        legend_group.set('transform', f'translate({margin}, {height - margin + 20})')
        
        # 图例背景
        bg = ET.SubElement(legend_group, 'rect')
        bg.set('width', '200')
        bg.set('height', '60')
        bg.set('fill', '#F5F5F5')
        bg.set('stroke', '#CCCCCC')
        
        # 图例项
        legend_items = [
            ('#E3F2FD', '#1976D2', '设备'),
            ('none', '#0066CC', '电缆'),
        ]
        
        for i, (fill, stroke, label) in enumerate(legend_items):
            y = 20 + i * 20
            
            item = ET.SubElement(legend_group, 'rect')
            item.set('x', '10')
            item.set('y', str(y - 8))
            item.set('width', '20')
            item.set('height', '12')
            item.set('fill', fill)
            item.set('stroke', stroke)
            
            text = ET.SubElement(legend_group, 'text')
            text.set('x', '40')
            text.set('y', str(y))
            text.set('class', 'device-label')
            text.text = label


class ExcelExporter:
    """Excel导出器"""
    
    def __init__(self, options: ExportOptions):
        self.options = options
    
    def export(self, data: RouteData, output_path: str) -> str:
        """
        导出Excel文件
        
        Args:
            data: 路径数据
            output_path: 输出文件路径
        
        Returns:
            输出文件路径
        """
        wb = openpyxl.Workbook()
        
        # 创建连接清单表
        ws_connections = wb.active
        ws_connections.title = "连接清单"
        self._create_connections_sheet(ws_connections, data)
        
        # 创建设备清单表
        ws_devices = wb.create_sheet("设备清单")
        self._create_devices_sheet(ws_devices, data)
        
        # 创建统计表
        ws_stats = wb.create_sheet("统计信息")
        self._create_stats_sheet(ws_stats, data)
        
        # 保存
        wb.save(output_path)
        
        return output_path
    
    def _create_connections_sheet(self, ws, data: RouteData):
        """创建连接清单工作表"""
        # 标题
        ws['A1'] = '连接清单'
        ws['A1'].font = Font(size=16, bold=True, color='1976D2')
        ws.merge_cells('A1:G1')
        
        # 表头
        headers = ['序号', '连接名称', '类型', '起点设备', '终点设备', '长度(m)', '路径点数量']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=3, column=col, value=header)
            cell.font = Font(bold=True, color='FFFFFF')
            cell.fill = PatternFill(start_color='1976D2', end_color='1976D2', fill_type='solid')
            cell.alignment = Alignment(horizontal='center', vertical='center')
        
        # 数据行
        for i, conn in enumerate(data.connections, 1):
            row = i + 3
            
            source_name = next((d.name for d in data.devices if d.id == conn.source_id), conn.source_id)
            target_name = next((d.name for d in data.devices if d.id == conn.target_id), conn.target_id)
            
            ws.cell(row=row, column=1, value=i)
            ws.cell(row=row, column=2, value=conn.name)
            ws.cell(row=row, column=3, value=conn.type)
            ws.cell(row=row, column=4, value=source_name)
            ws.cell(row=row, column=5, value=target_name)
            ws.cell(row=row, column=6, value=round(conn.length, 2))
            ws.cell(row=row, column=7, value=len(conn.path_points))
        
        # 合计行
        total_row = len(data.connections) + 4
        total_length = sum(c.length for c in data.connections)
        
        ws.cell(row=total_row, column=5, value='合计')
        ws.cell(row=total_row, column=5).font = Font(bold=True)
        ws.cell(row=total_row, column=6, value=round(total_length, 2))
        ws.cell(row=total_row, column=6).font = Font(bold=True)
        
        # 调整列宽
        for col in range(1, 8):
            ws.column_dimensions[get_column_letter(col)].width = 15
    
    def _create_devices_sheet(self, ws, data: RouteData):
        """创建设备清单工作表"""
        ws['A1'] = '设备清单'
        ws['A1'].font = Font(size=16, bold=True, color='1976D2')
        ws.merge_cells('A1:H1')
        
        headers = ['序号', '设备名称', '类型', 'X坐标', 'Y坐标', 'Z坐标', '宽度', '高度']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=3, column=col, value=header)
            cell.font = Font(bold=True, color='FFFFFF')
            cell.fill = PatternFill(start_color='1976D2', end_color='1976D2', fill_type='solid')
            cell.alignment = Alignment(horizontal='center', vertical='center')
        
        for i, device in enumerate(data.devices, 1):
            row = i + 3
            ws.cell(row=row, column=1, value=i)
            ws.cell(row=row, column=2, value=device.name)
            ws.cell(row=row, column=3, value=device.type)
            ws.cell(row=row, column=4, value=device.x)
            ws.cell(row=row, column=5, value=device.y)
            ws.cell(row=row, column=6, value=device.z)
            ws.cell(row=row, column=7, value=device.width)
            ws.cell(row=row, column=8, value=device.height)
        
        for col in range(1, 9):
            ws.column_dimensions[get_column_letter(col)].width = 12
    
    def _create_stats_sheet(self, ws, data: RouteData):
        """创建统计信息工作表"""
        ws['A1'] = '项目统计信息'
        ws['A1'].font = Font(size=16, bold=True, color='1976D2')
        ws.merge_cells('A1:C1')
        
        stats = [
            ('项目名称', self.options.project_name),
            ('导出日期', self.options.date),
            ('设备总数', len(data.devices)),
            ('连接总数', len(data.connections)),
            ('总长度(m)', round(sum(c.length for c in data.connections), 2)),
            ('平均长度(m)', round(sum(c.length for c in data.connections) / len(data.connections), 2) if data.connections else 0),
        ]
        
        for i, (label, value) in enumerate(stats, 3):
            ws.cell(row=i, column=1, value=label)
            ws.cell(row=i, column=1).font = Font(bold=True)
            ws.cell(row=i, column=2, value=value)
        
        ws.column_dimensions['A'].width = 20
        ws.column_dimensions['B'].width = 30


class ExportService:
    """导出服务主类"""
    
    EXPORTERS = {
        'pdf': PDFExporter,
        'svg': SVGExporter,
        'excel': ExcelExporter,
    }
    
    def __init__(self, output_dir: str = './exports'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def export(
        self,
        data: RouteData,
        options: ExportOptions,
        filename: Optional[str] = None
    ) -> str:
        """
        执行导出
        
        Args:
            data: 路径数据
            options: 导出选项
            filename: 文件名（可选）
        
        Returns:
            输出文件路径
        """
        if options.format not in self.EXPORTERS:
            raise ValueError(f"不支持的导出格式: {options.format}")
        
        # 生成文件名
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"route_export_{timestamp}.{options.format}"
        
        output_path = os.path.join(self.output_dir, filename)
        
        # 执行导出
        exporter_class = self.EXPORTERS[options.format]
        exporter = exporter_class(options)
        
        return exporter.export(data, output_path)
    
    def export_batch(
        self,
        data: RouteData,
        formats: List[str],
        options: Optional[ExportOptions] = None
    ) -> Dict[str, str]:
        """
        批量导出多种格式
        
        Args:
            data: 路径数据
            formats: 格式列表
            options: 导出选项（可选，每个格式使用相同选项）
        
        Returns:
            格式到文件路径的映射
        """
        results = {}
        
        for fmt in formats:
            if options:
                export_options = ExportOptions(
                    format=fmt,
                    page_size=options.page_size,
                    orientation=options.orientation,
                    title=options.title,
                    project_name=options.project_name
                )
            else:
                export_options = ExportOptions(format=fmt)
            
            try:
                path = self.export(data, export_options)
                results[fmt] = path
            except Exception as e:
                results[fmt] = f"错误: {str(e)}"
        
        return results


# 使用示例
if __name__ == "__main__":
    # 准备示例数据
    devices = [
        DeviceData(id='d1', name='设备A', type='server', x=100, y=100, width=40, height=30),
        DeviceData(id='d2', name='设备B', type='server', x=300, y=200, width=40, height=30),
        DeviceData(id='d3', name='设备C', type='switch', x=200, y=300, width=30, height=30),
    ]
    
    connections = [
        ConnectionData(
            id='c1',
            name='连接1',
            source_id='d1',
            target_id='d2',
            type='cable',
            path_points=[(100, 100, 0), (200, 100, 0), (200, 200, 0), (300, 200, 0)],
            length=223.6
        ),
        ConnectionData(
            id='c2',
            name='连接2',
            source_id='d2',
            target_id='d3',
            type='cable',
            path_points=[(300, 200, 0), (300, 250, 0), (200, 250, 0), (200, 300, 0)],
            length=170.7
        ),
    ]
    
    route_data = RouteData(
        devices=devices,
        connections=connections,
        bounds=(50, 50, 350, 350),
        grid_size=10.0
    )
    
    # 导出服务
    export_service = ExportService(output_dir='./test_exports')
    
    # PDF导出
    pdf_options = ExportOptions(
        format='pdf',
        page_size='A4',
        orientation='landscape',
        title='机房布线规划图',
        project_name='数据中心A区',
        author='工程师张三'
    )
    pdf_path = export_service.export(route_data, pdf_options, 'test_export.pdf')
    print(f"PDF导出完成: {pdf_path}")
    
    # SVG导出
    svg_options = ExportOptions(
        format='svg',
        title='机房布线规划图',
        project_name='数据中心A区'
    )
    svg_path = export_service.export(route_data, svg_options, 'test_export.svg')
    print(f"SVG导出完成: {svg_path}")
    
    # Excel导出
    excel_options = ExportOptions(
        format='excel',
        project_name='数据中心A区'
    )
    excel_path = export_service.export(route_data, excel_options, 'test_export.xlsx')
    print(f"Excel导出完成: {excel_path}")
