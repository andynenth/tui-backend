// socketManager.js
let socket;
const listeners = {};

export function connect(roomId) {
    socket = new WebSocket(`ws://localhost:5050/ws/${roomId}`);
    socket.onmessage = (event) => {
        const { event: name, data } = JSON.parse(event.data);
        if (listeners[name]) listeners[name].forEach(fn => fn(data));
    };
}
export function emit(event, data) {
    socket.send(JSON.stringify({ event, data }));
}
export function on(event, fn) {
    if (!listeners[event]) listeners[event] = [];
    listeners[event].push(fn);
}
