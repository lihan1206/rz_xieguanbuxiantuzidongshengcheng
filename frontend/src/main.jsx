import React from 'react';
import ReactDOM from 'react-dom/client';
import { App as AntdApp, ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import { BrowserRouter } from 'react-router-dom';

import App from './App';
import { AuthProvider } from './context/AuthContext';
import ErrorBoundary from './components/ErrorBoundary';
import './styles.css';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <ConfigProvider locale={zhCN} theme={{ token: { colorPrimary: '#0f766e', borderRadius: 10 } }}>
      <AntdApp>
        <ErrorBoundary>
          <BrowserRouter>
            <AuthProvider>
              <App />
            </AuthProvider>
          </BrowserRouter>
        </ErrorBoundary>
      </AntdApp>
    </ConfigProvider>
  </React.StrictMode>
);
