import { useEffect, useMemo, useState } from 'react';
import {
  App as AntdApp,
  Button,
  Card,
  Col,
  Form,
  Input,
  Modal,
  Row,
  Select,
  Skeleton,
  Space,
  Table,
  Tag,
  Typography,
} from 'antd';
import { useNavigate } from 'react-router-dom';
import { DeleteOutlined, PlusOutlined } from '@ant-design/icons';

import client from '../api/client';
import { useAuth } from '../context/AuthContext';
import { projectSchema } from '../utils/validators';

const statusColor = {
  进行中: 'processing',
  已完成: 'success',
  已归档: 'default',
};

export default function DashboardPage() {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [keyword, setKeyword] = useState('');
  const [status, setStatus] = useState(undefined);

  const navigate = useNavigate();
  const [form] = Form.useForm();
  const { message, modal } = AntdApp.useApp();
  const { logout, user, setUser } = useAuth();

  const loadMe = async () => {
    if (user) return;
    const { data } = await client.get('/auth/me');
    setUser(data);
  };

  const fetchProjects = async () => {
    setLoading(true);
    try {
      const { data } = await client.get('/projects', { params: { keyword, status } });
      setProjects(data);
    } catch (error) {
      const detail = error?.response?.data?.detail || '加载项目失败';
      message.error(detail);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMe().catch(() => {
      message.error('登录状态失效，请重新登录');
      logout();
      navigate('/login');
    });
  }, []);

  useEffect(() => {
    fetchProjects();
  }, [keyword, status]);

  const onCreate = async (values) => {
    const parsed = projectSchema.safeParse(values);
    if (!parsed.success) {
      message.error(parsed.error.issues[0].message);
      return;
    }

    setSubmitting(true);
    try {
      await client.post('/projects', values);
      message.success('项目创建成功');
      form.resetFields();
      setOpen(false);
      fetchProjects();
    } catch (error) {
      const detail = error?.response?.data?.detail || '创建项目失败';
      message.error(detail);
    } finally {
      setSubmitting(false);
    }
  };

  const onDeleteProject = (record) => {
    modal.confirm({
      title: '确认删除该项目吗？',
      content: `项目“${record.name}”及其设备、线缆、历史版本会被永久删除。`,
      okText: '确认删除',
      cancelText: '取消',
      okButtonProps: { danger: true },
      centered: true,
      onOk: async () => {
        await client.delete(`/projects/${record.id}`);
        message.success('项目已删除');
        fetchProjects();
      },
    });
  };

  const columns = useMemo(
    () => [
      { title: '项目名称', dataIndex: 'name' },
      { title: '地点', dataIndex: 'location' },
      { title: '用途', dataIndex: 'purpose', ellipsis: true },
      {
        title: '状态',
        dataIndex: 'status',
        render: (value) => <Tag color={statusColor[value] || 'default'}>{value}</Tag>,
      },
      {
        title: '操作',
        render: (_, record) => (
          <Space>
            <Button type="link" onClick={() => navigate(`/projects/${record.id}`)}>
              进入设计
            </Button>
            <Button type="text" danger icon={<DeleteOutlined />} onClick={() => onDeleteProject(record)}>
              删除
            </Button>
          </Space>
        ),
      },
    ],
    []
  );

  return (
    <div className="page-wrap">
      <Card className="hero-card" bordered={false}>
        <Row justify="space-between" align="middle" gutter={[16, 16]}>
          <Col>
            <Typography.Title level={2} style={{ margin: 0 }}>
              携观布线图自动生成软件
            </Typography.Title>
            <Typography.Text type="secondary">
              在这里创建项目、维护状态并进入自动布线设计页面。
            </Typography.Text>
          </Col>
          <Col>
            <Space>
              <Button onClick={() => { logout(); navigate('/login'); }}>退出登录</Button>
              <Button type="primary" icon={<PlusOutlined />} onClick={() => setOpen(true)}>
                新建项目
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      <Card bordered={false} style={{ marginTop: 16 }}>
        <Space wrap style={{ marginBottom: 12 }}>
          <Input.Search
            allowClear
            placeholder="按项目名称搜索"
            onSearch={(value) => setKeyword(value)}
            style={{ width: 260 }}
          />
          <Select
            allowClear
            placeholder="按状态筛选"
            style={{ width: 180 }}
            options={[
              { value: '进行中', label: '进行中' },
              { value: '已完成', label: '已完成' },
              { value: '已归档', label: '已归档' },
            ]}
            onChange={(value) => setStatus(value)}
          />
        </Space>
        {loading ? (
          <Skeleton active paragraph={{ rows: 6 }} />
        ) : (
          <Table rowKey="id" columns={columns} dataSource={projects} pagination={{ pageSize: 8 }} />
        )}
      </Card>

      <Modal
        title="新建布线项目"
        open={open}
        onCancel={() => setOpen(false)}
        onOk={() => form.submit()}
        okText="创建项目"
        cancelText="取消"
        confirmLoading={submitting}
        centered
      >
        <Form form={form} layout="vertical" onFinish={onCreate}>
          <Form.Item label="项目名称" name="name" rules={[{ required: true, message: '请输入项目名称' }]}>
            <Input placeholder="例如：园区弱电一期" />
          </Form.Item>
          <Form.Item label="项目地点" name="location">
            <Input placeholder="例如：上海市浦东新区" />
          </Form.Item>
          <Form.Item label="项目用途" name="purpose">
            <Input.TextArea placeholder="请输入项目用途说明" rows={3} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
