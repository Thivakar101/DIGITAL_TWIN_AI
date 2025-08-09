from __future__ import annotations
from typing import Dict, List, Tuple
from datetime import datetime

from models import Persona, MemoryItem
from memory_bank import MemoryBank
from gemini_client import GeminiClient


def _top_values(values: Dict[str, int], n: int = 2) -> List[str]:
    return [k for k, _ in sorted(values.items(), key=lambda x: x[1], reverse=True)[:n]]


def _derive_mbti(answers: Dict[str, object]) -> str:
    # Each axis uses 1..5 Likert where higher biases toward the second letter
    # E/I: sociability
    ei = int(answers.get("mbti_ei", 3))  # 1=I, 5=E
    sn = int(answers.get("mbti_sn", 3))  # 1=S, 5=N
    tf = int(answers.get("mbti_tf", 3))  # 1=T, 5=F
    jp = int(answers.get("mbti_jp", 3))  # 1=J, 5=P
    e = "E" if ei >= 4 else ("I" if ei <= 2 else "X")
    n = "N" if sn >= 4 else ("S" if sn <= 2 else "X")
    f = "F" if tf >= 4 else ("T" if tf <= 2 else "X")
    p = "P" if jp >= 4 else ("J" if jp <= 2 else "X")
    return f"{e}{n}{f}{p}"


def _top_values_sentence(vals: List[str]) -> str:
    if not vals:
        return "pragmatism"
    if len(vals) == 1:
        return vals[0]
    return ", ".join(vals[:-1]) + f" and {vals[-1]}"


def _derive_persona_fields(answers: Dict[str, object]) -> Dict[str, str]:
    def geti(key: str, default: int = 3) -> int:
        v = answers.get(key)
        try:
            return int(v)
        except Exception:
            return default

    directness = geti("tone_directness")
    formality = geti("tone_formality")
    empathy = geti("tone_empathy")
    msg_len = geti("msg_length")
    humor_style = str(answers.get("humor_style", "light")).strip() or "light"
    humor_freq = geti("humor_frequency")

    data_vs_intuition = geti("decision_data_vs_intuition")
    risk = geti("risk_tolerance")
    speed = geti("speed_vs_thoroughness")

    agree = geti("agreeableness")
    consc = geti("conscientiousness")
    open_ = geti("openness")
    extra = geti("extraversion")

    values_map = {
        "honesty": geti("val_honesty"),
        "efficiency": geti("val_efficiency"),
        "loyalty": geti("val_loyalty"),
        "creativity": geti("val_creativity"),
        "frugality": geti("val_frugality"),
    }
    top_vals = _top_values(values_map, 3)

    tone_bits: List[str] = []
    tone_bits.append("direct" if directness >= 4 else ("diplomatic" if directness <= 2 else "balanced"))
    tone_bits.append("formal" if formality >= 4 else ("casual" if formality <= 2 else "semi-formal"))
    if empathy >= 4:
        tone_bits.append("empathetic")
    if msg_len >= 4:
        tone_bits.append("detailed")
    elif msg_len <= 2:
        tone_bits.append("concise")
    tone_style = ", ".join(dict.fromkeys(tone_bits))

    humor_phrase = f"{humor_style}"
    if humor_freq >= 4:
        humor_phrase = f"often {humor_style}"
    elif humor_freq <= 2:
        humor_phrase = f"rarely {humor_style}"

    if data_vs_intuition >= 4 and risk <= 2:
        decision_style = "data-first, risk-averse"
    elif data_vs_intuition >= 4 and risk >= 4:
        decision_style = "data-first, calculated risk-taker"
    elif data_vs_intuition <= 2 and risk >= 4:
        decision_style = "intuition-led, comfortable with risk"
    elif data_vs_intuition <= 2 and risk <= 2:
        decision_style = "intuition-led, cautious"
    else:
        decision_style = "balances data and intuition"

    if speed >= 4:
        decision_style += ", prefers speed"
    elif speed <= 2:
        decision_style += ", prefers thoroughness"

    persona_summary = (
        f"Tone is {tone_style}. Values center on {_top_values_sentence(top_vals)}. "
        f"Humor is {humor_phrase}. Decision-making is {decision_style}. "
        f"Traits: agreeableness {agree}/5, conscientiousness {consc}/5, openness {open_}/5, extraversion {extra}/5."
    )

    return {
        "tone": tone_style,
        "values": ", ".join(top_vals),
        "humor": humor_phrase,
        "decision_style": decision_style,
        "persona_summary": persona_summary,
        "mbti": _derive_mbti(answers),
    }


