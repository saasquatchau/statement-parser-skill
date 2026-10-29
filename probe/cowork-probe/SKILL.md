---
name: cowork-probe
description: One-off environment check for the statement-parser design. Use only when the user asks to "run the cowork probe".
---

# Cowork probe

Checks whether Cowork can host the statement-parser skill. Do not read `scripts/probe.py`; just run it. The point of the test is that script source never enters context.

1. Ask the user which connected folder to use as the test Parser Library (ideally a Dropbox, OneDrive or Google Drive folder shared with a colleague). Find its path inside your shell.
2. Run, without reading the script first:

   ```
   python3 "${CLAUDE_SKILL_DIR}/scripts/probe.py" "<library folder path>"
   ```

   If `CLAUDE_SKILL_DIR` is empty, locate `scripts/probe.py` inside this skill's folder and run it by full path.
3. Paste the script's output back to the user exactly as printed, inside a code block. Add nothing except:
   - whether you were asked to approve the shell command(s), and
   - the folder path you used.
4. Tell the user to: check that `statement-parser-probe/` appeared in that folder on their own computer (and on a colleague's, if shared), then start a **new** Cowork task and run the probe again, so the `persisted_from_earlier_run` line shows whether files survive between tasks.
