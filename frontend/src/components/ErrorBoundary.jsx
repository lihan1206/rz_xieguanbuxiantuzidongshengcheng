import React from 'react';
import { Result, Button } from 'antd';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error) {
    console.error('界面错误边界捕获异常', error);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="center-wrap">
          <Result
            status="error"
            title="页面出现异常"
            subTitle="请刷新页面后重试，若问题持续请联系管理员。"
            extra={<Button onClick={() => window.location.reload()}>刷新页面</Button>}
          />
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
