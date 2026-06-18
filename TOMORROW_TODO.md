# 2026-06-19 待办清单

## 🎯 今日目标

修复命题热点搜索超时问题，并开始实现题库管理功能。

---

## ✅ P0 - 紧急任务（必须完成）

### 1. 修复搜索超时问题

- [ ] **重启后端服务**
  ```bash
  # 终止当前进程
  taskkill /F /IM python.exe
  
  # 重新启动
  cd d:/PixelSmile/EduRAG
  C:/Users/deejo/anaconda3/envs/pixel_ai/python.exe start_backend.py
  ```

- [ ] **测试API响应**
  ```bash
  curl -X POST http://localhost:5000/hot-topics/search \
    -H "Content-Type: application/json" \
    -d '{"category_id": "technology"}'
  ```
  - 预期：2分钟内返回结果
  - 如果失败，检查后端日志

- [ ] **验证缓存机制**
  - 第二次调用应该立即返回（<10秒）
  - 检查 `data/hot_topics_cache/` 目录

- [ ] **检查Ollama服务**
  ```bash
  curl http://localhost:11434/api/tags
  ```
  - 如果无响应，重启Ollama：`ollama serve`

---

## 📝 P1 - 重要任务（尽量完成）

### 2. 设计题库管理功能

- [ ] **确定数据存储方案**
  - 选项A：复用portfolio表（快速实现）
  - 选项B：创建新的essay_topics表（结构清晰）
  - **建议**：先选A，后续可迁移到B

- [ ] **设计API接口**
  ```
  POST   /hot-topics/favorite/<topic_id>    # 收藏话题
  DELETE /hot-topics/favorite/<topic_id>    # 取消收藏
  GET    /hot-topics/favorites              # 获取收藏列表
  ```

### 3. 实现收藏功能（后端）

- [ ] 在 `api/routes/hot_topics.py` 添加收藏API
- [ ] 在 `frontend/src/api/hotTopics.ts` 添加API调用
- [ ] 测试收藏/取消收藏流程

### 4. 优化热点话题展示（前端）

- [ ] 在话题卡片添加"收藏"按钮
- [ ] 显示收藏状态（已收藏/未收藏）
- [ ] 添加简单的动画反馈

---

## 🔧 P2 - 可选任务（时间允许可做）

### 5. 创建"我的题库"页面框架

- [ ] 创建 `frontend/src/pages/MyTopics/index.tsx`
- [ ] 添加到路由配置
- [ ] 实现基本的列表展示

### 6. 集成到写作训练

- [ ] 在写作训练页面添加"从题库选题"按钮
- [ ] 点击后显示题库选择对话框（可以先用Mock数据）

---

## 📊 进度追踪

| 任务 | 优先级 | 状态 | 备注 |
|------|--------|------|------|
| 修复搜索超时 | P0 | ⏳ 待开始 | 最关键 |
| 设计题库功能 | P1 | ⏳ 待开始 | 需要决策 |
| 实现收藏API | P1 | ⏳ 待开始 | 依赖设计 |
| 优化前端展示 | P1 | ⏳ 待开始 | 用户体验 |
| 创建题库页面 | P2 | ⏳ 待开始 | 可选 |
| 集成到训练 | P2 | ⏳ 待开始 | 可选 |

---

## 💡 注意事项

1. **点数管理**
   - 今天剩余：~23点
   - 明天重置：2000点
   - 预计使用：~300点
   - **策略**：优先完成P0任务

2. **技术要点**
   - 确保后端服务正确重启
   - 测试前清除浏览器缓存
   - 关注后端日志输出

3. **备选方案**
   - 如果Ollama持续不稳定，考虑完全使用降级数据
   - 可以先把UI做好，后端API用Mock数据

---

## 🔗 相关文档

- [命题热点搜索问题记录.md](./命题热点搜索问题记录.md)
- [项目开发进度.md](./项目开发进度.md)

---

**开始时间**: 明天上午  
**预计完成**: 明天下午  
**最后更新**: 2026-06-18 23:00
