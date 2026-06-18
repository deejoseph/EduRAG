import React, { useState, useEffect } from 'react';
import {
  Card, Upload, Button, Select, Table, Tag, Typography,
  Space, message, Alert, Popconfirm, Divider,
} from 'antd';
import {
  InboxOutlined, UploadOutlined, CheckCircleOutlined,
  CloseCircleOutlined, DeleteOutlined, DatabaseOutlined,
  ReloadOutlined, CloudUploadOutlined,
} from '@ant-design/icons';
import { uploadApi } from '../../api/upload';
import type { FileImportResult, UploadResponse } from '../../api/upload';
import { searchApi } from '../../api/search';

const { Title, Text } = Typography;
const { Dragger } = Upload;

interface CollectionInfo {
  name: string;
  count: number;
  metadata?: Record<string, any>;
}

const UploadPage: React.FC = () => {
  const [collections, setCollections] = useState<CollectionInfo[]>([]);
  const [selectedCollection, setSelectedCollection] = useState<string>('chinese_essays');
  const [fileList, setFileList] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [results, setResults] = useState<FileImportResult[] | null>(null);
  const [uploadResponse, setUploadResponse] = useState<UploadResponse | null>(null);
  const [loadingCollections, setLoadingCollections] = useState(false);

  const fetchCollections = async () => {
    try {
      setLoadingCollections(true);
      const res = await searchApi.collections();
      setCollections(res.collections || []);
    } catch {
      message.error('获取集合列表失败');
    } finally {
      setLoadingCollections(false);
    }
  };

  useEffect(() => {
    fetchCollections();
  }, []);

  const handleUpload = async () => {
    if (fileList.length === 0) {
      message.warning('请先选择要上传的文件');
      return;
    }

    setUploading(true);
    setResults(null);
    setUploadResponse(null);

    try {
      const res = await uploadApi.uploadFiles(fileList, selectedCollection);
      setUploadResponse(res);
      setResults(res.results);

      if (res.success_count > 0) {
        message.success(
          `导入完成！成功 ${res.success_count}/${res.total_files} 个文件，共 ${res.total_chunks} 个文档块`,
        );
        // 刷新集合统计
        fetchCollections();
      } else {
        message.warning('没有文件导入成功，请检查文件格式');
      }
    } catch (err: any) {
      const errMsg = err?.response?.data?.error || '上传失败，请检查后端服务';
      message.error(errMsg, 5);
    } finally {
      setUploading(false);
    }
  };

  const handleClear = () => {
    setFileList([]);
    setResults(null);
    setUploadResponse(null);
  };

  const handleDeleteCollection = async (name: string) => {
    try {
      await uploadApi.deleteCollection(name);
      message.success(`集合 ${name} 已删除`);
      fetchCollections();
    } catch (err: any) {
      const errMsg = err?.response?.data?.error || '删除失败';
      message.error(errMsg, 5);
    }
  };

  // 结果表格列
  const resultColumns = [
    {
      title: '文件名',
      dataIndex: 'filename',
      key: 'filename',
      ellipsis: true,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) =>
        status === 'success' ? (
          <Tag icon={<CheckCircleOutlined />} color="success">成功</Tag>
        ) : (
          <Tag icon={<CloseCircleOutlined />} color="error">失败</Tag>
        ),
    },
    {
      title: '文档块数',
      dataIndex: 'chunks',
      key: 'chunks',
      width: 100,
      align: 'center' as const,
    },
    {
      title: '文本长度',
      dataIndex: 'text_length',
      key: 'text_length',
      width: 100,
      render: (v: number | undefined) => v ? `${v.toLocaleString()} 字` : '-',
    },
    {
      title: '说明',
      key: 'info',
      render: (_: any, record: FileImportResult) =>
        record.error ? (
          <Text type="danger" ellipsis>{record.error}</Text>
        ) : (
          <Text type="secondary">{record.title || '-'}</Text>
        ),
    },
  ];

  // 集合表格列
  const collectionColumns = [
    {
      title: '集合名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '文档数量',
      dataIndex: 'count',
      key: 'count',
      render: (v: number) => (
        <Tag color="blue">{v.toLocaleString()} 条</Tag>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_: any, record: CollectionInfo) => {
        const isProtected = ['chinese_essays', 'exam_papers'].includes(record.name);
        return isProtected ? (
          <Text type="secondary">核心集合</Text>
        ) : (
          <Popconfirm
            title="确认删除"
            description={`确定要删除集合 "${record.name}" 吗？此操作不可恢复。`}
            onConfirm={() => handleDeleteCollection(record.name)}
            okText="删除"
            cancelText="取消"
            okButtonProps={{ danger: true }}
          >
            <Button type="link" danger size="small" icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        );
      },
    },
  ];

  return (
    <div className="page-container">
      <Space style={{ marginBottom: 24, width: '100%', justifyContent: 'space-between' }}>
        <Title level={4} style={{ margin: 0 }}>
          <CloudUploadOutlined style={{ marginRight: 8 }} />
          知识库管理
        </Title>
        <Button icon={<ReloadOutlined />} onClick={fetchCollections} loading={loadingCollections}>
          刷新
        </Button>
      </Space>

      {/* 上传区域 */}
      <Card title="上传文档" style={{ marginBottom: 16 }}>
        <Space style={{ marginBottom: 16 }}>
          <Text>目标集合：</Text>
          <Select
            value={selectedCollection}
            onChange={setSelectedCollection}
            style={{ width: 240 }}
            options={collections.map(c => ({
              label: `${c.name} (${c.count.toLocaleString()} 条)`,
              value: c.name,
            }))}
          />
        </Space>

        <Dragger
          accept=".pdf,.docx"
          multiple
          showUploadList={false}
          beforeUpload={(file) => {
            setFileList(prev => [...prev, file]);
            return false; // 阻止自动上传
          }}
          disabled={uploading}
        >
          <p className="ant-upload-drag-icon">
            <InboxOutlined />
          </p>
          <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
          <p className="ant-upload-hint">
            支持 PDF、DOCX 格式，可一次选择多个文件
          </p>
        </Dragger>

        {/* 已选文件列表 */}
        {fileList.length > 0 && (
          <>
            <Divider />
            <Space style={{ marginBottom: 12 }}>
              <Text strong>已选择 {fileList.length} 个文件</Text>
              <Button size="small" onClick={handleClear} disabled={uploading}>
                清空列表
              </Button>
            </Space>
            <Table
              dataSource={fileList.map((f, i) => ({
                key: i,
                name: f.name,
                size: `${(f.size / 1024).toFixed(1)} KB`,
                type: f.name.split('.').pop()?.toUpperCase() || '-',
              }))}
              columns={[
                { title: '文件名', dataIndex: 'name', key: 'name', ellipsis: true },
                { title: '格式', dataIndex: 'type', key: 'type', width: 80 },
                { title: '大小', dataIndex: 'size', key: 'size', width: 100 },
              ]}
              size="small"
              pagination={false}
              scroll={{ y: 200 }}
            />
            <Divider />
            <Space>
              <Button
                type="primary"
                icon={<UploadOutlined />}
                onClick={handleUpload}
                loading={uploading}
                size="large"
              >
                开始导入
              </Button>
              {uploading && <Text type="secondary">正在处理，请稍候...</Text>}
            </Space>
          </>
        )}
      </Card>

      {/* 上传结果 */}
      {results && uploadResponse && (
        <Card title="导入结果" style={{ marginBottom: 16 }}>
          <Alert
            type={uploadResponse.success_count > 0 ? 'success' : 'warning'}
            showIcon
            style={{ marginBottom: 16 }}
            message={
              uploadResponse.success_count > 0
                ? `成功导入 ${uploadResponse.success_count}/${uploadResponse.total_files} 个文件，新增 ${uploadResponse.total_chunks} 个文档块`
                : '没有文件导入成功'
            }
            description={
              uploadResponse.success_count > 0
                ? `目标集合：${uploadResponse.collection}`
                : '请检查文件格式是否正确（仅支持 PDF 和 DOCX）'
            }
          />
          <Table
            dataSource={results.map((r, i) => ({ ...r, key: i }))}
            columns={resultColumns}
            size="small"
            pagination={false}
          />
        </Card>
      )}

      {/* 知识库集合列表 */}
      <Card
        title={
          <Space>
            <DatabaseOutlined />
            知识库集合
          </Space>
        }
      >
        <Table
          dataSource={collections.map(c => ({ ...c, key: c.name }))}
          columns={collectionColumns}
          size="small"
          pagination={false}
          loading={loadingCollections}
        />
      </Card>
    </div>
  );
};

export default UploadPage;
