const chatBox = document.getElementById('chat-box');
const input = document.getElementById('chat-input');
let conversationHistory = [];

function scrollToBottom() { chatBox.scrollTop = chatBox.scrollHeight; }

function addMessage(type, content) {
    const isAI = type === 'ai';
    const div = document.createElement('div');
    div.className = 'msg-bubble';
    div.style.cssText = 'display:flex;align-items:flex-start;gap:10px;' + (isAI ? '' : 'flex-direction:row-reverse;');
    div.innerHTML = `
        <div style="width:36px;height:36px;border-radius:50%;flex-shrink:0;
            background:${isAI ? 'linear-gradient(135deg,#3f65ff,#7f35db)' : '#ede9ff'};
            display:flex;align-items:center;justify-content:center;font-size:16px;">
            ${isAI ? '🤖' : '👤'}
        </div>
        <div style="padding:12px 16px;max-width:420px;border-radius:16px;
            ${isAI ? 'background:#f5f7fb;border:1px solid #dfe4f2;border-top-left-radius:4px;'
                   : 'background:linear-gradient(135deg,#3f65ff,#7f35db);border-top-right-radius:4px;'}">
            <p style="font-size:14px;color:${isAI ? '#333' : 'white'};margin:0;line-height:1.6;">${content}</p>
        </div>`;
    chatBox.appendChild(div);
    scrollToBottom();
}

function addTyping() {
    const div = document.createElement('div');
    div.id = 'typing-indicator';
    div.style.cssText = 'display:flex;align-items:flex-start;gap:10px;';
    div.innerHTML = `
        <div style="width:36px;height:36px;border-radius:50%;flex-shrink:0;
            background:linear-gradient(135deg,#3f65ff,#7f35db);
            display:flex;align-items:center;justify-content:center;font-size:16px;">🤖</div>
        <div style="background:#f5f7fb;border:1px solid #dfe4f2;border-radius:16px;border-top-left-radius:4px;padding:12px 16px;">
            <span class="dot"></span><span class="dot"></span><span class="dot"></span>
        </div>`;
    chatBox.appendChild(div);
    scrollToBottom();
}

function removeTyping() {
    const el = document.getElementById('typing-indicator');
    if (el) el.remove();
}

function showBrokerModal(productName, productUrl) {
    const existing = document.getElementById('broker-modal');
    if (existing) existing.remove();

    const modal = document.createElement('div');
    modal.id = 'broker-modal';
    modal.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);z-index:9999;display:flex;align-items:center;justify-content:center;';
    modal.innerHTML = `
        <div style="background:#fff;border-radius:20px;padding:32px;max-width:480px;width:90%;max-height:80vh;overflow-y:auto;box-shadow:0 20px 60px rgba(0,0,0,.2);">
            <h3 style="font-size:18px;font-weight:700;color:#222;margin:0 0 6px;">Choose a Broker</h3>
            <p style="color:#62708f;font-size:14px;margin:0 0 20px;">Select a broker to send your request for <strong>${productName}</strong></p>
            <div id="broker-list" style="display:flex;flex-direction:column;gap:10px;">
                <p style="color:#62708f;text-align:center;padding:20px 0;">Loading brokers...</p>
            </div>
            <button onclick="document.getElementById('broker-modal').remove()"
                style="margin-top:16px;width:100%;padding:10px;border:1.5px solid #dfe4f2;border-radius:10px;background:#fff;color:#62708f;font-size:14px;cursor:pointer;font-family:inherit;">
                Cancel
            </button>
        </div>`;
    document.body.appendChild(modal);

    fetch('/api/brokers/')
        .then(r => r.json())
        .then(data => {
            const list = document.getElementById('broker-list');
            if (!data.brokers || data.brokers.length === 0) {
                list.innerHTML = `<p style="color:#62708f;text-align:center;">No brokers found. <a href="/brokers" style="color:#5b48f2;">Browse brokers</a></p>`;
                return;
            }
            list.innerHTML = data.brokers.map(b => `
                <button onclick="selectBroker(${b.id}, \`${productName.replace(/`/g,'\\`')}\`, \`${productUrl.replace(/`/g,'\\`')}\`)"
                    style="padding:14px 16px;border:1.5px solid #dfe4f2;border-radius:12px;background:#fff;cursor:pointer;
                    text-align:left;font-family:inherit;transition:border-color .15s,background .15s;width:100%;"
                    onmouseover="this.style.borderColor='#5b48f2';this.style.background='#f5f3ff';"
                    onmouseout="this.style.borderColor='#dfe4f2';this.style.background='#fff';">
                    <p style="font-weight:600;color:#222;margin:0 0 2px;font-size:14px;">${b.name}</p>
                    <p style="color:#62708f;margin:0;font-size:12px;">${b.city ? b.city + ' • ' : ''}⭐ ${b.rating.toFixed(1)}</p>
                </button>`).join('');
        })
        .catch(() => {
            document.getElementById('broker-list').innerHTML = `
                <a href="/brokers" style="display:block;padding:14px;background:#5b48f2;color:#fff;border-radius:10px;text-align:center;font-weight:600;text-decoration:none;">
                    Browse Brokers Page
                </a>`;
        });
}

