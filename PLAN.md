# Implementation Plan

1. ✅ **callback_data safety** – duplicates were already addressed in the bot’s inline keyboards and dedup logic, so this is complete.

2. **Prompt tracking & persistence**
   - Ensure `applications` has the new `generated_prompt` and `prompt_source` fields (already added via the latest SQL schema).
   - Persist the active prompt text (either `user_settings.application_prompt` or the legacy default) to `applications.generated_prompt` whenever Telegram triggers generation.
   - Store `prompt_source = 'telegram'` for bot-generated records and continue documenting the allowed source indicators (`telegram`, `dashboard`, `manual`).
   - Revisit this plan after the Telegram function stores the prompt so we can confirm rollout to Supabase + GitHub.

3. **Next deliverables**
   - Add UI/automation to expose editable prompts in the Dashboard and propagate Dashboard-generated prompts with `prompt_source = 'dashboard'`.
   - Provide a manual edit flow that can mark records as `prompt_source = 'manual'` when users override the AI output.
