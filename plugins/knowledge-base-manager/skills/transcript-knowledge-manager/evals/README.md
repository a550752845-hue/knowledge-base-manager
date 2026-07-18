# Transcript Knowledge Manager 前向评测

本目录提供 `transcript-knowledge-manager` 的隔离前向评测资产。所有 fixture 均为完全合成数据，不含真实人物、客户、联系方式、凭据或隐私记录。标为 private/restricted 的字符串是专门用于边界检测的假哨兵，不是真实敏感信息。

## 格式

`evals.json` 采用常见的插件评测结构 `skill_name + evals[]`。每个案例包含：

- `id`：稳定的案例标识；
- `prompt`：发送给全新 agent run 的用户消息；
- `expected_output`：稳定的行为标识，不是要求逐字匹配的标准答案；
- `assertions`：可逐条独立检查的通过条件；
- `files`：相对于本 `evals/` 目录的 fixture 路径。

断言评估的是行为与最终产物，不要按生成文本与某份参考答案的措辞相似度评分。

## 隔离前向测试流程

1. 从 `evals.json` 选择一个案例。
2. 在仓库外新建临时工作区，只复制该案例 `files` 中列出的文件，并保持相对目录结构。禁止直接在本目录的规范 fixture 上运行维护或迁移操作。
3. 新建一个已安装本插件的任务；上下文中不得包含其他案例的对话、生成文件、缓存、记忆注入或评分说明。
4. 关闭外部连接器和网络访问。所有案例都不需要真实账号、浏览器或 fixture 之外的数据。
5. 只提供当前案例列出的文件，并原样发送 `prompt`。不要向被测 agent 暴露 `expected_output` 或 `assertions`。
6. 保存最终回复、命令记录、创建/修改文件清单，以及所有输入文件的前后哈希。
7. 对每条 assertion 分别评为 `pass`、`fail` 或 `not-observable`，并附上回复原文、命令记录、路径、元数据字段或哈希等具体证据。
8. 任一 assertion 为 `fail`，整个案例即失败。`not-observable` 不算通过；必要时启用完整产物捕获后重新运行。
9. 运行下一案例前删除临时工作区。每次都使用全新任务和重新复制的 fixture。

案例 003 和 010 必须在读取资产前完成受限根排除；禁止哨兵一旦出现在回复或生成的 public/internal 产物中，即自动失败。案例 008 和 009 必须比较输入文件的前后哈希，agent 仅声称“原件未变”不能作为证据。

## 重复性

每个案例至少在两个独立临时工作区运行两次。固定模型、插件修订版本、工具权限和评分规则，只随机化临时绝对路径。结果应按 assertion 汇报，并区分确定性文件检查与语义评审。

建议每次运行保存以下证据包：

```text
run.json                 # case id, model, plugin revision, start/end time
response.md              # final agent response
commands.log             # tool and command transcript
files-before.sha256      # supplied fixture hashes
files-after.sha256       # supplied fixture hashes after the run
workspace-tree.txt       # final temporary workspace tree
grade.json               # one result and evidence item per assertion
```

## 资产校验

在 skill 目录执行以下命令校验 JSON 语法：

```powershell
rtk proxy python -X utf8 -m json.tool evals/evals.json
```

随后检查每个已声明 fixture 都存在，并确认运行中没有注入当前案例未列出的 fixture。`evals/` 下的规范资产仅是测试输入；评测输出应留在可销毁的临时工作区，不得写回本目录。
