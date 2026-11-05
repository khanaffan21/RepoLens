from ..config import settings
def generate(system,question,context,history=None):
    if not settings.openai_api_key:
        return "LLM is not configured. Retrieved grounding context:\\n\\n"+context[:7000]
    from openai import OpenAI
    client=OpenAI(api_key=settings.openai_api_key)
    msgs=[{"role":"system","content":system},{"role":"system","content":"Context:\\n"+context}]
    for x in (history or [])[-8:]:
        if x.get("role") in ("user","assistant"): msgs.append({"role":x["role"],"content":x.get("content","")[:3000]})
    msgs.append({"role":"user","content":question})
    res=client.chat.completions.create(model=settings.openai_model,messages=msgs,temperature=.2)
    return res.choices[0].message.content or "No answer."
