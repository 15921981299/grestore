# GRE 读故事记单词

基于 **胡敏《读故事记单词 · 新 GRE 核心词汇》** 的 Astro 静态站点：200 篇故事目录、MP3 跟读、中英对照与难词注释。

## 功能

- **首页** `/`：200 课故事目录
- **课程页** `/lessons/[slug]/`：MP3 播放器、英文故事、中文译文、难词注释

## 快速开始

```bash
npm install
npm run dev
```

## 数据与素材

| 内容 | 路径 | 导入命令 |
|------|------|----------|
| 课表目录 | `src/data/gre/lessons.json` | `npm run gre:build-data` |
| 课文与词表 | `src/data/gre/content/*.json` | `npm run import:gre-content` |
| MP3 音频 | `public/audio/*.mp3` | `npm run download:gre-audio -- --source-dir "MP3文件夹"` |

课文从桌面上的 `*GRE*.html` 导出文件导入；音频优先使用本地 `public/audio/`。

## 部署

```bash
npm run build
```

输出目录为 `dist/`。

## 免责声明

本站为个人 GRE 学习工具，内容版权归原书及权利人所有。请支持正版图书。
