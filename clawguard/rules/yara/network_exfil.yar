rule paste_service_url {
    meta:
        author = "ClawGuard"
        description = "URLs pointing to paste services commonly used for exfiltration"
        severity = "medium"
        category = "network_exfiltration"
    strings:
        $pastebin = "pastebin.com" ascii
        $hastebin = "hastebin.com" ascii
        $glot = "glot.io" ascii
        $dpaste = "dpaste.org" ascii
    condition:
        any of them
}

rule url_shortener {
    meta:
        author = "ClawGuard"
        description = "URL shorteners that can obscure malicious destinations"
        severity = "medium"
        category = "network_exfiltration"
    strings:
        $bitly = "bit.ly" ascii
        $tinyurl = "tinyurl.com" ascii
        $tco = "t.co/" ascii
        $isgd = "is.gd/" ascii
    condition:
        any of them
}

rule discord_webhook {
    meta:
        author = "ClawGuard"
        description = "Discord webhook URL used for data exfiltration"
        severity = "high"
        category = "network_exfiltration"
    strings:
        $webhook = "discord.com/api/webhooks" ascii
        $webhook2 = "discordapp.com/api/webhooks" ascii
    condition:
        any of them
}

rule telegram_bot_api {
    meta:
        author = "ClawGuard"
        description = "Telegram Bot API URL used for data exfiltration"
        severity = "high"
        category = "network_exfiltration"
    strings:
        $telegram = "api.telegram.org/bot" ascii
    condition:
        $telegram
}

rule raw_ip_in_script {
    meta:
        author = "ClawGuard"
        description = "Raw IP address in script suggesting hardcoded C2"
        severity = "medium"
        category = "network_exfiltration"
    strings:
        $ip = /\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/
        $localhost = "127.0.0.1"
        $zeros = "0.0.0.0"
    condition:
        $ip and not ($localhost or $zeros)
}
