var Telegram = {
    emoji_map: {
        "s0": "❕",
        "s1": "ℹ️",
        "s2": "⚠️",
        "s3": "🔸",
        "s4": "🛑",
        "s5": "💣",
        "ok": "✅",
        "update": "🔄"
    },

    html_tags_map: {
        "<br>": ""
    },

    token: null,
    to: null,
    message: null,
    proxy: null,
    parse_mode: null,

    sendMessage: function() {
        var params = {
            chat_id: Telegram.to,
            text: Telegram.message,
            disable_web_page_preview: true,
            disable_notification: false
        },
        data,
        response,
        request = new CurlHttpRequest(),
        url = 'https://api.telegram.org/bot' + Telegram.token + '/sendMessage';

        if (Telegram.parse_mode !== null) {
            params['parse_mode'] = Telegram.parse_mode;
        }

        if (Telegram.proxy) {
            request.SetProxy(Telegram.proxy);
        }

        request.AddHeader('Content-Type: application/json');
        data = JSON.stringify(params);

        // Remove replace() function if you want to see the exposed token in the log file.
        Zabbix.Log(4, '[Telegram Webhook] URL: ' + url.replace(Telegram.token, '<TOKEN>'));
        Zabbix.Log(4, '[Telegram Webhook] params: ' + data);
        response = request.Post(url, data);
        Zabbix.Log(4, '[Telegram Webhook] HTTP code: ' + request.Status());

        try {
            response = JSON.parse(response);
        }
        catch (error) {
            response = null;
        }

        if (request.Status() !== 200 || typeof response.ok !== 'boolean' || response.ok !== true) {
            if (typeof response.description === 'string') {
                throw response.description;
            }
            else {
                throw 'Unknown error. Check debug log for more information.'
            }
        }
    }
}

try {
    var params = JSON.parse(value);

    if (typeof params.Token === 'undefined') {
        throw 'Incorrect value is given for parameter "Token": parameter is missing';
    }

    Telegram.token = params.Token;

    if (params.HTTPProxy) {
        Telegram.proxy = params.HTTPProxy;
    } 

    if (['Markdown', 'HTML', 'MarkdownV2'].indexOf(params.ParseMode) !== -1) {
        Telegram.parse_mode = params.ParseMode;
    }

    Telegram.to = params.To;
    Telegram.message = params.Subject + '\n' + params.Message;

    // Replace emoji
    var emoji_re = /{{(\w*)}}/gi;
    Telegram.message = Telegram.message.replace(emoji_re, function(match, p1) {
        if (typeof Telegram.emoji_map[p1.toLowerCase()] !== 'undefined') {
            return Telegram.emoji_map[p1.toLowerCase()]
        }
        else {
            return '{{' + p1 + '}}'
        }
    });

    // Replace unsupported HTML tags
    var html_re = /(<\w*>)/gi;
    Telegram.message = Telegram.message.replace(html_re, function(match, p1) {
        if (typeof Telegram.html_tags_map[p1.toLowerCase()] !== 'undefined') {
            return Telegram.html_tags_map[p1.toLowerCase()]
        }
        else {
            return p1
        }
    });

    Telegram.sendMessage();

    return 'OK';
}
catch (error) {
    Zabbix.Log(4, '[Telegram Webhook] notification failed: ' + error);
    throw 'Sending failed: ' + error + '.';
}