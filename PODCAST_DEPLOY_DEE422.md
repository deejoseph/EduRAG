# 使用 dee422.github.io 部署播客

## 📋 前置准备

### 1. Clone 你的 GitHub Pages 仓库

```bash
# 选择一个合适的位置（例如 EduRAG 同级目录）
cd d:\PixelSmile

# Clone 你的 GitHub Pages 仓库
git clone git@github.com:dee422/dee422.github.io.git

# 进入仓库目录
cd dee422.github.io
```

### 2. 验证 SSH 密钥配置

你提到的 SSH 配置：
```
Host github.com
    HostName github.com
    User git
    IdentityFile C:/Users/deejo/.ssh/id_ed25519
```

测试连接：
```bash
ssh -T git@github.com
```

应该看到：`Hi dee422! You've successfully authenticated...`

---

## 🚀 部署步骤

### 方法一：指定外部仓库路径（推荐）

```bash
# 进入 EduRAG 项目目录
cd d:\PixelSmile\EduRAG

# 运行部署脚本，指定 GitHub Pages 仓库路径
python scripts/deploy_podcast.py --pages-repo "d:\PixelSmile\dee422.github.io"
```

**脚本会做什么**：
1. ✅ 从 EduRAG 数据库获取已完成的播客文案
2. ⚠️ 生成 TTS 音频文件（当前为占位符）
3. ✅ 在 `dee422.github.io` 目录生成 `feed.xml` 和 `audio/` 文件夹
4. ✅ 自动提交并推送到 `dee422.github.io` 仓库
5. ✅ GitHub Pages 自动部署（1-2分钟）

### 方法二：手动复制文件

如果你不想让脚本直接操作 GitHub Pages 仓库：

```bash
# 1. 在 EduRAG 中生成文件（不推送）
cd d:\PixelSmile\EduRAG
python scripts/deploy_podcast.py --skip-audio

# 2. 手动复制生成的文件
# 将 podcast-output/feed.xml 复制到 dee422.github.io/
# 将 podcast-output/audio/*.mp3 复制到 dee422.github.io/audio/

# 3. 在 dee422.github.io 仓库中提交
cd d:\PixelSmile\dee422.github.io
git add .
git commit -m "chore: 更新播客文件"
git push origin main
```

---

## 📡 访问地址

部署完成后，你的播客资源将通过以下地址访问：

- **RSS Feed**: `https://dee422.github.io/feed.xml`
- **音频目录**: `https://dee422.github.io/audio/`
- **单个音频**: `https://dee422.github.io/audio/{script_id}.mp3`

---

## 🎙️ 提交到小宇宙

1. 等待 1-2 分钟让 GitHub Pages 部署完成
2. 访问 `https://dee422.github.io/feed.xml` 验证 RSS 是否正确
3. 打开小宇宙 APP → 我 → 创作者中心 → 添加播客
4. 输入 RSS URL: `https://dee422.github.io/feed.xml`
5. 填写播客信息并提交审核
6. 等待审核通过（1-3 个工作日）

---

## ⚠️ 注意事项

### 1. 仓库路径

确保 `--pages-repo` 参数指向正确的路径：
```bash
# Windows 示例
python scripts/deploy_podcast.py --pages-repo "d:\PixelSmile\dee422.github.io"

# Linux/Mac 示例
python scripts/deploy_podcast.py --pages-repo "/home/user/dee422.github.io"
```

### 2. 音频文件问题

**当前状态**：
- 🚧 TTS 音频生成功能尚未实现
- RSS 中的音频 URL 是占位符：`https://dee422.github.io/audio/{script_id}.mp3`

**临时解决方案**：
- 手动生成 MP3 文件并放入 `dee422.github.io/audio/` 目录
- 确保文件名与 script_id 匹配

### 3. Git 冲突

如果 `dee422.github.io` 仓库中有其他内容，可能会产生冲突。建议：
- 保持该仓库专门用于播客托管
- 或者在推送前手动检查冲突

---

## 🔧 故障排查

### 1. 找不到 GitHub Pages 仓库

**错误信息**：`GitHub Pages仓库路径不存在`

**解决方法**：
```bash
# 确认仓库已 clone
ls d:\PixelSmile\dee422.github.io

# 如果不存在，重新 clone
cd d:\PixelSmile
git clone git@github.com:dee422/dee422.github.io.git
```

### 2. Git 推送失败

**可能原因**：
- SSH 密钥未配置
- 仓库权限问题
- 网络问题

**解决方法**：
```bash
# 测试 SSH 连接
ssh -T git@github.com

# 检查远程仓库
cd d:\PixelSmile\dee422.github.io
git remote -v

# 手动推送测试
git push origin main
```

### 3. GitHub Pages 未生效

**检查清单**：
- [ ] 仓库 Settings → Pages 是否启用？
- [ ] Source 是否设置为 `main` branch？
- [ ] 文件是否正确推送？

**验证方法**：
```bash
# 检查文件是否存在于仓库根目录
ls d:\PixelSmile\dee422.github.io/feed.xml
ls d:\PixelSmile\dee422.github.io/audio/
```

---

## 💡 最佳实践

### 1. 批量处理

积累多个播客文案后一次性部署，减少推送频率：
```bash
python scripts/deploy_podcast.py --pages-repo "d:\PixelSmile\dee422.github.io" --limit 20
```

### 2. 跳过音频生成

如果音频文件已手动准备好，可以跳过 TTS 生成：
```bash
python scripts/deploy_podcast.py --pages-repo "d:\PixelSmile\dee422.github.io" --skip-audio
```

### 3. 定期备份

定期备份 `dee422.github.io` 仓库：
```bash
cd d:\PixelSmile\dee422.github.io
git pull origin main
```

---

## 📊 工作流程图

```
EduRAG 数据库（播客文案）
    ↓
运行部署脚本（指定 --pages-repo）
    ↓
生成文件到 dee422.github.io/
  - feed.xml (RSS Feed)
  - audio/*.mp3 (音频文件)
    ↓
Git 提交并推送到 dee422.github.io 仓库
    ↓
GitHub Actions 自动部署到 Pages
    ↓
公开访问：https://dee422.github.io/feed.xml
    ↓
提交到小宇宙等平台
```

---

## 🆘 需要帮助？

如有问题，请：
1. 检查 Git 推送日志
2. 验证 GitHub Pages 设置
3. 查阅 EduRAG 项目 Issue