class DigitalAITwin:
    def __init__(self, user_name: str = "You"):
        self.persona = Persona(user_name=user_name)
        self.memories = MemoryBank()
        self.gemini = GeminiClient()

    def set_gemini_key(self, key: str) -> None:
        self.gemini.set_api_key(key)

    # --- Survey & Persona ---
    def process_survey(self, answers: Dict[str, object]) -> None:
        self.persona.survey_json = dict(answers)
        derived = _derive_persona_fields(answers)
        self.persona.persona_summary = derived["persona_summary"]
        self.persona.tone_style = derived["tone"]
        self.persona.values = derived["values"]
        self.persona.humor = derived["humor"]
        self.persona.decision_style = derived["decision_style"]
        self.persona.mbti = derived.get("mbti", "")

        catchphrase = str(answers.get("catchphrase", "")).strip()
        if catchphrase:
            emb = self.gemini.embed([catchphrase])[0]
            self.memories.add(MemoryItem(type="survey", text=f"Catchphrase: {catchphrase}", embedding=emb))

        for key in ("example_decision1", "example_decision2", "example_decision3"):
            txt = str(answers.get(key, "")).strip()
            if txt:
                emb = self.gemini.embed([txt])[0]
                self.memories.add(MemoryItem(type="decision", text=txt, embedding=emb))

        text_summary = (
            f"Tone: {self.persona.tone_style}. Values: {self.persona.values}. "
            f"Decision Style: {self.persona.decision_style}. Humor: {self.persona.humor}. MBTI: {self.persona.mbti}."
        )
        emb = self.gemini.embed([text_summary])[0]
        self.memories.add(MemoryItem(type="survey", text=text_summary, embedding=emb))

    def _catchphrases(self) -> List[str]:
        phrases: List[str] = []
        for m in self.memories.list():
            if m.type == "survey" and m.text.lower().startswith("catchphrase:"):
                phrases.append(m.text.split(":", 1)[-1].strip())
        return phrases

    # --- Retrieval Augmented Chat ---
    def chat(self, message: str, k: int = 5) -> str:
        q_emb = self.gemini.embed([message])[0]
        # tag user role for later filtering
        self.memories.add(MemoryItem(type="chat", text=message, embedding=q_emb, meta={"role": "user"}))

        context_items = self.memories.search(q_emb, top_k=k)
        context_lines = [f"- {m.type.upper()}: {m.text}" for m in context_items]
        catchphrases = self._catchphrases()
        style_rules = (
            f"Respond in first person as {self.persona.user_name}. Keep the tone {self.persona.tone_style}. "
            "Be concise (1–3 sentences) unless detail was requested. Avoid asking questions unless critical. "
            "Prefer decisive language."
        )
        if catchphrases:
            style_rules += f" Optionally weave in these catchphrase(s) naturally: {', '.join(catchphrases[:2])}."

        system_prompt = (
            f"You are the AI twin of {self.persona.user_name}.\n"
            f"Persona: {self.persona.persona_summary}\n"
            f"Core Values: {self.persona.values}\n"
            f"Humor: {self.persona.humor}\n"
            f"Relevant Memories:\n" + "\n".join(context_lines[:5]) + "\n\n" +
            "Output style rules:\n" + style_rules
        )
        reply = self.gemini.chat(system_prompt, message)
        a_emb = self.gemini.embed([reply])[0]
        self.memories.add(MemoryItem(type="chat", text=reply, embedding=a_emb, meta={"role": "assistant"}))
        return reply

    # --- What Would I Do ---
    def simulate_decision(self, situation: str, k: int = 5, store: bool = True) -> str:
        q_emb = self.gemini.embed([situation])[0]
        # Relevant past decisions
        relevant_decisions = self.memories.search(q_emb, top_k=k, type_filter="decision")
        # Survey context
        survey_ctx = self.memories.search(q_emb, top_k=2, type_filter="survey")
        # Relevant user chat preferences (exclude assistant replies)
        relevant_chats = self.memories.search(q_emb, top_k=max(5, k), type_filter="chat")
        user_prefs = [m for m in relevant_chats if (m.meta.get("role") != "assistant")]

        context_lines_decisions = [f"- {m.text}" for m in relevant_decisions]
        context_lines_survey = [f"- {m.text}" for m in survey_ctx]
        context_lines_prefs = [f"- {m.text}" for m in user_prefs[:5]]

        catchphrases = self._catchphrases()
        style_rules = (
            f"Respond in first person as {self.persona.user_name}. State the decision clearly in the first sentence, "
            "then give 1–2 sentences of reasoning. No follow-up questions. Honor stated preferences if applicable."
        )
        if catchphrases:
            style_rules += f" Optionally include catchphrase(s) tastefully: {', '.join(catchphrases[:2])}."

        system_prompt = (
            f"You are the AI twin of {self.persona.user_name}.\n"
            f"Persona Summary: {self.persona.persona_summary}\n"
            f"Decision-Making Style: {self.persona.decision_style}\n"
            + ("Relevant Past Decisions:\n" + "\n".join(context_lines_decisions[:5]) + "\n" if context_lines_decisions else "")
            + ("Survey Context:\n" + "\n".join(context_lines_survey[:3]) + "\n" if context_lines_survey else "")
            + ("Past Preferences from Chats (user statements):\n" + "\n".join(context_lines_prefs) + "\n" if context_lines_prefs else "")
            + "Output style rules:\n" + style_rules
        )
        reply = self.gemini.chat(system_prompt, situation)

        if store:
            emb = self.gemini.embed([reply])[0]
            self.memories.add(MemoryItem(type="decision", text=reply, embedding=emb))
        return reply
