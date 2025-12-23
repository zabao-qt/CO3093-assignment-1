const REFRESH_INTERVAL = 3000;

let currentChat = null;
let myId = null;
const notifiedBroadcasts = new Set();

function q(s){return document.querySelector(s)}

async function fetchMyId(){
  let r = await apiGET("/whoami");
  if(r && r.id) myId = r.id;
  else myId = "me";
}

async function apiGET(p){
  try{
    let r=await fetch(p, { credentials: 'include' });
    let t=await r.text();
    try{return JSON.parse(t)}catch(e){return t}
  }catch(e){return {error:"offline"}}
}

async function apiPOST(p,b){
  try{
    let r=await fetch(p,{
      method:"POST",
      credentials: 'include',
      headers:{"Content-Type":"application/json"},
      body:JSON.stringify(b)
    });
    let t=await r.text();
    try{return JSON.parse(t)}catch(e){return t}
  }catch(e){return {error:"offline"}}
}

function addNotification(x){
  let n=document.createElement("div");
  n.className="alert alert-info py-1";
  n.innerHTML=x;
  q("#notifications").prepend(n);
  setTimeout(()=>n.remove(),6000);
}

function escapeHtml(s){
  if(!s)return "";
  return s.replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":"&#39;"})[m]);
}

async function refreshOnlinePeers(){
  let r = await apiGET("/get-list");
  if(typeof r === "string"){
    try { r = JSON.parse(r); } catch(e){ r = []; }
  }

  let ul=q("#onlinePeers");
  ul.innerHTML="";
  if(!r||r.error) {
    addNotification("Tracker offline or returned error");
    return;
  }

  r.forEach(p=>{
    let id = `${p.ip}:${p.port}`;
    if (id === myId) return;

    let li = document.createElement("li");
    li.className = "list-group-item d-flex align-items-center justify-content-between";

    let left = document.createElement("div");
    left.className = "d-flex align-items-center";
    left.innerHTML = `
      <div class="me-2 d-flex align-items-center justify-content-center rounded-circle" style="width:36px;height:36px;background:linear-gradient(135deg,#2b2b50,#3b3b7a);box-shadow:0 4px 14px rgba(106,92,255,0.12);">
        <i class="bi bi-person-fill" style="font-size:1rem;color:#fff;"></i>
      </div>
      <div class="ms-1">
        <div class="fw-semibold small">${escapeHtml(id)}</div>
      </div>
    `;

    let btnWrap = document.createElement("div");
    btnWrap.innerHTML = `
      <button class="btn btn-sm btn-outline-light" title="Connect" onclick='connectPeer("${p.ip}",${p.port})'>
        <i class="bi bi-plug-fill"></i>
      </button>
    `;

    li.appendChild(left);
    li.appendChild(btnWrap);
    ul.appendChild(li);
  });
}

async function refreshChannels(){
  let r = await apiGET("http://127.0.0.1:9000/channels");
  let list = q("#channelsList");
  if(!list) return;

  let html = "";
  if(r && typeof r === "object" && Object.keys(r).length){
    for(let name in r){
      let esc = escapeHtml(name);
      html += `
        <div class="p-2 channel-item d-flex align-items-center justify-content-between"
             onclick='openChannel("${esc}")'>
          <div class="d-flex align-items-center">
            <i class="bi bi-hash text-accent me-2" style="color:var(--accent);"></i>
            <span class="fw-semibold">${esc}</span>
          </div>
          <i class="bi bi-caret-right-fill"></i>
        </div>`;
    }
  } else {
    html = `
      <div class="small p-2 d-flex align-items-center">
        <i class="bi bi-slash-circle me-2"></i>No channels
      </div>`;
  }

  list.innerHTML = html;
}

async function createChannel(){
  let name = q("#createChannelInput").value.trim();
  if(!name) return;
  await apiPOST("http://127.0.0.1:9000/create-channel", { name });
  refreshChannels();
  addNotification("Channel created: " + name);
}


