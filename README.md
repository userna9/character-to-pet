# Character-to-Pet · 角色桌宠工坊
# 角色桌宠工坊 · Character-to-Pet

从一句人物描述开始，检索图片参考、协商形象、生成动画素材包，并在支持的 ChatGPT 环境中创建宠物。
**安装到 agent 中使用的 Skill。** 告诉 agent 你想要的人物形象，它会检索参考、与你确认设定、制作动画素材包，并通过宿主的 Pets 工具创建 ChatGPT 桌宠。

A reusable agent skill for turning character ideas into researched references, approved designs, validated animation assets, and ChatGPT pets.
An installable agent skill: describe a character, research references, approve the design, and let your agent make the pet.

## 安装到你的 agent

把**本仓库的 GitHub 链接**发给支持技能安装的 agent，再复制这段话：

> 请安装这个仓库里的「角色桌宠工坊」技能，技能目录是 `skills/character-to-pet`。如果有 `$skill-installer`，请使用它安装；检查本环境的检索、imagegen 和 Pets 能力，并告诉我如何调用。

安装完成后，直接对 agent 说：

> 用角色桌宠工坊，做一个正常比例的银发狐娘桌宠。先检索两三张参考，和我确认形象后再制作，做好后创建并启用。

支持 `$` 技能调用的环境也可以输入 `$character-to-pet`。技能选择方式随宿主而异，见 [官方技能说明](https://learn.chatgpt.com/docs/build-skills)。

如果喜欢下载文件，可以从仓库 **Releases** 下载 `character-to-pet.zip`，按宿主支持的技能导入方式安装。完整目录结构、ZIP 安装和更新方法见 [安装到 agent](docs/install-in-agent.md)。

日常使用在 agent 的对话中完成；安装位置、脚本调用与依赖检查由 agent 处理。

```mermaid

## 使用条件
## 适用环境

| 图像与动画制作 | 内置 imagegen、当前版本 `work-pets:create-pet` 及其制作/验证脚本 |
| 本地辅助处理 | Python 3.10+、Pillow；MP4 预览另需 FFmpeg |
| agent 执行辅助脚本 | 宿主可运行 Python 3.10+、Pillow；MP4 预览另需 FFmpeg |
| 创建与启用 | 当前账号可用的 Pets 工具与对应客户端功能 |

Pets 的可用性、显示方式和上传机制依赖宿主版本。官方制作技能、验证器与服务没有打包进本仓库；使用时由 agent 从当前环境定位。仅有本仓库时仍可阅读流程、运行本地辅助脚本和测试。

## 安装

下载或克隆本仓库，在仓库根目录执行：

```bash
python tools/install_skill.py
```

默认安装到 `$CODEX_HOME/skills/character-to-pet`；未设置 `CODEX_HOME` 时使用 `~/.codex/skills/character-to-pet`。安装脚本只依赖 Python 标准库，不修改账号设置。

如果已有同名技能，脚本会停止。需要更新时可运行：

```bash
python tools/install_skill.py --replace
```

旧目录会保留为同级备份。也可以指定完整目标技能目录：

```bash
python tools/install_skill.py --dest ./local-skills/character-to-pet
```

宿主未显示新技能时，重新打开聊天或重启客户端。技能发现和调用方式见 [OpenAI 官方技能说明](https://learn.chatgpt.com/docs/build-skills)。

## 开始使用

在支持 `$skill-name` 调用的 agent 中输入：