function selectBroker(brokerId, productName, productUrl) {
    document.getElementById('broker-modal').remove();
    // Build URL with prefilled data
    const finalUrl = productUrl || `https://www.amazon.com/s?k=${encodeURIComponent(productName)}`;
    const url = `/create?broker_id=${brokerId}&prefill_name=${encodeURIComponent(productName)}&prefill_url=${encodeURIComponent(finalUrl)}`;
    window.location.href = url;
}

function showResults(data) {
    const area = document.getElementById('results-area');
    const container = document.getElementById('results-container');
    if (!data.has_results) { area.style.display = 'none'; return; }

    const colors = {
        'Amazon': { bg: '#fff3e0', color: '#e65100', emoji: '🛍️' },
        'Shein':  { bg: '#fce4ec', color: '#c2185b', emoji: '👗' },
        'Temu':   { bg: '#e3f2fd', color: '#1565c0', emoji: '🛒' },
    };

    let minPrice = Infinity, cheapest = '';
    data.results.forEach(item => {
        const p = parseFloat((item.price || '').replace('$','').replace(',',''));
        if (!isNaN(p) && p < minPrice) { minPrice = p; cheapest = item.platform; }
    });

    const grouped = {};
    data.results.forEach(item => { if (!grouped[item.platform]) grouped[item.platform] = item; });

    let html = `
        <div class="section-row">
            <div class="section-head left">
                <h2>Results for "${data.product_name}"</h2>
                <p>Cheapest: <strong style="color:#15b86a">${cheapest} $${isFinite(minPrice) ? minPrice.toFixed(2) : 'N/A'}</strong></p>
            </div>
        </div>
        <div class="cards steps-grid" style="margin-bottom:20px;">`;

    Object.values(grouped).forEach(item => {
        const c = colors[item.platform] || { bg: '#f5f7fb', color: '#5b48f2', emoji: '🛒' };
        const isCheap = item.platform === cheapest;
        const hasUrl = item.url && item.url.length > 0;

        html += `
            <div class="card" style="position:relative;${isCheap ? 'border:2px solid #15b86a;' : ''}">
                ${isCheap ? '<span style="position:absolute;top:-10px;left:12px;background:#15b86a;color:#fff;font-size:11px;font-weight:700;padding:2px 10px;border-radius:999px;">✅ Cheapest</span>' : ''}
                <div style="display:flex;align-items:center;gap:8px;margin-bottom:12px;">
                    <span style="font-size:20px;">${c.emoji}</span>
                    <span style="background:${c.bg};color:${c.color};padding:2px 10px;border-radius:999px;font-size:12px;font-weight:700;">${item.platform}</span>
                    ${item.note ? `<span style="font-size:11px;color:#62708f;font-style:italic;">${item.note}</span>` : ''}
                </div>
                ${item.image
                    ? `<img src="${item.image}" style="width:100%;height:120px;object-fit:contain;border-radius:10px;background:#f5f7fb;margin-bottom:10px;" onerror="this.style.display='none'">`
                    : `<div style="height:80px;background:#f5f7fb;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:32px;margin-bottom:10px;">${c.emoji}</div>`}
                <p style="font-weight:600;color:#222;font-size:13px;margin:0 0 6px;overflow:hidden;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;">${item.name || 'Product'}</p>
                <p style="font-size:20px;font-weight:700;color:#5b48f2;margin:0 0 12px;">${item.price}</p>
                <div style="display:flex;gap:8px;">
                    ${hasUrl ? `<a href="${item.url}" target="_blank" class="btn btn-light" style="flex:1;font-size:12px;padding:8px;text-decoration:none;text-align:center;">View →</a>` : ''}
                    <button onclick="showBrokerModal(\`${(item.name || data.product_name).replace(/`/g,'\\`')}\`, \`${hasUrl ? item.url.replace(/`/g,'\\`') : ''}\`)"
                        style="flex:1;padding:8px;font-size:12px;font-weight:600;border:1.5px solid #5b48f2;color:#5b48f2;background:#fff;border-radius:10px;cursor:pointer;font-family:inherit;">
                        📋 Request
                    </button>
                </div>
            </div>`;
    });

    html += `</div>
        <div class="card" style="background:linear-gradient(135deg,#3f65ff,#7f35db);border:none;display:flex;align-items:center;justify-content:space-between;gap:16px;">
            <div>
                <p style="color:#fff;font-weight:700;font-size:16px;margin:0 0 4px;">Found what you need?</p>
                <p style="color:rgba(255,255,255,.8);font-size:13px;margin:0;">Send a request and let brokers compete</p>
            </div>
            <a href="/brokers" class="btn btn-primary" style="white-space:nowrap;text-decoration:none;">Browse Brokers</a>
        </div>`;

    container.innerHTML = html;
    area.style.display = 'block';
    area.scrollIntoView({ behavior: 'smooth', block: 'start' });
    conversationHistory = [];
}

