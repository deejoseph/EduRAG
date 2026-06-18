import React from 'react';
import { Spin } from 'antd';

interface LoadingOverlayProps {
  loading: boolean;
  text?: string;
  children?: React.ReactNode;
}

const LoadingOverlay: React.FC<LoadingOverlayProps> = ({ loading, text = 'AI 正在思考中，请稍候...', children }) => {
  if (!loading) return <>{children}</>;

  return (
    <div className="loading-container">
      <Spin size="large" />
      <div style={{ marginTop: 16, fontSize: 15, color: '#666' }}>{text}</div>
    </div>
  );
};

export default LoadingOverlay;
