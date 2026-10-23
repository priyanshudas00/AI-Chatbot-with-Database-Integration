let activeChatId = null;

const chatListEl = document.getElementById("chatList");
const createForm = document.getElementById("createChatForm");
const messageForm = document.getElementById("messageForm");
const messagesEl = document.getElementById("messages");
const activeChatTitle = document.getElementById("activeChatTitle");
const messageInput = document.getElementById("messageInput");
const sendBtn = document.getElementById("sendBtn");
const renameBtn = document.getElementById("renameChat");
const deleteBtn = document.getElementById("deleteChat");

function escapeHtml(text) {
  return text
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}


function formatMessage(text) {
  const escaped = escapeHtml(text);
  return escaped
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\n/g, "<br>");
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || "Request failed");
  }
  return data;
}

function setChatEnabled(enabled) {
  messageInput.disabled = !enabled;
  sendBtn.disabled = !enabled;
  renameBtn.disabled = !enabled;
  deleteBtn.disabled = !enabled;
}

function renderMessages(items) {
  messagesEl.innerHTML = "";
  for (const item of items) {
    const div = document.createElement("div");
    div.className = `msg ${item.role}`;
    div.innerHTML = `
      <div class="meta">${escapeHtml(item.role)} • ${escapeHtml(String(item.created_at))}</div>
      <div>${formatMessage(item.content)}</div>
    `;
    messagesEl.appendChild(div);
  }
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

async function loadChats() {
  const chats = await api("/api/chats");
  chatListEl.innerHTML = "";

  for (const chat of chats) {
    const li = document.createElement("li");
    li.dataset.id = chat.id;
    if (chat.id === activeChatId) {
      li.classList.add("active");
    }
    const topic = chat.topic ? `Topic: ${escapeHtml(chat.topic)}` : "No topic";
    li.innerHTML = `<strong>#${chat.id}</strong> ${escapeHtml(chat.user_name)}<br><small>${topic}</small>`;
    li.addEventListener("click", async () => {
      activeChatId = chat.id;
      activeChatTitle.textContent = `Chat #${chat.id} - ${chat.user_name}`;
      setChatEnabled(true);
      await loadChats();
      await loadMessages();
    });
    chatListEl.appendChild(li);
  }
}

async function loadMessages() {
  if (!activeChatId) {
    return;
  }
  const items = await api(`/api/chats/${activeChatId}/messages`);
  renderMessages(items);
}

createForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const userName = document.getElementById("userName").value.trim();
  const topic = document.getElementById("topic").value.trim();
  if (!userName) {
    alert("User name is required");
    return;
  }

  try {
    const result = await api("/api/chats", {
      method: "POST",
      body: JSON.stringify({ user_name: userName, topic }),
    });
    activeChatId = result.chat_id;
    activeChatTitle.textContent = `Chat #${activeChatId} - ${userName}`;
    setChatEnabled(true);
    createForm.reset();
    await loadChats();
    renderMessages([]);
  } catch (error) {
    alert(error.message);
  }
});

messageForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!activeChatId) {
    return;
  }
  const text = messageInput.value.trim();
  if (!text) {
    return;
  }

  messageInput.value = "";
  try {
    await api(`/api/chats/${activeChatId}/messages`, {
      method: "POST",
      body: JSON.stringify({ message: text }),
    });
    await loadMessages();
  } catch (error) {
    alert(error.message);
  }
});

renameBtn.addEventListener("click", async () => {
  if (!activeChatId) {
    return;
  }
  const topic = prompt("New topic:");
  if (!topic) {
    return;
  }
  try {
    await api(`/api/chats/${activeChatId}`, {
      method: "PATCH",
      body: JSON.stringify({ topic }),
    });
    await loadChats();
  } catch (error) {
    alert(error.message);
  }
});

deleteBtn.addEventListener("click", async () => {
  if (!activeChatId) {
    return;
  }
  if (!confirm("Delete this chat and all messages?")) {
    return;
  }
  try {
    await api(`/api/chats/${activeChatId}`, { method: "DELETE" });
    activeChatId = null;
    activeChatTitle.textContent = "Select a chat";
    setChatEnabled(false);
    renderMessages([]);
    await loadChats();
  } catch (error) {
    alert(error.message);
  }
});

document.getElementById("refreshChats").addEventListener("click", async () => {
  try {
    await loadChats();
  } catch (error) {
    alert(error.message);
  }
});

setChatEnabled(false);
loadChats().catch((error) => alert(error.message));
