const headline = "Intelligence, redefined.";
const headlineElement = document.getElementById("typingHeadline");
const assistantPanel = document.getElementById("assistantPanel");
const counters = document.querySelectorAll(".counter");
const revealItems = document.querySelectorAll(".section-reveal");
const parallaxLayers = document.querySelectorAll(".parallax-layer");
let countersStarted = false;

function typeHeadline() {
    if (!headlineElement) {
        return;
    }

    headlineElement.textContent = "";
    let index = 0;

    const timer = window.setInterval(() => {
        headlineElement.textContent += headline[index];
        index += 1;

        if (index >= headline.length) {
            window.clearInterval(timer);
        }
    }, 58);
}

function addRipple(event) {
    const button = event.currentTarget;
    const ripple = document.createElement("span");
    const rect = button.getBoundingClientRect();

    ripple.className = "ripple";
    ripple.style.left = `${event.clientX - rect.left}px`;
    ripple.style.top = `${event.clientY - rect.top}px`;
    button.appendChild(ripple);

    window.setTimeout(() => ripple.remove(), 720);
}

function startAnalysis(event) {
    const button = event?.currentTarget;

    if (button) {
        addRipple(event);
        button.classList.add("is-loading");
        window.setTimeout(() => button.classList.remove("is-loading"), 650);
    }

    window.setTimeout(() => {
        document.getElementById("workspace").scrollIntoView({ behavior: "smooth", block: "start" });
        document.getElementById("askInput").focus({ preventScroll: true });
    }, 260);
}

function openAssistantPanel(event) {
    if (event) {
        addRipple(event);
    }

    assistantPanel.classList.add("is-open");
    assistantPanel.setAttribute("aria-hidden", "false");
}

function closeAssistantPanel() {
    assistantPanel.classList.remove("is-open");
    assistantPanel.setAttribute("aria-hidden", "true");
}

function animateCounter(counter) {
    const target = Number(counter.dataset.target);
    const duration = 1400;
    const start = performance.now();

    function update(now) {
        const progress = Math.min((now - start) / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        const value = Math.floor(target * eased);

        counter.textContent = value.toLocaleString();

        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }

    requestAnimationFrame(update);
}

const revealObserver = new IntersectionObserver(
    (entries) => {
        entries.forEach((entry) => {
            if (entry.isIntersecting) {
                entry.target.classList.add("is-visible");

                if (entry.target.id === "analytics" && !countersStarted) {
                    countersStarted = true;
                    counters.forEach(animateCounter);
                }
            }
        });
    },
    { threshold: 0.18 }
);

revealItems.forEach((item) => revealObserver.observe(item));

document.addEventListener("mousemove", (event) => {
    const x = (event.clientX / window.innerWidth - 0.5) * 2;
    const y = (event.clientY / window.innerHeight - 0.5) * 2;

    parallaxLayers.forEach((layer) => {
        const depth = Number(layer.dataset.depth || 10);
        layer.style.setProperty("--parallax-x", `${x * depth}px`);
        layer.style.setProperty("--parallax-y", `${y * depth}px`);
    });
});

document.getElementById("documentUpload").addEventListener("change", (event) => {
    const file = event.target.files[0];
    const status = document.getElementById("fileStatus");

    status.textContent = file ? `${file.name} attached` : "TXT, MD, CSV, JSON, or PDF context";
});

async function sendQuery(event) {
    event.preventDefault();

    const userInput = document.getElementById("userInput");
    const askInput = document.getElementById("askInput");
    const output = document.getElementById("output");
    const latency = document.getElementById("latency");
    const button = document.getElementById("generateButton");
    const promptParts = [userInput.value.trim(), askInput.value.trim()].filter(Boolean);
    const prompt = promptParts.join("\n\nQuestion:\n");

    addRipple({ currentTarget: button, clientX: button.getBoundingClientRect().left + 24, clientY: button.getBoundingClientRect().top + 24 });

    if (!prompt) {
        latency.textContent = "Please enter technical context or a question.";
        output.className = "output-empty";
        output.textContent = "Add technical context first, then generate a summary.";
        return;
    }

    button.disabled = true;
    button.classList.add("is-loading");
    latency.textContent = "Initializing intelligence...";
    output.className = "output-empty";
    output.textContent = "Analyzing inputs, extracting signal, and building executive summary...";

    try {
        const response = await fetch("/generate", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ user_input: prompt }),
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Request failed.");
        }

        output.className = "generated-text";
        output.textContent = data.output;
        latency.textContent = `Completed in ${data.latency}`;
    } catch (error) {
        output.className = "output-empty";
        output.textContent = `Error: ${error.message}`;
        latency.textContent = "Failed";
    } finally {
        button.disabled = false;
        button.classList.remove("is-loading");
    }
}

typeHeadline();
