import React from 'react';
import { Menu } from 'antd';
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
} from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';

const menuItems = [
  { key: '/', icon: <HomeOutlined />, label: '首页' },
  { key: '/writing', icon: <EditOutlined />, label: '写作训练' },
  { key: '/practice', icon: <ThunderboltOutlined />, label: '强化训练' },
  { key: '/growth-log', icon: <LineChartOutlined />, label: '成长日志' },
  { key: '/portfolio', icon: <BookOutlined />, label: '作品集' },
  { key: '/hot-topics', icon: <FireOutlined style={{ color: '#ff4d4f' }} />, label: '命题热点' },
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