function getCookie(name) {
    let val = null;
    document.cookie.split(';').forEach(c => {
        if (c.trim().startsWith(name + '=')) val = decodeURIComponent(c.trim().split('=')[1]);
    });
    return val;
}

async function sendMessage() {
    const message = input.value.trim();
    if (!message) return;
    addMessage('user', message);
    input.value = '';
    addTyping();
    conversationHistory.push({ role: 'user', content: message });
    try {
        const res = await fetch(chatSearchUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
            body: JSON.stringify({ message, type: 'chat', history: conversationHistory }),
        });
        const data = await res.json();
        removeTyping();
        if (data.type === 'search') {
            addMessage('ai', data.ai_summary || 'Here are the results!');
            showResults(data);
        } else {
            addMessage('ai', data.message);
            conversationHistory.push({ role: 'assistant', content: data.message });
        }
    } catch (err) {
        removeTyping();
        addMessage('ai', 'Sorry, something went wrong. Please try again.');
    }
}

async function categorySearch(category, emoji) {
    conversationHistory = [];
    addMessage('user', emoji + ' ' + category);
    addTyping();
    conversationHistory.push({ role: 'user', content: category });
    try {
        const res = await fetch(chatSearchUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
            body: JSON.stringify({ message: category, type: 'chat', history: conversationHistory }),
        });
        const data = await res.json();
        removeTyping();
        if (data.type === 'search') {
            addMessage('ai', data.ai_summary || 'Here are the results!');
            showResults(data);
        } else {
            addMessage('ai', data.message);
            conversationHistory.push({ role: 'assistant', content: data.message });
        }
    } catch (err) {
        removeTyping();
        addMessage('ai', 'What ' + category + ' product are you looking for?');
    }
}
