rule base64_decode_exec {
    meta:
        author = "ClawGuard"
        description = "Base64 decoding potentially followed by execution"
        severity = "high"
        category = "obfuscation"
    strings:
        $b64_python = "base64.b64decode" ascii
        $b64_js = "atob(" ascii
        $fromhex = "bytes.fromhex" ascii
    condition:
        any of them
}

rule long_encoded_string {
    meta:
        author = "ClawGuard"
        description = "Long base64-encoded string that may contain hidden payload"
        severity = "medium"
        category = "obfuscation"
    strings:
        $long_b64 = /[A-Za-z0-9+\/]{100,}={0,2}/
    condition:
        $long_b64
}

rule string_concat_obfuscation {
    meta:
        author = "ClawGuard"
        description = "String concatenation used to obfuscate URLs or commands"
        severity = "medium"
        category = "obfuscation"
    strings:
        $concat_http = /["']h["']\s*\+\s*["']t["']\s*\+\s*["']t["']\s*\+\s*["']p/
        $concat_eval = /["']e["']\s*\+\s*["']v["']\s*\+\s*["']a["']\s*\+\s*["']l/
    condition:
        any of them
}

rule unicode_escape_abuse {
    meta:
        author = "ClawGuard"
        description = "Excessive Unicode escape sequences suggesting obfuscation"
        severity = "medium"
        category = "obfuscation"
    strings:
        $unicode_esc = /\\u[0-9a-fA-F]{4}/
    condition:
        #unicode_esc > 10
}
