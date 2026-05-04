document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const chatMessages = document.getElementById('chat-messages');
    const sendButton = document.getElementById('send-button');
    const themeToggle = document.getElementById('theme-toggle');
    const moonIcon = document.getElementById('moon-icon');
    const sunIcon = document.getElementById('sun-icon');
    
    // Tab Elements
    const tabChat = document.getElementById('tab-chat');
    const tabDashboard = document.getElementById('tab-dashboard');
    const viewChat = document.getElementById('view-chat');
    const viewDashboard = document.getElementById('view-dashboard');

    let chartsLoaded = false;
    let typeChartInstance = null;
    let priorityChartInstance = null;

    // Prompt Chips Logic
    document.querySelectorAll('.chip').forEach(chip => {
        chip.addEventListener('click', () => {
            userInput.value = chip.innerText;
            chatForm.dispatchEvent(new Event('submit'));
        });
    });

    // Theme Toggle Logic
    themeToggle.addEventListener('click', () => {
        document.body.classList.toggle('dark-theme');
        const isDark = document.body.classList.contains('dark-theme');
        moonIcon.style.display = isDark ? 'none' : 'block';
        sunIcon.style.display = isDark ? 'block' : 'none';
        
        // Update charts if they exist
        if (chartsLoaded) {
            const textColor = isDark ? '#f8fafc' : '#1e293b';
            if(typeChartInstance) {
                typeChartInstance.options.plugins.legend.labels.color = textColor;
                typeChartInstance.options.scales.x.ticks.color = textColor;
                typeChartInstance.options.scales.y.ticks.color = textColor;
                typeChartInstance.update();
            }
            if(priorityChartInstance) {
                priorityChartInstance.options.plugins.legend.labels.color = textColor;
                priorityChartInstance.update();
            }
        }
    });

    // Tab Switching Logic
    tabChat.addEventListener('click', () => {
        tabChat.classList.add('active');
        tabDashboard.classList.remove('active');
        viewChat.style.display = 'flex';
        viewDashboard.style.display = 'none';
    });

    tabDashboard.addEventListener('click', () => {
        tabDashboard.classList.add('active');
        tabChat.classList.remove('active');
        viewChat.style.display = 'none';
        viewDashboard.style.display = 'block';
        
        if (!chartsLoaded) {
            loadDashboardData();
        }
    });

    // Load Dashboard Data via API
    async function loadDashboardData() {
        try {
            const res = await fetch('/api/analytics');
            const data = await res.json();

            if (data.error) throw new Error(data.error);

            document.getElementById('total-tickets-val').innerText = data.total_tickets.toLocaleString();

            const isDark = document.body.classList.contains('dark-theme');
            const textColor = isDark ? '#f8fafc' : '#1e293b';

            // Chart Colors
            const colors = ['#0f4c81', '#3b82f6', '#10b981', '#f59e0b', '#ef4444'];

            // Type Bar Chart
            const typeCtx = document.getElementById('typeChart').getContext('2d');
            typeChartInstance = new Chart(typeCtx, {
                type: 'bar',
                data: {
                    labels: data.type_data.map(d => d.label),
                    datasets: [{
                        label: 'Tickets',
                        data: data.type_data.map(d => d.value),
                        backgroundColor: colors[0],
                        borderRadius: 4
                    }]
                },
                options: {
                    responsive: true,
                    plugins: { legend: { display: false } },
                    scales: {
                        y: { beginAtZero: true, ticks: { color: textColor } },
                        x: { ticks: { color: textColor } }
                    }
                }
            });

            // Priority Pie Chart
            const prioCtx = document.getElementById('priorityChart').getContext('2d');
            priorityChartInstance = new Chart(prioCtx, {
                type: 'doughnut',
                data: {
                    labels: data.priority_data.map(d => d.label),
                    datasets: [{
                        data: data.priority_data.map(d => d.value),
                        backgroundColor: ['#ef4444', '#f59e0b', '#3b82f6', '#10b981'],
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: { position: 'right', labels: { color: textColor } }
                    }
                }
            });

            chartsLoaded = true;

        } catch (err) {
            document.getElementById('total-tickets-val').innerText = 'Error';
            console.error("Dashboard error:", err);
        }
    }


    // Chat Logic
    const scrollToBottom = () => {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    };

    const getTimeString = () => {
        const now = new Date();
        return now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    };

    const addUserMessage = (text) => {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message user-message';
        messageDiv.innerHTML = `
            <div class="message-content">${text}</div>
            <div class="message-timestamp">${getTimeString()}</div>
        `;
        chatMessages.appendChild(messageDiv);
        scrollToBottom();
    };

    const formatBotContent = (text) => {
        // Render Generative UI components
        const uiMatch = text.match(/<UI_COMPONENT:\s*(\{.*?\})\s*>/);
        let uiHtml = '';
        if (uiMatch) {
            try {
                const uiData = JSON.parse(uiMatch[1]);
                if (uiData.type === 'escalation_form') {
                    uiHtml = `
                        <div class="gen-ui-card">
                            <h4>⚠️ Escalation Ticket Drafted</h4>
                            <p><strong>Issue:</strong> ${uiData.data.issue_summary}</p>
                            <p><strong>Steps Taken:</strong> ${uiData.data.steps}</p>
                            <button class="gen-ui-btn" onclick="this.innerHTML='✅ Ticket Submitted'; this.disabled=true;">Submit Ticket to IT Support</button>
                        </div>
                    `;
                }
            } catch (e) { console.error("Error parsing UI Component", e); }
            text = text.replace(uiMatch[0], ''); // Remove raw tag from text
        }

        let html = marked.parse(text);
        html = html.replace(/\[Source: (.*?)\]/g, '<span class="citation" title="SOP Reference">📄 $1</span>');
        html = html.replace(/\[Ticket ID: (.*?)\]/g, '<span class="citation" title="Historical Ticket">🎫 $1</span>');
        return html + uiHtml;
    };

    const addBotMessage = (text) => {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message bot-message';
        messageDiv.innerHTML = `
            <div class="message-content">${formatBotContent(text)}</div>
            <div class="message-timestamp">${getTimeString()}</div>
        `;
        chatMessages.appendChild(messageDiv);
        scrollToBottom();
    };

    const addStatusMessage = (text) => {
        const statusDiv = document.createElement('div');
        statusDiv.className = 'status-msg';
        statusDiv.innerText = text;
        chatMessages.appendChild(statusDiv);
        scrollToBottom();
        return statusDiv;
    };

    const showTypingIndicator = () => {
        const indicator = document.createElement('div');
        indicator.className = 'typing-indicator';
        indicator.id = 'typing-indicator';
        indicator.innerHTML = `
            <div class="dot"></div>
            <div class="dot"></div>
            <div class="dot"></div>
        `;
        chatMessages.appendChild(indicator);
        scrollToBottom();
    };

    const removeTypingIndicator = () => {
        const indicator = document.getElementById('typing-indicator');
        if (indicator) indicator.remove();
    };

    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const message = userInput.value.trim();
        if (!message) return;

        userInput.value = '';
        userInput.disabled = true;
        sendButton.disabled = true;
        
        addUserMessage(message);
        showTypingIndicator();

        let statusElements = [];

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message })
            });

            if (!response.ok) throw new Error("Network response was not ok");

            const reader = response.body.getReader();
            const decoder = new TextDecoder('utf-8');
            let done = false;
            let buffer = '';

            while (!done) {
                const { value, done: readerDone } = await reader.read();
                done = readerDone;
                if (value) {
                    buffer += decoder.decode(value, { stream: true });
                    const lines = buffer.split('\n\n');
                    buffer = lines.pop(); 

                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            const dataStr = line.substring(6);
                            try {
                                const data = JSON.parse(dataStr);
                                
                                if (data.type === 'status') {
                                    removeTypingIndicator();
                                    let sElem = addStatusMessage(data.msg);
                                    statusElements.push(sElem);
                                    showTypingIndicator();
                                } else if (data.type === 'final') {
                                    removeTypingIndicator();
                                    statusElements.forEach(el => el.remove());
                                    addBotMessage(data.msg);
                                } else if (data.type === 'error') {
                                    removeTypingIndicator();
                                    addBotMessage(`⚠️ Error: ${data.msg}`);
                                }
                            } catch (err) {
                                console.error("Error parsing stream data", err);
                            }
                        }
                    }
                }
            }
        } catch (error) {
            removeTypingIndicator();
            addBotMessage('🔌 Network error: Could not connect to the server.');
        } finally {
            removeTypingIndicator();
            userInput.disabled = false;
            sendButton.disabled = false;
            userInput.focus();
        }
    });
});
