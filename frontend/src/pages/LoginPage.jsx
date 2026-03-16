import { useEffect, useState } from 'react';
import { Button, Card, Form, Input, Typography, App as AntdApp } from 'antd';
import { useNavigate } from 'react-router-dom';

import client from '../api/client';
import { useAuth } from '../context/AuthContext';
import { loginSchema } from '../utils/validators';

const { Title, Text } = Typography;

export default function LoginPage() {
  const [loading, setLoading] = useState(false);
  const { token, login, setUser } = useAuth();
  const navigate = useNavigate();
  const { message } = AntdApp.useApp();

  useEffect(() => {
    if (token) {
      navigate('/');
    }
  }, [token, navigate]);

  const onFinish = async (values) => {
    const parsed = loginSchema.safeParse(values);
    if (!parsed.success) {
      message.error(parsed.error.issues[0].message);
      return;
    }

    setLoading(true);
    try {
      const { data } = await client.post('/auth/login', values);
      login(data.access_token);
      const me = await client.get('/auth/me', {
        headers: { Authorization: `Bearer ${data.access_token}` },
      });
      setUser(me.data);
      message.success('登录成功');
      navigate('/');
    } catch (error) {
      const detail = error?.response?.data?.detail || '登录失败，请检查账号密码';
      message.error(detail);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-bg">
      <Card className="login-card" bordered={false}>
        <Title level={3} style={{ marginTop: 0 }}>
          携观布线图自动生成软件
        </Title>
        <Text type="secondary">请使用系统账号登录，默认管理员：admin / 123456</Text>
        <Form layout="vertical" onFinish={onFinish} style={{ marginTop: 20 }}>
          <Form.Item label="账号" name="username" rules={[{ required: true, message: '请输入账号' }]}>
            <Input placeholder="请输入账号" />
          </Form.Item>
          <Form.Item label="密码" name="password" rules={[{ required: true, message: '请输入密码' }]}>
            <Input.Password placeholder="请输入密码" />
          </Form.Item>
          <Button type="primary" htmlType="submit" loading={loading} block>
            登录系统
          </Button>
        </Form>
      </Card>
    </div>
  );
}