async function refreshPending(){
  let r = await apiGET("/get-pending");
  let ul = q("#pendingRequests");
  ul.innerHTML = "";

  (r || []).forEach(req => {
    let li = document.createElement("li");
    li.className = "list-group-item d-flex justify-content-between align-items-center";

    let encoded = encodeURIComponent(JSON.stringify(req));

    li.innerHTML = `
      <div class="d-flex flex-column flex-md-row align-items-center justify-content-between w-100">
        <div class="mb-2 mb-md-0">
          <span class="fw-semibold small">${escapeHtml(req.from)}</span>
          <span class="small">wants to connect</span>
        </div>
        
        <div class="d-flex align-items-center">
          <button class="btn btn-sm btn-outline-success me-1 d-flex align-items-center justify-content-center"
                  style="width:32px;height:32px"
                  onclick='acceptRequest("${encoded}")'>
            <i class="bi bi-check-lg"></i>
          </button>

          <button class="btn btn-sm btn-outline-danger d-flex align-items-center justify-content-center"
                  style="width:32px;height:32px"
                  onclick='denyRequest("${encoded}")'>
            <i class="bi bi-x-lg"></i>
          </button>
        </div>
      </div>
    `;
    ul.appendChild(li);
  });
}

async function refreshConnected(){
  let r = await apiGET("/get-connected");

  if(r && typeof r === "object" && r.status === "ok" && Array.isArray(r.peers)){
    r = r.peers;
  }
  if(r && typeof r === "object" && !Array.isArray(r)){
    // try to detect if it's shaped like { "<id>": {...}, ... } or {peers: [...]}
    if(Array.isArray(r.peers)) r = r.peers;
    else {
      // convert object values to array
      r = Object.keys(r).map(k => r[k]);
    }
  }

  if(!Array.isArray(r)) r = [];

  let ul = q("#connectedPeers");
  ul.innerHTML = "";

  r.forEach(p=>{
    let host = p.host || p.ip || p[0] || "";
    let port = p.port || p[1] || "";
    let id = p.id || `${host}:${port}`;
    let encoded = encodeURIComponent(JSON.stringify({ id, ip: host, port }));

    let li = document.createElement("li");
    li.className = "list-group-item d-flex justify-content-between align-items-center";

    li.innerHTML = `
      <div class="d-flex align-items-center">
        <div class="me-2 d-flex align-items-center justify-content-center rounded-circle"
            style="width:36px;height:36px;background:linear-gradient(135deg,#3d2b62,#5d4ca4);box-shadow:0 4px 14px rgba(106,92,255,0.12);">
          <i class="bi bi-person-badge-fill" style="font-size:1rem;color:#fff;"></i>
        </div>
        <div>
          <div class="fw-semibold small">${escapeHtml(id)}</div>
          <div class="small">connected</div>
        </div>
      </div>

      <div class="d-flex align-items-center">
        <button class="btn btn-sm btn-outline-primary me-1 d-flex align-items-center justify-content-center"
                style="width:34px;height:34px"
                title="Open chat"
                onclick='openP2P("${encoded}")'>
          <i class="bi bi-chat-dots-fill"></i>
        </button>

        <button class="btn btn-sm btn-outline-danger d-flex align-items-center justify-content-center"
                style="width:34px;height:34px"
                title="Disconnect"
                onclick='disconnectPeer("${encoded}")'>
          <i class="bi bi-plug-fill"></i>
        </button>
      </div>
    `;

    ul.appendChild(li);
  });
}

