import React from 'react';
import { Collapse, Tag, Typography } from 'antd';
import { FileTextOutlined } from '@ant-design/icons';
import type { Reference } from '../../types/api';

const { Text, Paragraph } = Typography;

interface ReferencePanelProps {
  references: Reference[];
  title?: string;
}

const ReferencePanel: React.FC<ReferencePanelProps> = ({ references }) => {
  if (!references || references.length === 0) return null;

  const items = references.map((ref, idx) => {
    const meta = ref.metadata || {};
    const tags = [];
    if (meta.year) tags.push(<Tag color="blue" key="year">{meta.year}年</Tag>);
    if (meta.exam_region) tags.push(<Tag color="green" key="region">{meta.exam_region}</Tag>);
    if (meta.doc_category) tags.push(<Tag color="orange" key="cat">{meta.doc_category}</Tag>);
    if (meta.question_type) tags.push(<Tag color="purple" key="qt">{meta.question_type}</Tag>);
    if (meta.source_file) tags.push(<Tag key="file">{meta.source_file}</Tag>);

    return {
      key: String(idx),
      label: (
        <span>
          <FileTextOutlined style={{ marginRight: 8 }} />
          参考 {idx + 1} {meta.source_file && <Text type="secondary" style={{ fontSize: 12 }}>({meta.source_file})</Text>}
        </span>
      ),
      children: (
        <div>
          <div style={{ marginBottom: 8 }}>{tags}</div>
          <Paragraph ellipsis={{ rows: 5, expandable: true, symbol: '展开' }}>
            {ref.text}
          </Paragraph>
        </div>
      ),
    };
  });

  return (
    <div className="reference-panel" style={{ marginTop: 16 }}>
      <Collapse items={items} ghost size="small" />
    </div>
  );
};

export default ReferencePanel;
