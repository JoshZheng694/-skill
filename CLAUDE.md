# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

中国经济史课程复习项目。将教材PDF（马工程《中国经济史》2019版，419页）OCR为Markdown，再结合复习指南提纲，用多代理并行提取整合为完整背诵资料。

## 核心文件位置

| 内容 | 路径 | 说明 |
|------|------|------|
| 教材OCR分块 | `原始文件/chunk_01.md` ~ `chunk_42.md` | 全书419页，每块~10页，EasyOCR识别 |
| 教材PDF分块 | `原始文件/chunk_*_p*-p*.pdf` | 原始PDF分块，OCR源文件 |
| 复习指南 | `.tmp/经济史复习指南.md` | 8大板块提纲+考点+页码，由同目录docx转换 |
| OCR脚本 | `原始文件/_run_3p.py` | 3-worker并行OCR脚本，DPI 200 |
| OCR转换器 | `.claude/skills/pdf-to-markdown/scripts/convert_pdf.py` | 单文件PDF→MD，自动检测文字/扫描型 |

## 关键约定

- **MD命名规范**：分块用 `chunk_NN_pXXX-pYYY.md` 格式（如 `chunk_11_p101-p110.md`）
- **禁止重复OCR**：检测脚本按分块编号去重，同一编号已有MD则跳过
- **EasyOCR配置**：中文+英文模型，CPU模式，OMP_NUM_THREADS=2
- **子代理必须自己存文件**：子代理结果写到本地文件，不返回给主代理

## 多代理工作流

使用 `/do-agent` 技能进行多阶段并行处理：
1. 主代理写plan.md到 `agent_tasks/{task_name}_YYYYMMDDHH/`
2. 子代理并行执行，各自读写分配的文件
3. 子代理只返回状态摘要，完整结果存本地
4. 审阅阶段 → 修订阶段 → 最终交付

## 内存约束

- 总RAM 32GB，3个EasyOCR Worker约15GB
- 禁止超过3个OCR Worker同时运行
- RAM > 90% 必须杀进程，RAM > 95% 强制清空
- 新OCR任务前先 `powershell -Command "Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force"` 清残留

## 常用命令

```bash
# 检查OCR进度
python -c "
from pathlib import Path
mds = sorted(Path('原始文件').glob('chunk_*.md'))
done = set(m.stem.split('_')[1] for m in mds if len(m.stem.split('_'))>=2)
print(f'{len(done)}/42 done')
"

# 杀所有Python进程
powershell -Command "Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force"

# 转DOCX为MD
python -c "
from docx import Document
from pathlib import Path
doc = Document('文件.docx')
text = '\n'.join(p.text for p in doc.paragraphs)
Path('输出.md').write_text(text, encoding='utf-8')
"
```
