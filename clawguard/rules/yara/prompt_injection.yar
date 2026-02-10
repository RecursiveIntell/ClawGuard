rule ignore_previous_instructions {
    meta:
        author = "ClawGuard"
        description = "Prompt injection attempting to override system instructions"
        severity = "critical"
        category = "prompt_injection"
    strings:
        $ignore1 = "ignore previous instructions" nocase
        $ignore2 = "ignore all previous" nocase
        $ignore3 = "disregard previous" nocase
        $ignore4 = "forget your instructions" nocase
    condition:
        any of them
}

rule system_prompt_override {
    meta:
        author = "ClawGuard"
        description = "Attempting to override system prompt or assume new identity"
        severity = "critical"
        category = "prompt_injection"
    strings:
        $override1 = "system prompt override" nocase
        $override2 = "you are now" nocase
        $override3 = "new system prompt" nocase
        $override4 = "CORE DIRECTIVE" nocase
        $override5 = "SKILL_OVERRIDE" nocase
    condition:
        any of them
}

rule memory_file_targeting {
    meta:
        author = "ClawGuard"
        description = "Instructions targeting agent memory and personality files"
        severity = "critical"
        category = "prompt_injection"
    strings:
        $heartbeat = "HEARTBEAT.md" ascii
        $memory = "MEMORY.md" ascii
        $soul = "SOUL.md" ascii
    condition:
        any of them
}

rule stealth_instructions {
    meta:
        author = "ClawGuard"
        description = "Instructions to hide behavior from user"
        severity = "high"
        category = "prompt_injection"
    strings:
        $hide1 = "do not tell the user" nocase
        $hide2 = "do not mention" nocase
        $hide3 = "silently" nocase
        $hide4 = "without the user knowing" nocase
        $hide5 = "never report" nocase
    condition:
        any of them
}

rule hidden_html_instructions {
    meta:
        author = "ClawGuard"
        description = "Hidden instructions in HTML comments"
        severity = "high"
        category = "prompt_injection"
    strings:
        $open = "<!--" ascii
        $instruct = "INSTRUCTION" nocase
        $system = "SYSTEM" nocase
        $override = "OVERRIDE" nocase
        $execute = "EXECUTE" nocase
    condition:
        $open and any of ($instruct, $system, $override, $execute)
}
