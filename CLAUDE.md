# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

中国经济史课程复习项目。将教材PDF（马工程《中国经济史》2019版，419页）OCR为Markdown，再结合复习指南提纲，用多代理并行提取整合为完整背诵资料，经多轮审阅修订后交付。

## 核心文件位置

| 内容 | 路径 | 说明 |
|------|------|------|
| 教材OCR分块 | `原始文件/chunk_01_p1-p10.md` ~ `原始文件/chunk_42_p411-p419.md` | 全书419页，每块~10页，EasyOCR识别 |
| 教材PDF分块 | `原始文件/chunk_*_p*-p*.pdf` | 原始PDF分块，OCR源文件 |
| 复习指南 | `.tmp/经济史复习指南.md` | 8大板块提纲+考点+页码，由同目录docx转换 |
| OCR脚本 | `原始文件/_run_3p.py` | 3-worker并行OCR脚本，DPI 200 |
| 复习提纲（初版） | `agent_tasks/经济史复习提纲_2026062020/经济史完整复习提纲.md` | 第一版完整提纲（86300字） |
| 复习提纲（修订版） | `agent_tasks/经济史复习提纲审阅补充_2026062117/经济史完整复习提纲_修订版.md` | 经10审阅+2元审阅修订版（159903字） |

## Skills

| Skill | 用途 | 触发词 |
|-------|------|--------|
| `do-agent` | 多代理并行工作流（规划→执行→审阅→修订） | `/do-agent` |
| `pdf-to-markdown` | PDF→MD转换（自动检测文字/扫描型） | PDF转换相关 |
| `study-guide-generator` | 教材→复习提纲完整闭环（OCR提取→填补→审阅→修订→交付） | `/study-guide-generator`, 创建复习资料 |

## 多代理工作流 (do-agent)

四阶段全自动化流水线：
1. **规划阶段**：主代理探索材料→写plan.md到 `agent_tasks/{task}_YYYYMMDDHH/`
2. **实施阶段**：最多10个子代理并行，各自读写分配的文件，**结果只存本地不返回主代理**
3. **审阅阶段**：元审阅代理交叉检查全部输出，产出问题清单
4. **修订阶段**：教师代理整合所有审阅修正，产出最终文档

关键约束：
- 子代理必须自己将结果立即保存到本地文件，严禁将完整输出返回主代理
- 子代理只返回状态摘要（"审阅X个考点，修复Y处，补充Z处"）
- 相邻代理之间应有少量重叠，确保边界考点不遗漏

## study-guide-generator 完整闭环

此Skill编码了"教材OCR分块 + 复习指南模板 → 完整背诵资料"的端到端流水线：

```
教材PDF → OCR分块(MD) → [阶段1: 10代理提取填模板]
                              ↓
                         [阶段2: 10审阅代理验证]
                              ↓
                         [阶段3: 2元审阅交叉检查]
                              ↓
                         [阶段4: 1教师代理整合修订]
                              ↓
                         最终背诵资料（可直接打印）
```

详细工作流见 `.claude/skills/study-guide-generator/SKILL.md`

## 审阅质量标准

核心规则（编码到所有审阅代理提示词中）：
- **禁止省略号**：所有教材引文中的"……"/"..."必须替换为完整原文
- **页码统一**：统一使用教材印刷页码，消除PDF页码/推测页码偏移
- **课堂vs教材区分**：教材未涉及的内容标注 `> ⚠️ 课堂补充：`，不得伪装为教材原文
- **逐考点验证**：每条"教材原文"引用必须能在对应OCR分块中找到原文

## 关键约定

- **MD命名规范**：分块用 `chunk_NN_pXXX-pYYY.md` 格式（如 `chunk_11_p101-p110.md`）
- **禁止重复OCR**：检测脚本按分块编号去重，同一编号已有MD则跳过
- **EasyOCR配置**：中文+英文模型，CPU模式，OMP_NUM_THREADS=2
- **子代理必须自己存文件**：子代理结果写到本地文件，不返回给主代理
- **代理任务目录**：`agent_tasks/{short_description}_YYYYMMDDHH/`，若同名已存在则加后缀

## 内存约束

- 总RAM 32GB，3个EasyOCR Worker约15GB
- 禁止超过3个OCR Worker同时运行
- RAM > 90% 必须杀进程，RAM > 95% 强制清空
- 新OCR任务前先 `powershell -Command "Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force"` 清残留

## Git & GitHub

- **仓库**: https://github.com/JoshZheng694/-skill
- **默认分支**: master → main
- **提交规范**: 中文提交信息，结尾加 `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`

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

# 统计省略号残留（审阅阶段用）
grep -c '\.\.\.' agent_tasks/*/经济史完整复习提纲*.md

# Git推送
git add -A && git commit -m "描述" && git push origin master
```
