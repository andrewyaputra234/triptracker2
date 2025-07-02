document.addEventListener("DOMContentLoaded", () => {
  const chatBox = document.getElementById('chat-box');
  const input = document.getElementById('user-input');
  const sendBtn = document.getElementById('send-btn');

  const tripName = window.tripNameFromServer || '';
  const suggestion = window.suggestionFromServer || '';

  let messages = [
    { role: "system", content: "You are a helpful assistant that gives budget advice." },
    { role: "assistant", content: suggestion }
  ];

  function convertToHTML(input) {
  let html = input
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/(?:^|\n)([-*])\s+(.*)/g, '<li>$2</li>')
    .replace(/(<li>[\s\S]*?<\/li>)/g, match => `<ul>${match}</ul>`)
    .replace(/\n\n+/g, '</p><p>')
    .replace(/\n/g, '<br>');

  if (!html.startsWith('<p>')) {
    html = '<p>' + html + '</p>';
  }

  return html;
}

  const appendMessage = (sender, text, isTypewriter = false) => {
    const msg = document.createElement('div');
    msg.className = `chat-msg ${sender}`;

    const bubble = document.createElement('div');
    bubble.className = 'chat-bubble';

    const timestamp = document.createElement('div');
    timestamp.className = 'chat-timestamp';
    const now = new Date();
    timestamp.textContent = `${sender === 'user' ? 'You' : 'AI'} • ${now.toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'})}`;

    msg.appendChild(bubble);
    msg.appendChild(timestamp);
    chatBox.appendChild(msg);
    chatBox.scrollTop = chatBox.scrollHeight;

    if (isTypewriter) {
      bubble.innerHTML = "";
      const htmlText = convertToHTML(text);
      const regex = /(<[^>]+>|[^<]+)/g;
      const chunks = htmlText.match(regex);

      let chunkIndex = 0;
      let charIndex = 0;

      function type() {
        if (chunkIndex >= chunks.length) return;

        const chunk = chunks[chunkIndex];

        if (chunk.startsWith('<')) {
          bubble.innerHTML += chunk;
          chunkIndex++;
          setTimeout(type, 2);
        } else {
          bubble.innerHTML += chunk.charAt(charIndex);
          charIndex++;
          if (charIndex === chunk.length) {
            chunkIndex++;
            charIndex = 0;
            setTimeout(type, 2);
          } else {
            setTimeout(type, 2);
          }
        }

        chatBox.scrollTop = chatBox.scrollHeight;
      }

      type();
    } else {
      bubble.innerHTML = convertToHTML(text);
    }
  };

  const sendMessage = async () => {
    const userInput = input.value.trim();
    if (!userInput) return;

    appendMessage('user', userInput);
    input.value = "";
    messages.push({ role: "user", content: userInput });

    const loadingMsg = document.createElement('div');
    loadingMsg.className = 'chat-msg ai';
    const loadingBubble = document.createElement('div');
    loadingBubble.className = 'chat-bubble';
    loadingBubble.textContent = 'AI is typing...';
    loadingMsg.appendChild(loadingBubble);
    chatBox.appendChild(loadingMsg);
    chatBox.scrollTop = chatBox.scrollHeight;

    try {
      const response = await fetch(`/api/ai_chat/${tripName}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages })
      });

      const data = await response.json();
      chatBox.removeChild(loadingMsg);

      if (data.reply) {
        messages.push({ role: "assistant", content: data.reply });
        appendMessage('ai', data.reply, true);
      } else {
        appendMessage('ai', '[No reply]');
      }
    } catch (error) {
      chatBox.removeChild(loadingMsg);
      appendMessage('ai', '[Error fetching response]');
    }
  };

  appendMessage('ai', suggestion, true);

  sendBtn.addEventListener('click', sendMessage);
  input.addEventListener('keydown', e => {
    if (e.key === 'Enter') sendMessage();
  });
});
