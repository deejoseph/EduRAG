/**
 * 每日金句组件
 * 显示从知识库中提取的随机名人名言，支持循环滚动
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Card, Typography, Spin, message } from 'antd';
import { BulbOutlined, CopyOutlined } from '@ant-design/icons';
import apiClient from '../../api/client';

const { Text } = Typography;

interface Quote {
  id: string;
  text: string;
  author: string;
  category: string;
}

const DailyQuote: React.FC<{ collapsed?: boolean }> = ({ collapsed }) => {
  const [quote, setQuote] = useState<Quote | null>(null);
  const [loading, setLoading] = useState(true);
  const [currentIndex, setCurrentIndex] = useState(0);

  // 默认名言（API失败时使用）
  const defaultQuotes: Quote[] = [
    {
      id: 'default_1',
      text: '学而不思则罔，思而不学则殆。',
      author: '孔子',
      category: '学习'
    },
    {
      id: 'default_2',
      text: '读书破万卷，下笔如有神。',
      author: '杜甫',
      category: '读书'
    },
    {
      id: 'default_3',
      text: '不积跬步，无以至千里；不积小流，无以成江海。',
      author: '荀子',
      category: '积累'
    }
  ];

  // 获取每日金句
  const fetchDailyQuote = useCallback(async () => {
    try {
      setLoading(true);
      const response = await apiClient.get('/quotes/daily');
      
      if (response.success) {
        setQuote(response.quote);
        
        // 记录学习日志（查看）
        await apiClient.post('/quotes/log', {
          quote_id: response.quote.id,
          action: 'view'
        }).catch(console.error); // 日志记录失败不影响显示
      } else {
        // API返回失败，使用默认名言
        const randomIndex = Math.floor(Math.random() * defaultQuotes.length);
        setQuote(defaultQuotes[randomIndex]);
      }
    } catch (error) {
      console.warn('获取每日金句失败，使用默认名言:', error);
      // API失败时，使用默认名言
      const randomIndex = Math.floor(Math.random() * defaultQuotes.length);
      setQuote(defaultQuotes[randomIndex]);
    } finally {
      setLoading(false);
    }
  }, []);

  // 初始加载
  useEffect(() => {
    fetchDailyQuote();
    
    // 每天凌晨自动刷新（检查时间变化）
    const interval = setInterval(() => {
      const now = new Date();
      if (now.getHours() === 0 && now.getMinutes() === 0) {
        fetchDailyQuote();
      }
    }, 60000); // 每分钟检查一次
    
    return () => clearInterval(interval);
  }, [fetchDailyQuote]);

  // 复制名言到剪贴板
  const handleCopy = async () => {
    if (!quote) return;
    
    try {
      await navigator.clipboard.writeText(`${quote.text} —— ${quote.author}`);
      message.success('已复制到剪贴板');
      
      // 记录复制行为
      await apiClient.post('/quotes/log', {
        quote_id: quote.id,
        action: 'copy'
      }).catch(console.error);
    } catch (error) {
      message.error('复制失败');
    }
  };

  if (collapsed) {
    return null; // 折叠时不显示
  }

  if (loading) {
    return (
      <div style={{
        padding: '12px 16px',
        borderBottom: '1px solid #f0f0f0',
        background: '#fafafa',
      }}>
        <Spin size="small" />
      </div>
    );
  }

  if (!quote) {
    // 不应该到达这里，但以防万一
    return null;
  }

  return (
    <Card
      size="small"
      style={{
        margin: '8px 12px',
        borderRadius: 8,
        boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
        border: 'none',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      }}
      bodyStyle={{ padding: '12px 16px' }}
    >
      <div style={{ color: '#fff' }}>
        <div style={{ 
          display: 'flex', 
          alignItems: 'center', 
          marginBottom: 8,
          fontSize: 12,
          opacity: 0.9
        }}>
          <BulbOutlined style={{ marginRight: 6 }} />
          <span>每日金句</span>
        </div>
        
        <div 
          onClick={handleCopy}
          style={{ 
            cursor: 'pointer',
            minHeight: 40,
            lineHeight: 1.6,
            fontSize: 14,
            fontWeight: 500,
            marginBottom: 8,
            transition: 'opacity 0.3s',
          }}
          onMouseEnter={(e) => e.currentTarget.style.opacity = '0.8'}
          onMouseLeave={(e) => e.currentTarget.style.opacity = '1'}
        >
          {quote.text}
        </div>
        
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          fontSize: 12,
          opacity: 0.85,
        }}>
          <span>—— {quote.author}</span>
          <CopyOutlined 
            onClick={handleCopy}
            style={{ cursor: 'pointer' }}
            title="复制名言"
          />
        </div>
      </div>
    </Card>
  );
};

export default DailyQuote;
