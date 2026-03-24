import React, { useEffect, useState, useRef, useCallback } from "react";
import io from "socket.io-client";
import "./App.css";

const SOCKET_URL = "http://localhost:5000";
const socket = io(SOCKET_URL, { autoConnect: true });

function ts() {
  return new Date().toTimeString().slice(0, 8);
}

export default function App() {
  // Which role is this browser tab: null | 'server' | 'client'
  const [role, setRole] = useState(null);
  const [seed, setSeed] = useState("opensesame");
  const [keyHex, setKeyHex] = useState("");
  const [ready, setReady] = useState(false);

  // Unified chat: { id, text, from: 'server'|'client', ts }
  const [messages, setMessages] = useState([]);
  const [packets, setPackets]   = useState([]);
  const [input, setInput]       = useState("");

  const feedRef    = useRef(null);
  const trafficRef = useRef(null);
  const sidRef     = useRef(null);   // stable socket SID for this role

  // Auto-scroll
  useEffect(() => {
    if (feedRef.current)
      feedRef.current.scrollTop = feedRef.current.scrollHeight;
  }, [messages]);
  useEffect(() => {
    if (trafficRef.current)
      trafficRef.current.scrollTop = trafficRef.current.scrollHeight;
  }, [packets]);

  // ── Socket listeners ──
  useEffect(() => {
    socket.on("key_ready", (data) => {
      setKeyHex(data.key_hex);
      setReady(true);
    });

    // A new plaintext message arrived for this role
    socket.on("receive_message", (data) => {
      setMessages((prev) => [
        ...prev,
        {
          id:   Date.now() + Math.random(),
          text: data.message,
          from: data.from_role,   // who sent it
          ts:   ts(),
        },
      ]);
    });

    // Raw cipher broadcast — bottom panel
    socket.on("receive_encrypted", (data) => {
      setPackets((prev) => [
        ...prev,
        {
          id:     Date.now() + Math.random(),
          cipher: data.cipher,
          from:   data.from_role,
          ts:     ts(),
          bytes:  data.cipher.length / 2,
          blocks: Math.ceil(data.cipher.length / 32),
        },
      ]);
    });

    return () => {
      socket.off("key_ready");
      socket.off("receive_message");
      socket.off("receive_encrypted");
    };
  }, []);

  // ── Pick a role ──
  const pickRole = useCallback((r) => {
    setRole(r);
    sidRef.current = `${r}-${Math.random().toString(36).slice(2, 7)}`;
    socket.emit("register", { sid: sidRef.current, role: r });
  }, []);

  // ── Init shared key ──
  const initKey = useCallback(() => {
    if (!seed.trim() || !role) return;
    setReady(false);
    setKeyHex("");
    setMessages([]);
    setPackets([]);
    socket.emit("init_key", { sid: sidRef.current, seed });
  }, [seed, role]);

  // ── Send a message ──
  const sendMessage = useCallback(() => {
    const msg = input.trim();
    if (!msg || !ready || !role) return;
    setInput("");

    // Optimistically add own message to feed
    setMessages((prev) => [
      ...prev,
      {
        id:   Date.now() + Math.random(),
        text: msg,
        from: role,
        ts:   ts(),
      },
    ]);

    socket.emit("send_message", {
      sid:     sidRef.current,
      role:    role,
      message: msg,
    });
  }, [input, ready, role]);

  const handleKey = (e) => { if (e.key === "Enter") sendMessage(); };

  const otherRole = role === "server" ? "client" : "server";

  // ── Role picker screen ──
  if (!role) {
    return (
      <div className="app" style={{ justifyContent: "center", alignItems: "center", gap: 24 }}>
        <div className="topbar-title" style={{ textAlign: "center", fontSize: "1rem" }}>
          CRYPTOGRAPHIC COMMS
        </div>
        <div style={{ fontSize: "0.65rem", color: "#4a7a9b", letterSpacing: "0.1em" }}>
          OPEN THIS PAGE IN TWO TABS — PICK A ROLE IN EACH
        </div>
        <div style={{ display: "flex", gap: 16 }}>
          <button className="btn-role server" onClick={() => pickRole("server")}>
            SERVER
          </button>
          <button className="btn-role client" onClick={() => pickRole("client")}>
            CLIENT
          </button>
        </div>
      </div>
    );
  }

  // ── Main UI ──
  return (
    <div className="app">

      {/* TOP BAR */}
      <div className="topbar">
        <span className="topbar-title">CRYPTOGRAPHIC COMMS</span>

        <div className={`role-badge ${role}`}>
          YOU ARE: {role.toUpperCase()}
        </div>

        <div className="topbar-seed">
          <label>SHARED SEED</label>
          <input
            value={seed}
            onChange={(e) => setSeed(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && initKey()}
            placeholder="shared seed phrase..."
          />
          <button className="btn-init" onClick={initKey}>
            INIT KEY
          </button>
          {keyHex && (
            <div className="key-pill" title={`Full key: ${keyHex}`}>
              KEY: {keyHex.slice(0, 20)}…
            </div>
          )}
        </div>
      </div>

      {/* CHAT SECTION */}
      <div className="chat-section">
        <div className="chat-header">
          <div className={`chat-header-dot ${role}`} />
          <span className={`chat-header-label ${role}`}>
            {role.toUpperCase()} ↔ {otherRole.toUpperCase()}
          </span>
          <span className="chat-header-sub">
            {ready
              ? "END-TO-END ENCRYPTED · MANDELBROT KEY ACTIVE"
              : "ENTER SEED AND CLICK INIT KEY"}
          </span>
        </div>

        <div className="msg-feed" ref={feedRef}>
          {messages.length === 0 ? (
            <div className="empty-feed">
              <span className="empty-icon">🔐</span>
              <span className="empty-text">
                {ready
                  ? "NO MESSAGES YET — TYPE BELOW TO START"
                  : "INIT KEY TO BEGIN ENCRYPTED CHAT"}
              </span>
            </div>
          ) : (
            messages.map((m) => {
              const mine = m.from === role;
              return (
                <div key={m.id} className={`msg-row ${mine ? "mine" : "theirs"}`}>
                  <span className={`msg-sender ${m.from}`}>
                    {m.from.toUpperCase()}
                  </span>
                  <div className="msg-bubble">{m.text}</div>
                  <span className="msg-meta">{m.ts}</span>
                </div>
              );
            })
          )}
        </div>

        <div className="input-row">
          <input
            className={`msg-input ${role}`}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKey}
            placeholder={
              !ready
                ? "Init key first..."
                : `${role === "server" ? "Server" : "Client"} — type a message...`
            }
            disabled={!ready}
          />
          <button
            className={`btn-send ${role}`}
            onClick={sendMessage}
            disabled={!ready || !input.trim()}
          >
            SEND
          </button>
        </div>
      </div>

      {/* BOTTOM: RAW WIRE TRAFFIC */}
      <div className="traffic-section">
        <div className="traffic-header">
          <div className="blink-dot" />
          <span className="traffic-title">RAW SOCKET TRAFFIC — INTERCEPTED CIPHERTEXT</span>
          <span className="traffic-count">
            {packets.length} packet{packets.length !== 1 ? "s" : ""} captured
          </span>
        </div>

        <div className="traffic-body" ref={trafficRef}>
          {packets.length === 0 ? (
            <div className="traffic-empty">
              <span className="empty-icon">🔴</span>
              <span className="empty-text">NO PACKETS YET — SEND A MESSAGE</span>
            </div>
          ) : (
            packets.map((p) => (
              <div key={p.id} className="packet">
                <div className="packet-top">
                  <span className="pkt-badge">ENCRYPTED</span>
                  <span className="pkt-from">
                    from: {p.from.toUpperCase()} · event: receive_encrypted
                  </span>
                  <span className="pkt-ts">{p.ts}</span>
                </div>
                <div className="cipher-hex">
                  {p.cipher.match(/.{1,64}/g).join("\n")}
                </div>
                <div className="pkt-footer">
                  {p.blocks} AES block{p.blocks !== 1 ? "s" : ""} · {p.bytes} bytes ·
                  CHM-chained · unreadable without shared Mandelbrot key
                </div>
              </div>
            ))
          )}
        </div>
      </div>

    </div>
  );
}