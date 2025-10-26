# 如何使用 Spec-Kit 指导 AI 开发

本文档是一个快速入门指南，用于说明如何使用 `spec-kit` 工具包，通过指导 AI 代理（如 Gemini）来进行高效、规范的软件开发。

## 核心理念

`spec-kit` 的核心是**规范驱动开发 (Spec-Driven Development)**。在这种模式下，您的角色是“导演”或“架构师”，负责提供高层级的意图、原则和决策。AI 代理的角色是“执行者”，负责具体的编码实现。

---

## 第一步：全局安装 `specify-cli` (一次性操作)

在您开始使用 `spec-kit` 之前，需要先将它的命令行工具 `specify-cli` 安装到您的电脑上。这个步骤只需要执行一次。

1.  **确保已安装 `uv`**:
    ```bash
    pip install uv
    ```

2.  **使用 `uv` 安装 `specify-cli`**:
    ```bash
    uv tool install specify-cli --from git+https://github.com/github/spec-kit.git
    ```
    安装成功后，您就可以在系统的任何路径下使用 `specify` 命令了。

---

## 第二步：在您的项目中初始化 `spec-kit`

对于每一个您想使用 `spec-kit` 进行开发的项目，都需要在项目内部进行初始化。

### 场景 A：应用于一个已有的项目

这是最常见的场景。您可以将 `spec-kit` 的能力集成到任何现有的代码库中。

1.  **进入项目根目录**:
    ```bash
    cd /path/to/your/existing-project
    ```

2.  **在当前目录初始化**:
    ```bash
    # 使用 . 来指定当前目录
    specify init . --ai gemini
    ```
    这个命令不会删除您的代码，只会在项目根目录下创建一个 `.specify` 文件夹，用于存放工作流的配置和产物。

### 场景 B：从零开始一个新项目

1.  **创建并进入新项目目录**:
    ```bash
    # <project-name> 替换为您的项目名
    specify init <project-name> --ai gemini
    cd <project-name>
    ```
    这个命令会帮您创建一个新的文件夹，并自动在里面完成初始化。

---

## 第三步：核心开发流程 (与 AI 交互)

完成初始化后，您就可以在项目根目录启动 AI 代理（例如 Gemini CLI），并通过以下一系列 `/speckit.*` 命令来指导开发。

### 1. `/speckit.constitution` - 设定项目“宪法”

告诉 AI 项目必须遵守的最高原则。

**示例**:
```
/speckit.constitution 创建一套以后端性能和代码可读性为重心的开发原则。所有 API 都必须有单元测试，并且代码风格遵循 PEP8。
```

### 2. `/speckit.specify` - 描述功能“规范”

用自然语言描述您想构建的功能，**重点是“做什么”和“为什么”**，而不是技术细节。

**示例**:
```
/speckit.specify 我想开发一个在线相册应用。用户可以创建相册，上传照片到相册中。在首页，相册以网格形式展示。点击相册可以查看里面的所有照片。
```

### 3. `/speckit.plan` - 制定技术“计划”

明确告诉 AI 您希望使用的技术栈和架构。

**示例**:
```
/speckit.plan 这个应用使用 React 和 TypeScript 作为前端，使用 Node.js 和 Express 搭建后端 REST API，图片存储在本地文件系统。
```

### 4. `/speckit.tasks` - 生成“任务”列表

这是一个自动化步骤，AI 会根据前面的规范和计划，自动生成详细的、有序的开发任务清单。

**操作**:
```
/speckit.tasks
```

### 5. `/speckit.implement` - 开始“实现”

命令 AI 开始根据任务列表进行编码。

**操作**:
```
/speckit.implement
```
**注意**: 在此阶段，AI 可能会执行本地命令（如 `npm install`, `dotnet build` 等），请确保您的本地开发环境已准备就绪。

---
## 总结

您的工作是提供清晰的、高质量的指令。AI 的工作是忠实地、自动化地执行这些指令。通过这种协作，可以大大提升开发效率和项目质量。
