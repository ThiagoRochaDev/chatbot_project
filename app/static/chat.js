async function sendMessage() {
    const input = document.getElementById("user-input");
    const message = input.value.trim();
    if (!message) return;

    const chatBox = document.getElementById("chat-box");

    // Exibe a mensagem do usuário
    chatBox.innerHTML += `<div class="user"><strong>Você:</strong> ${message}</div>`;

    // Envia a mensagem para o backend Flask
    const response = await fetch("/ask", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ message })
    });

    const data = await response.json();

    // Exibe a resposta do chatbot
    chatBox.innerHTML += `<div class="bot"><strong>Bot:</strong> ${data.answer}</div>`;
    chatBox.scrollTop = chatBox.scrollHeight;

    input.value = "";
}
