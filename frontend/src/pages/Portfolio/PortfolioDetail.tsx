import React, { useEffect, useState } from 'react';
import {
  Modal, Button, Tag, Space, Typography, Divider, Input, message, Tabs, Card,
} from 'antd';
import { StarOutlined, StarFilled, TagsOutlined, BookOutlined, FileTextOutlined, RobotOutlined } from '@ant-design/icons';
import type { PortfolioItem } from '../../types/portfolio';
import { getPortfolioItem, updatePortfolioItem, toggleStar, addTag, removeTag } from '../../api/portfolio';
import MarkdownRenderer from '../../components/common/MarkdownRenderer';

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;

interface PortfolioDetailProps {
  visible: boolean;
  itemId: string | null;
  onClose: () => void;
  onUpdate: () => void;
}

const PortfolioDetail: React.FC<PortfolioDetailProps> = ({ visible, itemId, onClose, onUpdate }) => {
  const [loading, setLoading] = useState(false);
  const [item, setItem] = useState<PortfolioItem | null>(null);
  const [editingNotes, setEditingNotes] = useState(false);
  const [notesValue, setNotesValue] = useState('');
  const [newTag, setNewTag] = useState('');

  const loadItem = async () => {
    if (!itemId) return;
    setLoading(true);
    try {
      const res = await getPortfolioItem(itemId);
      setItem(res.item);
      setNotesValue(res.item.notes || '');
    } catch (error) {
      message.error('加载失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (visible && itemId) {
      loadItem();
    }
  }, [visible, itemId]);

  const handleToggleStar = async () => {
    if (!itemId) return;
    try {
      await toggleStar(itemId);
      message.success('星标状态已更新');
      loadItem();
      onUpdate();
    } catch (error) {
      message.error('操作失败');
    }
  };

  const handleSaveNotes = async () => {
    if (!itemId) return;
    try {
      await updatePortfolioItem(itemId, { notes: notesValue });
      message.success('笔记已保存');
      setEditingNotes(false);
      loadItem();
      onUpdate();
    } catch (error) {
      message.error('保存失败');
    }
  };

  const handleAddTag = async () => {
    if (!itemId || !newTag.trim()) return;
    try {
      await addTag(itemId, newTag.trim());
      message.success('标签已添加');
      setNewTag('');
      loadItem();
      onUpdate();
    } catch (error) {
      message.error('添加失败');
    }
  };

  const handleRemoveTag = async (tag: string) => {
    if (!itemId) return;
    try {
      await removeTag(itemId, tag);
      message.success('标签已删除');
      loadItem();
      onUpdate();
    } catch (error) {
      message.error('删除失败');
    }
  };

  if (!item) {
    return (
      <Modal title="作品详情" open={visible} onCancel={onClose} footer={null} width={900} loading={loading}>
        加载中...
      </Modal>
    );
  }

  return (
    <Modal
      title={
        <Space>
          <BookOutlined />
          {item.title}
          {item.score && <Tag color="blue">{item.score}分</Tag>}
          {item.starred && <StarFilled style={{ color: '#faad14' }} />}
        </Space>
      }
      open={visible}
      onCancel={onClose}
      footer={[
        <Button key="close" onClick={onClose}>关闭</Button>,
        <Button key="star" icon={item.starred ? <StarFilled /> : <StarOutlined />} onClick={handleToggleStar}>
          {item.starred ? '取消星标' : '添加星标'}
        </Button>,
      ]}
      width={900}
      bodyStyle={{ maxHeight: '70vh', overflowY: 'auto' }}
    >
      <Tabs
        defaultActiveKey="content"
        items={[
          {
            key: 'content',
            label: <span><FileTextOutlined /> 作文内容</span>,
            children: (
              <div>
                {item.topic && (
                  <Card size="small" style={{ marginBottom: 16 }}>
                    <Title level={5}>题目</Title>
                    <Paragraph>{item.topic}</Paragraph>
                    <Space wrap>
                      {item.essay_type && <Tag color="blue">{item.essay_type}</Tag>}
                      {item.essay_style && <Tag color="green">{item.essay_style}</Tag>}
                      {item.grade_level && <Tag color="geekblue">{item.grade_level}</Tag>}
                      {item.exam_year && <Tag color="purple">{item.exam_year}年</Tag>}
                      {item.exam_region && <Tag color="cyan">{item.exam_region}</Tag>}
                      {item.word_count && <Tag>{item.word_count}字</Tag>}
                    </Space>
                  </Card>
                )}

                <div style={{ marginBottom: 16 }}>
                  <Space wrap>
                    <TagsOutlined />
                    <Text strong>标签：</Text>
                    {item.tags.map((tag) => (
                      <Tag key={tag} closable onClose={() => handleRemoveTag(tag)}>{tag}</Tag>
                    ))}
                    <Input size="small" placeholder="添加标签" style={{ width: 120 }} value={newTag} onChange={(e) => setNewTag(e.target.value)} onPressEnter={handleAddTag} />
                  </Space>
                </div>

                <Divider />
                <div style={{ whiteSpace: 'pre-wrap', lineHeight: 1.8 }}>{item.content}</div>
              </div>
            ),
          },
          {
            key: 'feedback',
            label: <span><RobotOutlined /> AI 评估</span>,
            children: item.ai_feedback ? (
              <div>
                {item.score && (
                  <Card size="small" style={{ marginBottom: 16 }}>
                    <Title level={5}>评分</Title>
                    <Space wrap>
                      <Tag color="blue">总分: {item.score}/100</Tag>
                      {item.evaluation_scores?.content && <Tag>内容立意: {item.evaluation_scores.content}/25</Tag>}
                      {item.evaluation_scores?.structure && <Tag>结构安排: {item.evaluation_scores.structure}/25</Tag>}
                      {item.evaluation_scores?.language && <Tag>语言表达: {item.evaluation_scores.language}/25</Tag>}
                      {item.evaluation_scores?.development && <Tag>发展等级: {item.evaluation_scores.development}/25</Tag>}
                    </Space>
                  </Card>
                )}
                <MarkdownRenderer content={item.ai_feedback} />
              </div>
            ) : (
              <div style={{ textAlign: 'center', padding: 40 }}><Text type="secondary">暂无 AI 评估</Text></div>
            ),
          },
          {
            key: 'notes',
            label: <span><FileTextOutlined /> 学习笔记</span>,
            children: (
              <div>
                <Text type="secondary">记录你的学习心得、写作技巧总结或需要重点关注的地方</Text>
                <Divider />
                {editingNotes ? (
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <TextArea rows={8} value={notesValue} onChange={(e) => setNotesValue(e.target.value)} placeholder="写下你的学习笔记..." />
                    <Space>
                      <Button type="primary" onClick={handleSaveNotes}>保存</Button>
                      <Button onClick={() => setEditingNotes(false)}>取消</Button>
                    </Space>
                  </Space>
                ) : (
                  <div>
                    {item.notes ? <div style={{ whiteSpace: 'pre-wrap', lineHeight: 1.8 }}>{item.notes}</div> : <Text type="secondary">还没有笔记</Text>}
                    <Button type="link" onClick={() => setEditingNotes(true)} style={{ marginTop: 8 }}>
                      {item.notes ? '编辑笔记' : '添加笔记'}
                    </Button>
                  </div>
                )}
              </div>
            ),
          },
        ]}
      />
    </Modal>
  );
};

export default PortfolioDetail;
