# LeadPilot

An AI agent that chats with an inbound sales lead, asks qualifying
questions (need, budget, timeline, decision authority), and hands off a
structured summary a sales rep can act on immediately.

## 1. Get your AMD Developer Cloud endpoint running

1. Go to AMD Developer Cloud and create a GPU Droplet using the
   **vLLM Quick Start** image, on the single **MI300X** plan.
2. Wait ~3 minutes for it to initialize.
3. Note the Droplet's IP address. Your OpenAI-compatible endpoint will be:
   `http://YOUR_DROPLET_IP:8000/v1`
4. Note the model name it deployed (shown in the vLLM startup logs, e.g.
   `meta-llama/Llama-3.1-8B-Instruct` or a Qwen model).

## 2. Configure LeadPilot

Set two environment variables before running (or just edit the defaults
at the top of `app.py`):

```bash
export LEADPILOT_BASE_URL="http://YOUR_DROPLET_IP:8000/v1"
export LEADPILOT_MODEL="meta-llama/Llama-3.1-8B-Instruct"
```

## 3. Install and run

```bash
pip install -r requirements.txt
streamlit run app.py
```

This opens LeadPilot in your browser. Chat with it as if you were a lead,
then click **Generate lead summary for sales rep** to see the structured
output (fit score, need/budget/timeline/authority, recommended action).

## Screenshot ideas for your lablab.ai submission

- **Mini Challenge 1 image**: a screenshot of an in-progress conversation,
  showing LeadPilot asking a natural qualifying question.
- **Mini Challenge 2 image**: a screenshot of the generated lead summary
  card (fit score + recommended action), after clicking the summary button.

## Notes

- Swap `SYSTEM_PROMPT` in `app.py` if you want to tune the questions or tone.
- The summary step asks the model to return strict JSON - if your model
  ignores that instruction sometimes, lower the temperature further or
  add a one-shot example to the prompt.
