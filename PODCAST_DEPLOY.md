# 播客部署指南

本指南说明如何将生成的播客文案部署到GitHub Pages，并发布到小宇宙等播客平台。

## 📋 前置准备

### 1. 启用GitHub Pages

1. 访问你的仓库: https://github.com/deejoseph/EduRAG
2. 进入 **Settings** → **Pages**
3. 在 **Build and deployment** 中配置:
   - Source: **Deploy from a branch**
   - Branch: **main** / **root**
   - Folder: **/(Root)**
4. 点击 **Save**

> ⚠️ 注意：首次启用后，GitHub会分配一个URL，格式为：
> `https://deejoseph.github.io/EduRAG/`

### 2. 验证GitHub Pages

部署工作流第一次运行后，访问以下URL验证：
- RSS Feed: `https://deejoseph.github.io/EduRAG/feed.xml`
- 音频目录: `https://deejoseph.github.io/EduRAG/audio/`

---

## 🚀 自动化部署

### 方法一：使用部署脚本（推荐）

```bash
# 进入项目根目录
cd d:\PixelSmile\EduRAG

# 运行部署脚本
python scripts/deploy_podcast.py
```

**脚本功能**：
1. ✅ 从数据库获取所有已完成的播客文案
2. ⚠️ 生成TTS音频文件（当前为占位符，待实现）
3. ✅ 生成RSS Feed XML文件
4. ✅ 自动提交并推送到GitHub
5. ✅ GitHub Actions自动部署到Pages

**可选参数**：
```bash
# 跳过音频生成（仅更新RSS）
python scripts/deploy_podcast.py --skip-audio

# 限制处理的文案数量
python scripts/deploy_podcast.py --limit 10
```

### 方法二：手动部署

```bash
# 1. 生成RSS文件（通过API或手动创建）
# 2. 将文件放入 podcast-output/ 目录
# 3. 提交并推送
git add podcast-output/
git commit -m "chore: 更新播客文件"
git push origin main
```

---

## 🎙️ 发布到播客平台

### 小宇宙

1. **等待部署完成**（约1-2分钟）
2. 访问RSS URL验证：`https://deejoseph.github.io/EduRAG/feed.xml`
3. 打开小宇宙APP
4. 进入 **我** → **创作者中心** → **添加播客**
5. 输入RSS URL: `https://deejoseph.github.io/EduRAG/feed.xml`
6. 填写播客信息并提交审核
7. 等待审核通过（通常1-3个工作日）

### Apple Podcasts

1. 使用Apple ID登录 [Apple Podcasts Connect](https://podcastsconnect.apple.com/)
2. 点击 **+** 添加新播客
3. 输入RSS URL
4. 验证信息并提交
5. 等待审核（通常3-5个工作日）

### Spotify

1. 访问 [Spotify for Podcasters](https://podcasters.spotify.com/)
2. 注册/登录账号
3. 点击 **Get started**
4. 输入RSS URL
5. 验证所有权并完成设置

### 其他平台

大多数播客平台都支持RSS订阅模式，流程类似：
1. 找到平台的"添加播客"或"订阅"功能
2. 输入你的RSS URL
3. 等待审核通过

---

## ⚠️ 重要提示

### 音频文件问题

**当前状态**：
- 🚧 TTS音频生成功能尚未实现
- RSS中的音频URL是占位符：`https://deejoseph.github.io/EduRAG/audio/{script_id}.mp3`

**临时解决方案**：
1. 手动生成音频文件（使用本地TTS工具）
2. 将MP3文件放入 `podcast-output/audio/` 目录
3. 确保文件名与script_id匹配
4. 重新运行部署脚本

**后续计划**：
- 集成Azure TTS或阿里云TTS服务
- 自动生成高质量音频文件

### GitHub Pages国内访问

- ✅ **可以访问**，但速度较慢（2-5秒加载）
- ✅ 对于播客RSS这种低频访问场景，完全够用
- ⚠️ 偶尔可能出现访问失败（取决于网络环境）
- 💡 如果遇到访问问题，可以考虑使用国内CDN加速

### 更新频率

- GitHub Pages有速率限制：**每小时最多触发10次部署**
- 建议：批量生成文案后一次性部署，不要频繁推送

---

## 🔧 故障排查

### 1. GitHub Pages未生效

**检查清单**：
- [ ] 是否已在Settings中启用Pages？
- [ ] 工作流是否成功运行？（查看Actions标签页）
- [ ] `podcast-output/` 目录是否存在且包含文件？

**解决方法**：
```bash
# 检查工作流状态
git log --oneline -5

# 手动触发部署
gh workflow run deploy-podcast.yml
```

### 2. RSS文件无法访问

**可能原因**：
- 文件路径错误
- GitHub Pages尚未部署完成
- 浏览器缓存

**解决方法**：
```bash
# 验证文件存在
ls podcast-output/feed.xml

# 清除浏览器缓存或使用无痕模式访问
```

### 3. 音频文件404

**原因**：音频文件尚未生成或上传

**解决方法**：
- 暂时使用占位符文件测试
- 等待TTS功能实现
- 或手动上传MP3文件到 `podcast-output/audio/`

---

## 📊 工作流程图

```
生成播客文案
    ↓
运行部署脚本 (python scripts/deploy_podcast.py)
    ↓
自动生成: 
  - podcast-output/feed.xml (RSS Feed)
  - podcast-output/audio/*.mp3 (音频文件)
    ↓
Git提交并推送
    ↓
GitHub Actions自动部署
    ↓
GitHub Pages公开访问
    ↓
提交RSS URL到小宇宙等平台
    ↓
审核通过后自动同步更新
```

---

## 💡 最佳实践

1. **批量处理**：积累多个文案后一次性部署
2. **测试先行**：先在本地验证RSS格式正确性
3. **备份数据**：定期备份 `podcast-output/` 目录
4. **监控访问**：使用Google Analytics等工具跟踪RSS访问量
5. **及时更新**：文案修改后记得重新部署

---

## 🆘 需要帮助？

如有问题，请：
1. 检查GitHub Actions日志
2. 验证RSS格式：[W3C Feed Validation Service](https://validator.w3.org/feed/)
3. 查阅项目Issue或创建新问题
