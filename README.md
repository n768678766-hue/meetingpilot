# MeetingPilot

MeetingPilot 是一个轻量级的会后文本结构化工具（post-transcription meeting text structuring tool），不是音频转录产品。

它接收已有的会议转写文本，自动生成结构化纪要、决策事项、待办任务、风险点、不确定项，并支持导出 Markdown / CSV。

## MVP Goals
- Paste meeting transcript text or upload transcript files (.txt, .md, .srt, .vtt).
- Generate structured meeting notes.
- Extract action items with task, owner, due date, and priority.
- Flag unclear or missing information.
- Export Markdown and CSV.
- Record bad cases for prompt and workflow improvement.
- Transcript length feedback with rough token estimates and cost/latency hints.

## Recommended Stack
- Python 3.11+
- Streamlit
- OpenAI-compatible API client
- Pydantic for structured output validation
- Pandas for CSV export
- Local JSON/CSV storage

## Project Layout

```text
meetingpilot/
  src/meetingpilot/
    app.py
    config.py
    exporters.py
    llm_client.py
    models.py
    prompts.py
    storage.py
  docs/
  samples/
  scripts/
  data/
  temp/
```

## Quick Start

```powershell
cd meetingpilot
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
streamlit run src\meetingpilot\app.py
```

Copy `.env.example` to `.env` and set your API credentials before calling a real model.

MeetingPilot 没有 API Key 也能演示。如果 `OPENAI_API_KEY` 为空，应用会使用本地演示模式，你仍然可以载入示例、生成结构化结果、测试导出和记录 Bad Case。

## DeepSeek 配置

在项目根目录创建 `.env`，然后把你的 DeepSeek API Key 填到第一行：

```text
OPENAI_API_KEY=<your-deepseek-api-key>
OPENAI_BASE_URL=https://api.deepseek.com
OPENAI_MODEL=deepseek-v4-pro
```

如果你的服务商后台显示的模型 ID 不是 `deepseek-v4-pro`，请把 `OPENAI_MODEL` 改成后台实际提供的模型 ID。

## Demo Workflow

1. Start the Streamlit app.
2. Click `Load Sample` or paste a transcript.
3. Click `Extract Notes`.
4. Review summary, decisions, action items, risks, uncertainty flags, and follow-up questions.
5. Download Markdown or CSV.
6. Record any wrong or missing output in the Bad Case form.

## Local Data

- Meeting result JSON files are saved under `data/meetings/`.
- Bad cases are appended to `data/bad_cases.jsonl`.
- Generated data stays local and should not be committed.
