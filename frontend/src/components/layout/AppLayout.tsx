import React, { useState } from 'react';
import { Layout } from 'antd';
import SideMenu from './SideMenu';

const { Content, Sider } = Layout;

interface AppLayoutProps {
  children: React.ReactNode;
}

const AppLayout: React.FC<AppLayoutProps> = ({ children }) => {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        theme="light"
        width={220}
        style={{ borderRight: '1px solid #f0f0f0' }}
      >
        <div style={{
          height: 64,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontWeight: 700,
          fontSize: collapsed ? 16 : 20,
          color: '#1890ff',
          borderBottom: '1px solid #f0f0f0',
        }}>
          {collapsed ? 'Edu' : 'EduRAG 写作助手'}
        </div>
        <SideMenu />
      </Sider>
      <Layout>
        <Content style={{ overflow: 'auto', background: '#f5f7fa' }}>
          {children}
        </Content>
      </Layout>
    </Layout>
  );
};

export default AppLayout;
