const API_ROOT = "";
let currentChannel = null;
let channels = [];
let lastMessageCount = 0;

async function apiGet(path) {
  const r = await fetch(path);
  if (!r.ok) throw new Error(r.statusText);
  return r.json();
}
async function apiPost(path, bodyObj) {
  const r = await fetch(path, {
    method: "POST",
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify(bodyObj)
  });
  if (!r.ok) throw new Error(r.statusText);
  return r.json();
}

async function refreshChannels() {
  try {
    const res = await apiGet("/get-channels");
    channels = res.channels || [];
    const list = document.getElementById("channel-list");
    list.innerHTML = "";
    channels.forEach(c => {
      const li = document.createElement("li");
      li.textContent = c;
      li.onclick = () => selectChannel(c);
      list.appendChild(li);
    });
  } catch(e) {
    console.warn("refreshChannels error", e);
  }
}

async function selectChannel(name) {
  currentChannel = name;
  document.getElementById("current-channel").textContent = name;
  document.getElementById("notification").classList.add("hidden");
  await refreshMessages();
}

async function refreshMessages() {
  if (!currentChannel) return;
  try {
    const res = await apiPost("/get-messages", {channel: currentChannel});
    const msgs = (res.messages || []);
    const box = document.getElementById("messages");
    box.innerHTML = "";
    msgs.forEach(m => {
      const div = document.createElement("div");
      div.className = "message";
      div.innerHTML = `<span class="sender">${escapeHtml(m.sender)}:</span> ${escapeHtml(m.message)}`;
      box.appendChild(div);
    });
    box.scrollTop = box.scrollHeight;
    // notifications when new messages appear and page not focused
    if (!document.hasFocus() && msgs.length > lastMessageCount) {
      document.getElementById("notification").classList.remove("hidden");
    }
    lastMessageCount = msgs.length;
  } catch(e) {
    console.warn("refreshMessages error", e);
  }
}

async function createChannel() {
  const name = document.getElementById("new-channel").value.trim();
  if (!name) return;
  await apiPost("/create-channel", {channel: name});
  await refreshChannels();
  selectChannel(name);
  document.getElementById("new-channel").value = "";
}

async function sendMessage() {
  const msg = document.getElementById("message-input").value.trim();
  const sender = document.getElementById("sender").value.trim() || "anonymous";
  if (!currentChannel || !msg) return;
  await apiPost("/send-channel", {channel: currentChannel, sender, message: msg});
  document.getElementById("message-input").value = "";
  await refreshMessages();
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
}

document.getElementById("create-channel").addEventListener("click", createChannel);
document.getElementById("send-btn").addEventListener("click", sendMessage);
document.getElementById("message-input").addEventListener("keydown", e => { if (e.key === "Enter") sendMessage(); });

window.addEventListener("load", async () => {
  await refreshChannels();
  // poll for messages every 2s
  setInterval(refreshMessages, 2000);
});
