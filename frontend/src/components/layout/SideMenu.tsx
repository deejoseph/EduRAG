import React from 'react';
import { Menu, Badge } from 'antd';
import {
  HomeOutlined,
  EditOutlined,
  ThunderboltOutlined,
  LineChartOutlined,
  SearchOutlined,
  SettingOutlined,
  CloudUploadOutlined,
  BookOutlined,
  FireOutlined,
  SoundOutlined,
} from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';

const menuItems = [
  { key: '/', icon: <HomeOutlined />, label: '首页' },
  { key: '/writing', icon: <EditOutlined />, label: '引导练习' },
  { 
    key: '/practice', 
    icon: <ThunderboltOutlined style={{ color: '#faad14' }} />, 
    label: (
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <span style={{ fontWeight: 600, color: '#faad14' }}>强化训练</span>
        <Badge count="关键" style={{ backgroundColor: '#ff4d4f', fontSize: 10 }} />
      </div>
    ),
  },
  { key: '/growth-log', icon: <LineChartOutlined />, label: '成长日志' },
  { key: '/portfolio', icon: <BookOutlined />, label: '作品集' },
  { key: '/hot-topics', icon: <FireOutlined style={{ color: '#ff4d4f' }} />, label: '命题热点' },
  { key: '/podcast', icon: <SoundOutlined style={{ color: '#722ed1' }} />, label: '播客模块' },
  { key: '/search', icon: <SearchOutlined />, label: '知识检索' },
  { key: '/upload', icon: <CloudUploadOutlined />, label: '添加知识' },
  { key: '/settings', icon: <SettingOutlined />, label: '系统设置' },
];

const SideMenu: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const selectedKey = '/' + location.pathname.split('/')[1] || '/';

  return (
    <Menu
      mode="inline"
      selectedKeys={[selectedKey === '/' ? '/' : selectedKey]}
      items={menuItems}
      onClick={({ key }) => navigate(key)}
      style={{ borderRight: 0, marginTop: 8 }}
    />
  );
};

export default SideMenu;
