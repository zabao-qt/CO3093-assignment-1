<!-- # HCMC University of Technology  
### Faculty of Computer Science & Engineering  

---

## Course: Computer Network  
### Assignment 1 – Implement HTTP Server and Chat Application  

**October 2, 2025**

---

### Goal  
The objective of this assignment is the application of major components in a computer network, for example, the client-server paradigm, the peer-to-peer paradigm, and network programming.

---

### Content  
In detail, students will practice with three major modules: the client-server HTTP communication, the peer-to-peer based chat application, and the TCP/IP connection, which includes:

- Client processes and server processes  
- Multiple peer processes connecting together  
- TCP socket network programming  

Besides, students will practice the design and implementation of a simple peer-to-peer protocol via TCP/IP.

---

### Result  
After this assignment, students can partly understand the principles of a computer network system.  
They can understand and design the roles of different types of processes, i.e., the server process, client process, and tracker peer process in a network communication.

--- -->

# 🌐✨ **WeApRous – Hybrid Chat Application**

<p align="center">
  <strong>Computer Networks – CO3093 / CO3094</strong><br>
  <em>HCMC University of Technology (VNU-HCM)</em>
</p>

---

## 🚀 Overview

**WeApRous** is a **hybrid chat application** built completely from scratch using **raw TCP sockets and a self-implemented HTTP framework** (no Flask, no Django, no Express).
The system combines **Client–Server** and **Peer‑to‑Peer (P2P)** networking models into a single, coherent real‑time chat platform.

> 💡 This project demonstrates deep understanding of **network protocols**, **socket programming**, **HTTP**, **cookie-based authentication**, and **distributed system architecture**.

---

## 🧠 Key Concepts Demonstrated

* 🔐 **HTTP Cookie-based Authentication** (custom implementation)
* 🌍 **Client–Server Architecture** (Tracker & Channel Backend)
* 🔗 **Peer‑to‑Peer Communication** (direct TCP, no relay)
* 🔄 **Hybrid Networking Model**
* ⚙️ **Concurrent Socket Programming** (multi-threaded)

---

## 🏗️ System Architecture

```text
Browser UI
   │
   ▼
WebApp (HTTP Server + REST API)
   │        │
   │        ├── Tracker Backend (Port 9000)
   │        │     • Peer registry
   │        │     • Channel management
   │        │     • Channel message history
   │        │
   │        └── Peer Node (TCP Server)
   │              • Direct P2P chat
   │              • Broadcast messages
   │              • Connection handshake
   ▼
Other Peer Nodes (TCP)
```

🧩 **Components**:

| Component             | Description                                             |
| --------------------- | ------------------------------------------------------- |
| **Tracker Backend**   | Central server managing peers & channels                |
| **WebApp (WeApRous)** | UI + REST controller bridging browser ↔ backend ↔ peers |
| **Peer Node**         | Independent TCP server per user for P2P messaging       |
| **Browser UI**        | Interactive chat interface                              |

---

## 🔐 Authentication Flow (HTTP Cookies)

1. User accesses `/login`
2. Server validates credentials

   ```
   username = admin
   password = password
   ```
3. On success:

   * HTTP `302 Found`
   * `Set-Cookie: auth=true`
4. Access to `/index.html` is **blocked** without valid cookie

---

## 💬 Chat Features

### 🔗 Peer‑to‑Peer Chat (TCP)

* Direct socket connection between peers
* No server relay after handshake
* Real‑time message delivery
* UI shows **sent & received messages** distinctly

### 📢 Broadcast Messaging

* One‑to‑many messaging over TCP
* Delivered to all connected peers
* Highlighted UI bubbles + notifications

### 🧵 Channel Chat (Client–Server)

* Create & join channels
* Messages stored centrally (JSON persistence)
* Auto‑load history on channel switch
* Sender displayed as `IP:PORT`

---

## 🔄 End‑to‑End Workflow

### 1️⃣ Start the system

```bash
# Tracker backend
python start_backend.py --server-ip 0.0.0.0 --server-port 9000

# ChatApp instances (example)
python start_chatapp.py --ui-port 8001 --peer-port 7001 --my-ip 127.0.0.1
python start_chatapp.py --ui-port 8002 --peer-port 7002 --my-ip 127.0.0.1
```

Each ChatApp instance automatically:

* Registers itself to the tracker
* Starts its own PeerNode (TCP server)
* Launches the Web UI

---

### 2️⃣ Login

Open browser:

```
http://127.0.0.1:8001/login
```

✔ Successful login → cookie stored → redirected to chat UI
❌ Invalid login → `401 Unauthorized`

---

### 3️⃣ Discover & Connect Peers

* UI fetches peer list from tracker
* Click **Connect** → TCP handshake
* Peer receives request → **Accept / Deny**
* On accept → direct P2P channel established

---

### 4️⃣ Chat!

* 💬 Select a peer → P2P chat
* 📢 Broadcast to all connected peers
* 🧵 Join a channel → server-based chat


---

---

## 📡 REST API

| Method | Endpoint           | Description                      |
| ------ | ------------------ | -------------------------------- |
| GET    | `/login`           | Login page                       |
| POST   | `/login`           | Authenticate & set cookie        |
| GET    | `/whoami`          | Return current peer ID           |
| GET    | `/get-list`        | Fetch online peers from tracker  |
| POST   | `/connect-peer`    | Send P2P connection request      |
| POST   | `/accept-request`  | Accept incoming P2P request      |
| POST   | `/deny-request`    | Deny incoming P2P request        |
| POST   | `/disconnect-peer` | Remove connected peer            |
| POST   | `/send-peer`       | Send direct P2P message          |
| POST   | `/broadcast-peer`  | Broadcast message to peers       |
| GET    | `/get-pending`     | List pending connection requests |
| GET    | `/get-connected`   | List connected peers             |
| GET    | `/get-messages`    | Retrieve local P2P message log   |

---