import { useEffect, useMemo, useState } from 'react';
import {
  App as AntdApp,
  Button,
  Card,
  Col,
  Form,
  Input,
  InputNumber,
  Modal,
  Row,
  Select,
  Skeleton,
  Space,
  Table,
  Tag,
  Typography,
} from 'antd';
import { useNavigate, useParams } from 'react-router-dom';
import { DeleteOutlined, PlusOutlined, ThunderboltOutlined } from '@ant-design/icons';

import client from '../api/client';
import { deviceSchema } from '../utils/validators';

export default function ProjectDetailPage() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const { message, modal } = AntdApp.useApp();

  const [project, setProject] = useState(null);
  const [deviceTypes, setDeviceTypes] = useState([]);
  const [cableTypes, setCableTypes] = useState([]);
  const [devices, setDevices] = useState([]);
  const [cables, setCables] = useState([]);
  const [versions, setVersions] = useState([]);
  const [issues, setIssues] = useState([]);
  const [loading, setLoading] = useState(true);
  const [routing, setRouting] = useState(false);
  const [openDevice, setOpenDevice] = useState(false);
  const [creatingDevice, setCreatingDevice] = useState(false);

  const [form] = Form.useForm();

  const loadData = async () => {
    setLoading(true);
    try {
      const [projectRes, deviceTypeRes, cableTypeRes, devicesRes, cablesRes, versionsRes, issuesRes] = await Promise.all([
        client.get(`/projects/${projectId}`),
        client.get('/device-types'),
        client.get('/cable-types'),
        client.get(`/projects/${projectId}/devices`),
        client.get(`/projects/${projectId}/cables`),
        client.get(`/projects/${projectId}/versions`),
        client.get(`/projects/${projectId}/validate`),
      ]);
      setProject(projectRes.data);
      setDeviceTypes(deviceTypeRes.data);
      setCableTypes(cableTypeRes.data);
      setDevices(devicesRes.data);
      setCables(cablesRes.data);
      setVersions(versionsRes.data);
      setIssues(issuesRes.data);
    } catch (error) {
      const detail = error?.response?.data?.detail || '加载项目详情失败';
      message.error(detail);
      if (error?.response?.status === 401) {
        navigate('/login');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [projectId]);

  const onCreateDevice = async (values) => {
    const parsed = deviceSchema.safeParse({
      ...values,
      device_type_id: Number(values.device_type_id),
      x: Number(values.x),
      y: Number(values.y),
    });
    if (!parsed.success) {
      message.error(parsed.error.issues[0].message);
      return;
    }

    setCreatingDevice(true);
    try {
      await client.post(`/projects/${projectId}/devices`, parsed.data);
      message.success('设备新增成功');
      form.resetFields();
      setOpenDevice(false);
      loadData();
    } catch (error) {
      const detail = error?.response?.data?.detail || '设备新增失败';
      message.error(detail);
    } finally {
      setCreatingDevice(false);
    }
  };

  const onDeleteDevice = (device) => {
    modal.confirm({
      title: '确认删除该设备吗？',
      content: `设备“${device.name}”删除后，相关连接将失效。`,
      okText: '确认删除',
      cancelText: '取消',
      okButtonProps: { danger: true },
      centered: true,
      onOk: async () => {
        await client.delete(`/projects/${projectId}/devices/${device.id}`);
        message.success('设备已删除');
        loadData();
      },
    });
  };

  const onAutoRoute = async () => {
    setRouting(true);
    try {
      const firstCableType = cableTypes[0];
      await client.post(`/projects/${projectId}/auto-route`, {
        connections: [],
        obstacles: [],
        cable_type_id: firstCableType?.id,
      });
      message.success('自动布线完成');
      loadData();
    } catch (error) {
      const detail = error?.response?.data?.detail || '自动布线失败';
      message.error(detail);
    } finally {
      setRouting(false);
    }
  };

  const onExport = async (fmt) => {
    try {
      const res = await client.get(`/projects/${projectId}/export/${fmt}`, { responseType: 'blob' });
      const blob = new Blob([res.data]);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `项目-${projectId}.${fmt}`;
      a.click();
      window.URL.revokeObjectURL(url);
      message.success(`已导出 ${fmt.toUpperCase()} 文件`);
    } catch (error) {
      const detail = error?.response?.data?.detail || '导出失败';
      message.error(detail);
    }
  };

  const deviceTypeMap = useMemo(() => {
    const map = {};
    deviceTypes.forEach((item) => {
      map[item.id] = item.name;
    });
    return map;
  }, [deviceTypes]);

  const deviceColumns = [
    { title: '设备名称', dataIndex: 'name' },
    { title: '设备类型', dataIndex: 'device_type_id', render: (v) => deviceTypeMap[v] || '-' },
    { title: '坐标X', dataIndex: 'x' },
    { title: '坐标Y', dataIndex: 'y' },
    {
      title: '操作',
      render: (_, record) => (
        <Button type="text" danger icon={<DeleteOutlined />} onClick={() => onDeleteDevice(record)}>
          删除
        </Button>
      ),
    },
  ];

  const cableTypeMap = useMemo(() => {
    const map = {};
    cableTypes.forEach((item) => {
      map[item.id] = item.name;
    });
    return map;
  }, [cableTypes]);

  const cableColumns = [
    { title: '线缆ID', dataIndex: 'id' },
    { title: '线缆类型', dataIndex: 'cable_type_id', render: (v) => cableTypeMap[v] || '-' },
    { title: '起点设备', dataIndex: 'start_device_id' },
    { title: '终点设备', dataIndex: 'end_device_id' },
    { title: '长度(m)', dataIndex: 'length', render: (v) => v.toFixed(1) },
  ];

  if (loading) {
    return (
      <div className="page-wrap">
        <Skeleton active paragraph={{ rows: 10 }} />
      </div>
    );
  }

  return (
    <div className="page-wrap">
      <Card className="hero-card" bordered={false}>
        <Row justify="space-between" align="middle" gutter={[16, 16]}>
          <Col>
            <Typography.Title level={3} style={{ margin: 0 }}>
              {project?.name}
            </Typography.Title>
            <Typography.Text type="secondary">
              地点：{project?.location || '未填写'} ｜ 用途：{project?.purpose || '未填写'}
            </Typography.Text>
          </Col>
          <Col>
            <Space>
              <Button onClick={() => navigate('/')}>返回项目列表</Button>
              <Button type="primary" icon={<ThunderboltOutlined />} onClick={onAutoRoute} loading={routing}>
                自动生成布线
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={14}>
          <Card
            title="设备与元件"
            extra={
              <Button type="primary" icon={<PlusOutlined />} onClick={() => setOpenDevice(true)}>
                新增设备
              </Button>
            }
            bordered={false}
          >
            <Table rowKey="id" columns={deviceColumns} dataSource={devices} pagination={{ pageSize: 6 }} />
          </Card>
        </Col>

        <Col xs={24} lg={10}>
          <Card title="规则校验结果" bordered={false}>
            <Space direction="vertical" style={{ width: '100%' }}>
              {issues.length === 0 ? <Tag color="success">当前布线符合规则</Tag> : null}
              {issues.map((issue, idx) => (
                <Tag
                  key={idx}
                  color={issue.level === 'error' ? 'error' : issue.level === 'warning' ? 'warning' : 'processing'}
                >
                  {issue.message}
                </Tag>
              ))}
            </Space>
          </Card>

          <Card title="导出布线图" bordered={false} style={{ marginTop: 16 }}>
            <Space wrap>
              <Button onClick={() => onExport('pdf')}>导出 PDF</Button>
              <Button onClick={() => onExport('svg')}>导出 SVG</Button>
              <Button onClick={() => onExport('dxf')}>导出 DXF</Button>
              <Button onClick={() => onExport('json')}>导出 JSON</Button>
            </Space>
          </Card>
        </Col>
      </Row>

      <Card title="线缆连接结果" bordered={false} style={{ marginTop: 16 }}>
        <Table rowKey="id" columns={cableColumns} dataSource={cables} pagination={{ pageSize: 6 }} />
      </Card>

      <Card title="历史版本" bordered={false} style={{ marginTop: 16 }}>
        <Table
          rowKey="id"
          dataSource={versions}
          columns={[
            { title: '版本号', dataIndex: 'version_no' },
            { title: '备注', dataIndex: 'note' },
            { title: '创建时间', dataIndex: 'created_at' },
          ]}
          pagination={{ pageSize: 5 }}
        />
      </Card>

      <Modal
        title="新增设备"
        open={openDevice}
        onCancel={() => setOpenDevice(false)}
        onOk={() => form.submit()}
        okText="保存设备"
        cancelText="取消"
        confirmLoading={creatingDevice}
        centered
      >
        <Form form={form} layout="vertical" onFinish={onCreateDevice}>
          <Form.Item label="设备名称" name="name" rules={[{ required: true, message: '请输入设备名称' }]}>
            <Input placeholder="例如：接入交换机-A1" />
          </Form.Item>
          <Form.Item label="设备类型" name="device_type_id" rules={[{ required: true, message: '请选择设备类型' }]}>
            <Select
              options={deviceTypes.map((item) => ({
                value: item.id,
                label: `${item.name}（${item.category}）`,
              }))}
              placeholder="请选择设备类型"
            />
          </Form.Item>
          <Row gutter={12}>
            <Col span={12}>
              <Form.Item label="坐标 X" name="x" rules={[{ required: true, message: '请输入 X 坐标' }]}>
                <InputNumber style={{ width: '100%' }} min={0} max={100} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="坐标 Y" name="y" rules={[{ required: true, message: '请输入 Y 坐标' }]}>
                <InputNumber style={{ width: '100%' }} min={0} max={100} />
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Modal>
    </div>
  );
}
