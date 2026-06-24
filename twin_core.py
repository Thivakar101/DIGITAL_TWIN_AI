from __future__ import annotations
from typing import Dict, List

from app_config import get_env_value, set_env_values
from local_model_client import LocalModelClient
from memory_bank import MemoryBank
from models import MemoryItem, Persona


def _top_values(values: Dict[str, int], n: int = 2) -> List[str]:
    return [k for k, _ in sorted(values.items(), key=lambda x: x[1], reverse=True)[:n]]


def _derive_mbti(answers: Dict[str, object]) -> str:
    ei = int(answers.get('mbti_ei', 3))
    sn = int(answers.get('mbti_sn', 3))
    tf = int(answers.get('mbti_tf', 3))
    jp = int(answers.get('mbti_jp', 3))
    e = 'E' if ei >= 4 else ('I' if ei <= 2 else 'X')
    n = 'N' if sn >= 4 else ('S' if sn <= 2 else 'X')
    f = 'F' if tf >= 4 else ('T' if tf <= 2 else 'X')
    p = 'P' if jp >= 4 else ('J' if jp <= 2 else 'X')
    return f'{e}{n}{f}{p}'


def _top_values_sentence(vals: List[str]) -> str:
    if not vals:
        return 'pragmatism'
    if len(vals) == 1:
        return vals[0]
    return ', '.join(vals[:-1]) + f' and {vals[-1]}'


def _derive_persona_fields(answers: Dict[str, object]) -> Dict[str, str]:
    def geti(key: str, default: int = 3) -> int:
        value = answers.get(key)
        try:
            return int(value)
        except Exception:
            return default

    directness = geti('tone_directness')
    formality = geti('tone_formality')
    empathy = geti('tone_empathy')
    msg_len = geti('msg_length')
    humor_style = str(answers.get('humor_style', 'light')).strip() or 'light'
    humor_freq = geti('humor_frequency')

    data_vs_intuition = geti('decision_data_vs_intuition')
    risk = geti('risk_tolerance')
    speed = geti('speed_vs_thoroughness')

    agree = geti('agreeableness')
    consc = geti('conscientiousness')
    open_ = geti('openness')
    extra = geti('extraversion')

    values_map = {
        'honesty': geti('val_honesty'),
        'efficiency': geti('val_efficiency'),
        'loyalty': geti('val_loyalty'),
        'creativity': geti('val_creativity'),
        'frugality': geti('val_frugality'),
    }
    top_vals = _top_values(values_map, 3)

    tone_bits: List[str] = []
    tone_bits.append('direct' if directness >= 4 else ('diplomatic' if directness <= 2 else 'balanced'))
    tone_bits.append('formal' if formality >= 4 else ('casual' if formality <= 2 else 'semi-formal'))
    if empathy >= 4:
        tone_bits.append('empathetic')
    if msg_len >= 4:
        tone_bits.append('detailed')
    elif msg_len <= 2:
        tone_bits.append('concise')
    tone_style = ', '.join(dict.fromkeys(tone_bits))

    humor_phrase = f'{humor_style}'
    if humor_freq >= 4:
        humor_phrase = f'often {humor_style}'
    elif humor_freq <= 2:
        humor_phrase = f'rarely {humor_style}'

    if data_vs_intuition >= 4 and risk <= 2:
        decision_style = 'data-first, risk-averse'
    elif data_vs_intuition >= 4 and risk >= 4:
        decision_style = 'data-first, calculated risk-taker'
    elif data_vs_intuition <= 2 and risk >= 4:
        decision_style = 'intuition-led, comfortable with risk'
    elif data_vs_intuition <= 2 and risk <= 2:
        decision_style = 'intuition-led, cautious'
    else:
        decision_style = 'balances data and intuition'

    if speed >= 4:
        decision_style += ', prefers speed'
    elif speed <= 2:
        decision_style += ', prefers thoroughness'

    persona_summary = (
        f'Tone is {tone_style}. Values center on {_top_values_sentence(top_vals)}. '
        f'Humor is {humor_phrase}. Decision-making is {decision_style}. '
        f'Traits: agreeableness {agree}/5, conscientiousness {consc}/5, openness {open_}/5, extraversion {extra}/5.'
    )

    return {
        'tone': tone_style,
        'values': ', '.join(top_vals),
        'humor': humor_phrase,
        'decision_style': decision_style,
        'persona_summary': persona_summary,
        'mbti': _derive_mbti(answers),
    }


