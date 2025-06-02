// frontend/socketManager.js
let socket;
const listeners = {}; // เก็บ callback functions สำหรับแต่ละ event type

export function connect(roomId) {
    if (socket && socket.readyState === WebSocket.OPEN) {
        console.warn("WebSocket already connected.");
        return;
    }
    socket = new WebSocket(`ws://localhost:5050/ws/${roomId}`);

    socket.onopen = () => {
        console.log(`WebSocket connected to room: ${roomId}`);
        // ✅ สำคัญ: เมื่อ WS เปิดแล้ว ให้แจ้ง Backend ว่า Client พร้อมแล้ว
        emit('client_ready', { room_id: roomId }); // ส่ง event 'client_ready'
        if (listeners['connected']) listeners['connected'].forEach(fn => fn());
    };

  socket.onmessage = (event) => {
    console.log("[WebSocket] Raw message received:", event.data); // ต้องเห็น
    const message = JSON.parse(event.data);
    console.log("[WebSocket] Parsed message:", message); // ต้องเห็น
    const eventName = message.event;
    const data = message.data;

    if (listeners[eventName]) {
      console.log(`[WebSocket] Triggering listeners for event: ${eventName}`); // ต้องเห็น
      listeners[eventName].forEach((fn) => fn(data));
    } else {
      console.warn(`[WebSocket] No listener for event: ${eventName}`, data);
    }
  };

  socket.onclose = (event) => {
    console.log("WebSocket disconnected:", event);
    if (listeners["disconnected"])
      listeners["disconnected"].forEach((fn) => fn(event));
  };

  socket.onerror = (error) => {
    console.error("WebSocket error:", error);
    if (listeners["error"]) listeners["error"].forEach((fn) => fn(error));
  };
}

// ไม่จำเป็นต้องใช้ emit ถ้าใช้แค่รับ update จาก server อย่างเดียว
// แต่ถ้ามี event ที่ client จะส่งไปให้ server ก็เก็บไว้
export function emit(event, data) {
  if (socket && socket.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify({ event, data }));
  } else {
    console.warn("WebSocket not open. Cannot emit event:", event);
  }
}

// ฟังก์ชันสำหรับลงทะเบียน Listener
export function on(event, fn) {
  if (!listeners[event]) listeners[event] = [];
  listeners[event].push(fn);
}

// ฟังก์ชันสำหรับยกเลิกการลงทะเบียน Listener (สำคัญสำหรับ Clean-up)
export function off(event, fn) {
  if (listeners[event]) {
    listeners[event] = listeners[event].filter((callback) => callback !== fn);
  }
}

// ฟังก์ชันสำหรับปิดการเชื่อมต่อ WebSocket
export function disconnect() {
  if (socket) {
    socket.close();
    socket = null;
  }
}

export function getSocketReadyState() {
    if (socket) {
        return socket.readyState; // 0=CONNECTING, 1=OPEN, 2=CLOSING, 3=CLOSED
    }
    return null;
}