let url = "ws://${window.location.host}/ws/notification/";

const socket = new WebSocket(url);

socket.onmessage(function(e) {
    let data = JSON.parse(e.data);
    console.log(data);
    
    if (data.type === "notification") {
        let notification = $("#notifications");
        
        if (notification.length < 2) {
            // notification.insertAdjacentHTML("beforeend", data.message)
            notification.append(`
              <span class="position-absolute top-0 start-100 translate-middle p-2 bg-danger border border-light rounded-circle">
                <span class="visually-hidden">New alerts</span>
              </span>
            `)
        }
    }
});

socket.onclose = function(e) {
    console.error("Websocket close unexpectedly!");
}