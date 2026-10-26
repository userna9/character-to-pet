# 设定记录与交付

## 设定字段

保存为当前 run 的 `request-brief.md` 或 JSON，格式按任务需要选择：

- 用户原始描述、目标平台与当前阶段（仅检索/仅材料/制作包/创建/创建并启用）。
- 角色名、稳定 ASCII 文件夹标识、画风、正常比例或 Q 版、服装、配色。
- 身份特征及不可变项：脸、头发、眼睛、角/翼/尾、附肢连接、饰物与开衩侧别。
- 来源清单：作品页、作者与追溯证据、所选文件、哪些是观察、哪些是建议。
- 用户已确认的决定与启用意向；未决定的保持未定，不填虚构许可。
- 工具能力、Library 保存能力、产物位置与真实制作进度。

不要把白龙娘的白发紫瞳、礼服、170 像素身高或某次角色的动作习惯设为所有角色的默认值。

## 脚本定位

下文 `SKILL_DIR` 是本技能目录，`PET_SCRIPTS` 是本次解析到的当前 create-pet/scripts，`RUN_DIR` 是制作目录，`OUT_DIR` 是成品目录。使用会话提供的 Python/Pillow/ffmpeg 或已核实的 PATH，不复制另一台机器的绝对路径。

### 合并参考

```text
python SKILL_DIR/scripts/reference_panel.py --output RUN_DIR/references/identity-panel.png --image canonical.png --label canonical --image original.png --label original --image contact.png --label standard-contact
```

保持原图比例并加中性底色/角色标签。布局引导单独附加，提示词明确面板用途；输出 manifest 记录真实输入，不绘制新角色。

### 跨行动作登记（仅在观察到跳变时）

```text
python SKILL_DIR/scripts/register_rows.py --frames-root RUN_DIR/frames --output-root RUN_DIR/registered-frames --json-out RUN_DIR/qa/registration.json
```

输入是官方完整姿势提取器输出。自动基于 idle 与 jumping 真实包围盒选择共同站立高度，保留跳跃位移，对整行使用同一变换，输出独立目录。可设置 `--body-height` 与 `--baseline`，值须来自实际几何/视觉检查，不照抄上次角色。处理后重跑官方 inspect_frames、compose_atlas 及最终门禁。脚本不判断动作或方向含义。

### 最终文件预览

```text
python SKILL_DIR/scripts/deliver_pet.py render --atlas OUT_DIR/spritesheet.png --output-dir OUT_DIR/previews --pet-scripts PET_SCRIPTS --ffmpeg FFMPEG
```

只裁出最终图集既有像素，输出九类 GIF、全状态 GIF/MP4、idle-jump-idle、16 向 look-loop、标签静帧与 preview manifest。总览使用中性背景。辅助脚本当前支持 v2；契约变更时使用更新后的官方工具，不强行解释其他布局。

### 打包

```text
python SKILL_DIR/scripts/deliver_pet.py package --atlas OUT_DIR/spritesheet.png --run-dir RUN_DIR --deliverables OUT_DIR --atlas-report RUN_DIR/final/validation-extended.json --quality-report RUN_DIR/qa/pet-quality.json --mcp-report RUN_DIR/qa/mcp-preflight.json --output OUT_DIR/character-pet-materials.zip
```

`mcp-preflight.json` 保存真实 validate_pet_spritesheet structuredContent，允许增加 `validated_sha256` 为调用时真实哈希。打包检查 ok/valid、报告哈希、MCP 尺寸/字节数及可用的绑定哈希，不生成质量结论或创建宠物。

用户只要本地包或创建工具不可用时，增加 `--local-only`，包中明确记录 local-only；不要求 MCP 响应，但结构/官方质量报告仍必需，不能声称已创建。

素材包只收已选源图、身份参考、提示词、brief、选定 QA/成品与稳定元数据，不递归收集未知日志、上传会话或临时凭据。`pet-info.json` 可含 `id/name/description/is_custom/is_active/active_pet_id/sprite_version/sha256/generation_mode`；打包去除其他字段，本地记录不能替代真实工具核验。

## 说明启动

已创建、已选为 active、浮层可见是三个状态。常见桌面入口为 Settings > Pets、Show pet、`/pet` 和显示快捷键，但指导时以当前官方文档/UI 为准，不把桌面命令给网页用户。

- 技能结构与调用：https://learn.chatgpt.com/docs/build-skills
- 宠物产品说明：https://learn.chatgpt.com/docs/pets

网页说明的格式可能落后于 Pets 插件；以当前真实工具 schema、制作合同与实际验证决定制作/传输，不摘一个旧尺寸后降低门禁。