async function refreshMessages(){
  let r = await apiGET("/get-messages");
  let win = q("#chatWindow");
  if(!Array.isArray(r)) r = (r || []);
  win.innerHTML = "";

  let showPeer = null;
  if(currentChat && currentChat.type === "p2p") showPeer = currentChat.id;

  (r || []).forEach(m=>{
    let from, msg, isBroadcast=false, broadcastSender=null;
    if(Array.isArray(m) || Array.isTuple && m.length >= 2){
      if(m[0] === "BROADCAST" && m.length >= 3){
        isBroadcast = true;
        broadcastSender = m[1];
        msg = m[2];
        from = "BROADCAST";
      } else {
        from = m[0];
        msg = m[1];
      }
    } else if(m && typeof m === "object"){
      // object form from server
      if(m.type === "BROADCAST"){
        isBroadcast = true;
        broadcastSender = m.from || m.sender || "unknown";
        msg = m.message || m.msg || "";
        from = "BROADCAST";
      } else {
        from = m.from || m.sender || "unknown";
        msg = m.message || m.msg || "";
      }
    } else {
      // unknown format — skip
      return;
    }

    // Filtering:
    if(showPeer){
      if(!(from === showPeer || from === myId || from === "BROADCAST")) return;
    }

    // Notify for broadcast messages (only once per unique sender+msg)
    if(from === "BROADCAST"){
      // Determine origin display: prefer broadcastSender, otherwise fallback to myId
      let origin = broadcastSender || "unknown";
      // Build a notification key to avoid duplicates
      let key = `${origin}:${msg}`;
      if(broadcastSender !== myId && !notifiedBroadcasts.has(key)){
        if (broadcastSender === myId)
            addNotification(`BROADCASTED: ${msg}`);
        else
            addNotification(`BROADCASTED from ${origin}: ${msg}`);
        notifiedBroadcasts.add(key);
        // keep notifiedBroadcasts bounded: remove old entries when size grows
        if(notifiedBroadcasts.size > 200) {
          // drop oldest by recreating a new Set of last 100
          let arr = Array.from(notifiedBroadcasts);
          let slice = arr.slice(-100);
          notifiedBroadcasts.clear();
          slice.forEach(x=>notifiedBroadcasts.add(x));
        }
      }
    }

    // Build bubble
    const wrapper = document.createElement("div");
    wrapper.className = "d-flex mb-2";

    if (from === "BROADCAST") {
      let origin = broadcastSender || "unknown";
      if (broadcastSender === myId) {
          wrapper.innerHTML = 
          `<div class="d-flex justify-content-center mx-auto px-3 py-1 small text-white bg-secondary rounded-pill" style="width: fit-content;">
              <i class="bi bi-megaphone-fill me-2"></i>
              BROADCASTED: ${escapeHtml(msg)}
          </div>`;
      } else {
          wrapper.innerHTML = 
          `<div class="d-flex justify-content-center mx-auto px-3 py-1 small text-white bg-secondary rounded-pill" style="width: fit-content;">
              <i class="bi bi-megaphone-fill me-2"></i>
              BROADCASTED from ${escapeHtml(origin)}: ${escapeHtml(msg)}
          </div>`;
      }
  } else if(from === myId){
      wrapper.innerHTML = `
        <div class="d-flex ms-auto flex-column align-items-end" style="max-width:72%;">
          <div class="small mb-1">You <i class="bi bi-check2-circle ms-1" title="sent"></i></div>
          <div class="px-3 py-2 rounded-3 text-white" style="background:linear-gradient(135deg,var(--accent),#9e85ff);box-shadow:none;">
            ${escapeHtml(msg)}
          </div>
        </div>`;
    } else {
      wrapper.innerHTML = `
        <div class="d-flex me-auto flex-column align-items-start" style="max-width:72%;">
          <div class="small mb-1">${escapeHtml(from)}</div>
          <div class="px-3 py-2 rounded-3 text-white" style="background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.08);">
            ${escapeHtml(msg)}
          </div>
        </div>`;
    }
    win.appendChild(wrapper);
  });

  // scroll to bottom
  win.scrollTop = win.scrollHeight;
}

async function connectPeer(ip,port){
  await apiPOST("/connect-peer",{ip,port});
  addNotification("Connect request sent to "+ip+":"+port);
}

async function acceptRequest(encoded){
  let r = JSON.parse(decodeURIComponent(encoded));
  let resp = await apiPOST("/accept-request", r);
  if(resp && resp.status){
    addNotification("Accepted " + r.from);
  } else {
    addNotification("Accept failed");
  }
  // update UI immediately
  refreshPending();
  refreshConnected();
}

async function denyRequest(encoded){
  let r = JSON.parse(decodeURIComponent(encoded));
  let resp = await apiPOST("/deny-request", r);
  if(resp && resp.status){
    addNotification("Denied " + r.from);
  } else {
    addNotification("Deny failed");
  }
  // update UI immediately
  refreshPending();
  refreshConnected();
}

async function disconnectPeer(encoded){
  try{
    let p = JSON.parse(decodeURIComponent(encoded));
    let resp = await apiPOST("/disconnect-peer", { id: p.id, ip: p.ip, port: p.port });
    if(resp && (resp.status === "ok" || resp.status === "disconnected")){
      addNotification("Disconnected " + (p.id || `${p.ip}:${p.port}`));
    } else {
      addNotification("Disconnect request failed");
    }
  }catch(e){
    addNotification("Disconnect: bad peer data");
  }
  refreshConnected();
}

function openP2P(s){
  try{
    let decoded = decodeURIComponent(s);
    let p = JSON.parse(decoded);
    currentChat = { type:"p2p", ip:p.ip || p.host, port:p.port, id:p.id || (`${p.ip||p.host}:${p.port}`) };
    q("#chatWindow").innerHTML = `<div class="">Chatting with ${escapeHtml(currentChat.id)}</div>`;
  }catch(e){
    addNotification("Open chat failed: invalid peer data");
  }
}

// async function sendMessage(){
//   if(!currentChat){addNotification("No chat selected");return}
//   let msg=q("#messageInput").value.trim();
//   if(!msg)return;
//   if(currentChat.type==="p2p"){
//     await apiPOST("/send-peer",{ip:currentChat.ip,port:currentChat.port,message:msg});
//     addNotification("Sent to "+currentChat.id);
//   }
//   q("#messageInput").value="";
// }

