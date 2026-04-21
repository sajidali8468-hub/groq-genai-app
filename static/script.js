async function sendQuery() {
    const userInput = document.getElementById("userInput");
    const output = document.getElementById("output");
    const latency = document.getElementById("latency");
    const button = document.querySelector("button");

    const prompt = userInput.value.trim();

    if (!prompt) {
        latency.textContent = "Please enter a technical prompt.";
        return;
    }

    button.disabled = true;
    button.classList.add("opacity-60", "cursor-not-allowed");
    latency.textContent = "Generating...";
    output.classList.remove("hidden");
    output.innerHTML = '<p class="text-gray-500">Processing request...</p>';

    try {
        const response = await fetch("/generate", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ user_input: prompt })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Request failed.");
        }

        output.innerHTML = `
            <div class="prose max-w-none">
                <h2 class="text-2xl font-semibold mb-4">Generated Output</h2>
                <div id="generatedText" class="whitespace-pre-wrap text-gray-800 leading-7"></div>
            </div>
        `;
        document.getElementById("generatedText").textContent = data.output;
        latency.textContent = `Completed in ${data.latency}`;
    } catch (error) {
        output.innerHTML = '<p class="text-red-500 font-medium">Error: <span id="errorText"></span></p>';
        document.getElementById("errorText").textContent = error.message;
        latency.textContent = "Failed";
    } finally {
        button.disabled = false;
        button.classList.remove("opacity-60", "cursor-not-allowed");
    }
}