class DigitalAITwin:
    def __init__(self, user_name: str = ''):
        resolved_name = (user_name or get_env_value('USER_NAME', 'You')).strip() or 'You'
        self.persona = Persona(user_name=resolved_name)
        self.memories = MemoryBank()
        self.model = LocalModelClient()

    def set_user_name(self, user_name: str, persist: bool = False) -> None:
        self.persona.user_name = (user_name or 'You').strip() or 'You'
        if persist:
            set_env_values({'USER_NAME': self.persona.user_name})

    def set_local_model(self, model_name: str, base_url: str, persist: bool = False) -> None:
        self.model.set_model(model_name)
        self.model.set_base_url(base_url)
        if persist:
            set_env_values({'OLLAMA_MODEL': self.model.model_name, 'OLLAMA_BASE_URL': self.model.base_url})

    def api_status(self) -> Dict[str, object]:
        return {
            'user_name': self.persona.user_name,
            'persona_summary': self.persona.persona_summary,
            'memory_count': len(self.memories.list()),
            **self.model.status(),
        }

    def process_survey(self, answers: Dict[str, object]) -> None:
        self.persona.survey_json = dict(answers)
        derived = _derive_persona_fields(answers)
        self.persona.persona_summary = derived['persona_summary']
        self.persona.tone_style = derived['tone']
        self.persona.values = derived['values']
        self.persona.humor = derived['humor']
        self.persona.decision_style = derived['decision_style']
        self.persona.mbti = derived.get('mbti', '')

        catchphrase = str(answers.get('catchphrase', '')).strip()
        if catchphrase:
            emb = self.model.embed([catchphrase])[0]
            self.memories.add(MemoryItem(type='survey', text=f'Catchphrase: {catchphrase}', embedding=emb))

        for key in ('example_decision1', 'example_decision2', 'example_decision3'):
            txt = str(answers.get(key, '')).strip()
            if txt:
                emb = self.model.embed([txt])[0]
                self.memories.add(MemoryItem(type='decision', text=txt, embedding=emb))

        text_summary = (
            f'Tone: {self.persona.tone_style}. Values: {self.persona.values}. '
            f'Decision Style: {self.persona.decision_style}. Humor: {self.persona.humor}. MBTI: {self.persona.mbti}.'
        )
        emb = self.model.embed([text_summary])[0]
        self.memories.add(MemoryItem(type='survey', text=text_summary, embedding=emb))

    def _catchphrases(self) -> List[str]:
        phrases: List[str] = []
        for memory in self.memories.list():
            if memory.type == 'survey' and memory.text.lower().startswith('catchphrase:'):
                phrases.append(memory.text.split(':', 1)[-1].strip())
        return phrases

    def chat(self, message: str, k: int = 5) -> str:
        q_emb = self.model.embed([message])[0]

        context_items = self.memories.search(q_emb, top_k=max(8, k * 2))
        grounded_context = []
        for memory in context_items:
            if memory.type == 'chat' and memory.meta.get('role') == 'assistant':
                continue
            grounded_context.append(memory)
            if len(grounded_context) >= k:
                break

        context_lines = [f'- {memory.type.upper()}: {memory.text}' for memory in grounded_context]
        catchphrases = self._catchphrases()
        style_rules = (
            f'You are a calm, attentive listener speaking with {self.persona.user_name}. Keep the tone {self.persona.tone_style}. '
            "Respond naturally in a warm, grounded way. Do not pretend to share the user's experiences. "
            "Do not say you remember something unless it appears explicitly in the relevant memory list below, and when it does, say 'You mentioned earlier...' instead of claiming a shared memory. "
            'Do not invent backstory, shared events, or emotions. Focus on acknowledging what the user just said and, at most, add one gentle reflective sentence. '
            'Keep replies concise, usually 1-3 sentences.'
        )
        if catchphrases:
            style_rules += f" If it fits naturally, you may lightly echo these catchphrase(s): {', '.join(catchphrases[:2])}."

        system_prompt = (
            f'You are the digital twin assistant for {self.persona.user_name}.\n'
            f'Persona: {self.persona.persona_summary}\n'
            f'Core Values: {self.persona.values}\n'
            f'Humor: {self.persona.humor}\n'
            + ('Relevant user-provided context:\n' + '\n'.join(context_lines[:5]) + '\n\n' if context_lines else '')
            + 'Output style rules:\n' + style_rules
        )

        self.memories.add(MemoryItem(type='chat', text=message, embedding=q_emb, meta={'role': 'user'}))
        reply = self.model.chat(system_prompt, message)
        a_emb = self.model.embed([reply])[0]
        self.memories.add(MemoryItem(type='chat', text=reply, embedding=a_emb, meta={'role': 'assistant'}))
        return reply

    def simulate_decision(self, situation: str, k: int = 5, store: bool = True) -> str:
        q_emb = self.model.embed([situation])[0]
        relevant_decisions = self.memories.search(q_emb, top_k=k, type_filter='decision')
        survey_ctx = self.memories.search(q_emb, top_k=2, type_filter='survey')
        relevant_chats = self.memories.search(q_emb, top_k=max(5, k), type_filter='chat')
        user_prefs = [memory for memory in relevant_chats if memory.meta.get('role') != 'assistant']

        context_lines_decisions = [f'- {memory.text}' for memory in relevant_decisions]
        context_lines_survey = [f'- {memory.text}' for memory in survey_ctx]
        context_lines_prefs = [f'- {memory.text}' for memory in user_prefs[:5]]

        catchphrases = self._catchphrases()
        style_rules = (
            f'Respond in first person as {self.persona.user_name}. State the decision clearly in the first sentence, '
            'then give 1-2 sentences of reasoning. No follow-up questions. Honor stated preferences if applicable.'
        )
        if catchphrases:
            style_rules += f" Optionally include catchphrase(s) tastefully: {', '.join(catchphrases[:2])}."

        system_prompt = (
            f'You are the AI twin of {self.persona.user_name}.\n'
            f'Persona Summary: {self.persona.persona_summary}\n'
            f'Decision-Making Style: {self.persona.decision_style}\n'
            + ('Relevant Past Decisions:\n' + '\n'.join(context_lines_decisions[:5]) + '\n' if context_lines_decisions else '')
            + ('Survey Context:\n' + '\n'.join(context_lines_survey[:3]) + '\n' if context_lines_survey else '')
            + ('Past Preferences from Chats (user statements):\n' + '\n'.join(context_lines_prefs) + '\n' if context_lines_prefs else '')
            + 'Output style rules:\n' + style_rules
        )
        reply = self.model.chat(system_prompt, situation)

        if store:
            emb = self.model.embed([reply])[0]
            self.memories.add(MemoryItem(type='decision', text=reply, embedding=emb))
        return reply