async function broadcastMessage(){
  let msg=prompt("Broadcast message:");
  if(!msg)return;
  await apiPOST("/broadcast-peer",{message:msg});
  addNotification("Broadcast sent");
}

function openChannel(name){
  currentChat = { type:"channel", name };
  q("#chatWindow").innerHTML =
  `<div class="d-flex align-items-center justify-content-between mb-3">
      <div class="d-flex align-items-center gap-2">
        <i class="bi bi-hash fs-4" style="color:var(--accent)"></i>
        <div>
          <div class="fw-semibold">${escapeHtml(name)}</div>
          <div class="small">Channel</div>
        </div>
      </div>
      <button class="btn btn-outline-danger ms-2" onclick="leaveChannel()" title="Leave channel">
        <i class="bi bi-box-arrow-left me-1"></i>Leave
      </button>
    </div>`;
}

function leaveChannel(){
  currentChat = null;
  q("#chatWindow").innerHTML = `<div class="d-flex flex-column align-items-center justify-content-center text-center" style="height:100%;">
      <i class="bi bi-chat-dots fs-1 mb-2" style="color:rgba(51, 204, 51, 0.8)"></i>
      <div class="fw-semibold">Left channel</div>
      <div class="small">Select a channel or peer to continue chatting</div>
    </div>`;
}

async function sendMessage(){
  let msg = q("#messageInput").value.trim();
  if(!msg) return;
  if(!currentChat){ addNotification("Select chat"); return; }

  if(currentChat.type==="p2p"){
    let win = q("#chatWindow");
    let wrapper = document.createElement("div");
    wrapper.className = "d-flex mb-2";
    wrapper.innerHTML = `
      <div class="d-flex ms-auto flex-column align-items-end" style="max-width:72%;">
        <div class="small mb-1">You <i class="bi bi-clock-history ms-1" title="sending"></i></div>
        <div class="px-3 py-2 rounded-3 text-white msg-me" style="background:linear-gradient(135deg,var(--accent),#9e85ff);box-shadow:none;">
          ${escapeHtml(msg)}
        </div>
      </div>`;
    win.appendChild(wrapper);
    win.scrollTop = win.scrollHeight;

    await apiPOST("/send-peer",{ip:currentChat.ip,port:currentChat.port,message:msg});
  } 
  else if(currentChat.type==="channel"){
    if(!myId) await fetchMyId();
    await apiPOST("http://127.0.0.1:9000/post-channel", {
      name: currentChat.name,
      sender: myId || "me",
      msg: msg
    });
  }
  q("#messageInput").value="";
}

async function loadChannelMessages(name){
  let r = await apiPOST("http://127.0.0.1:9000/channel-history", {name});
  let win = q("#chatWindow");
  win.innerHTML="";
  (r||[]).forEach(m=>{
    win.innerHTML += `<div><small>${escapeHtml(m.sender)}</small>: ${escapeHtml(m.msg)}</div>`;
  });
  win.scrollTop = win.scrollHeight;
}

q("#btnRefresh").addEventListener("click",()=>refreshAll());
q("#btnSend").addEventListener("click",sendMessage);
q("#btnBroadcast").addEventListener("click",broadcastMessage);

document.addEventListener("DOMContentLoaded", ()=>{
  const btn = q("#btnCreateChannel");
  const input = q("#createChannelInput");

  if(btn && input){
    btn.addEventListener("click", async (ev)=>{
      ev.preventDefault(); // avoid form auto-submit if inside a form
      const name = (input.value || "").trim();
      if(!name) { addNotification("Channel name empty"); return; }
      let resp = await apiPOST("http://127.0.0.1:9000/create-channel", { name });
      if(resp && (resp.status === "ok" || resp.status === "created")){
        addNotification("Channel created: " + name);
        input.value = ""; // clear after success
        refreshChannels();
      } else {
        addNotification("Create channel failed");
      }
    });
  }
});


function refreshAll(){
  if(currentChat && currentChat.type==="channel"){
    loadChannelMessages(currentChat.name);
  }
  refreshOnlinePeers();
  refreshPending();
  refreshConnected();
  if(currentChat && currentChat.type==="channel"){
    loadChannelMessages(currentChat.name);
  } else {
      refreshMessages();
  }
  refreshChannels();
}

fetchMyId().then(()=>{
  refreshAll();
  setInterval(refreshAll,REFRESH_INTERVAL);
});
