function loadSample() {
    document.getElementById("inputText").value = `Hello everyone, myself Muskan, studying in class 8th B section from Christ Public School. 
I am 13 years old. I live with my family. There are 3 people in my family, me, my mother and my father.
One special thing about my family is that they are very kind hearted to everyone and soft spoken. One thing I really enjoy is play, playing cricket and taking wickets.
A fun fact about me is that I see in mirror and talk by myself. One thing people don't know about me is that I once stole a toy from one of my cousin.
 My favorite subject is science because it is very interesting. Through science I can explore the whole world and make the discoveries and improve the lives of others. 
Thank you for listening.`;
}

function openFile() { document.getElementById("fileInput").click(); }

function loadFile(event) {
    const file = event.target.files[0];
    if (!file) return;
    if (file.name.endsWith(".txt")) {
        const reader = new FileReader();
        reader.onload = e => document.getElementById("inputText").value = e.target.result;
        reader.readAsText(file);
    } else alert("Please upload a .txt file only.");
}

async function scoreText() {
    const text = document.getElementById("inputText").value.trim();
    if (!text) return alert("Please paste text or upload a file.");
    document.getElementById("loading").classList.remove("hidden");
    document.getElementById("result").classList.add("hidden");

    const response = await fetch("/score", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text })
    });

    const data = await response.json();
    document.getElementById("loading").classList.add("hidden");
    renderDashboard(data);
}

function renderDashboard(data) {
    const div = document.getElementById("result");
    div.classList.remove("hidden");

    const grammarCriterion = data.per_criterion.find(c => c.criterion === "Language & Grammar");
    const clarityCriterion = data.per_criterion.find(c => c.criterion.startsWith("Clarity"));
    const ttr = grammarCriterion?.components.TTR ?? "N/A";
    const filler_count = clarityCriterion?.components["Filler count"] ?? "N/A";
    const filler_pct = clarityCriterion?.components["Filler %"] ?? "N/A";

    div.innerHTML = `
    <div class="grid grid-cols-2 md:grid-cols-2 gap-4 mb-4">
        <div class="bg-gradient-to-r from-indigo-500 to-purple-500 text-white p-4 rounded-2xl shadow-lg text-center">
            <div class="text-lg font-semibold">Words</div>
            <div class="text-2xl font-bold">${data.word_count}</div>
        </div>
        <div class="bg-gradient-to-r from-purple-500 to-pink-500 text-white p-4 rounded-2xl shadow-lg text-center">
            <div class="text-lg font-semibold">Sentences</div>
            <div class="text-2xl font-bold">${data.sentence_count}</div>
        </div>
        <div class="bg-gradient-to-r from-green-400 to-teal-500 text-white p-4 rounded-2xl shadow-lg text-center">
            <div class="text-lg font-semibold">TTR</div>
            <div class="text-2xl font-bold">${ttr}</div>
        </div>
        <div class="bg-gradient-to-r from-yellow-400 to-orange-500 text-white p-4 rounded-2xl shadow-lg text-center">
            <div class="text-lg font-semibold">Filler Words</div>
            <div class="text-2xl font-bold">${filler_count} (${filler_pct}%)</div>
        </div>
    </div>

    <div class="flex flex-col md:flex-row gap-4">
        <div class="md:w-1/2 bg-white p-4 rounded-2xl shadow-lg flex flex-col items-center">
            <canvas id="scorePie" class="w-48 h-48"></canvas>
            <div class="text-3xl font-bold mt-2">${data.overall_score}%</div>
        </div>

        <div class="md:w-1/2 flex flex-col gap-3">
            ${data.per_criterion.map((c, idx) => {
                const percentage = ((c.score / c.max_score) * 100).toFixed(1);
                return `
                <div class="p-4 bg-white rounded-2xl shadow hover:shadow-lg transition cursor-pointer" onclick="toggleDetails('details${idx}')">
                    <div class="flex justify-between items-center">
                        <h3 class="font-semibold text-gray-800 truncate">${c.criterion}</h3>
                        <span class="font-bold text-indigo-600">${c.score}/${c.max_score}</span>
                    </div>
                    <div class="w-full bg-gray-200 rounded-full h-3 overflow-hidden mt-2">
                        <div class="bg-gradient-to-r from-green-400 to-blue-500 h-3 rounded-full" style="width:${percentage}%"></div>
                    </div>
                    <div id="details${idx}" class="mt-2 text-gray-500 text-sm hidden break-words">${c.feedback}</div>
                </div>`;
            }).join('')}
        </div>
    </div>
    `;

    const canvas = document.getElementById('scorePie');
    if (canvas) {
        const ctx = canvas.getContext('2d');
        if (window.scorePieInstance) window.scorePieInstance.destroy();
        window.scorePieInstance = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Score', 'Remaining'],
                datasets: [{
                    data: [data.overall_score, 100 - data.overall_score],
                    backgroundColor: ['#4f46e5', '#e5e7eb'],
                    borderWidth: 0
                }]
            },
            options: { cutout: '70%', plugins: { legend: { display: false }, tooltip: { enabled: true } }, responsive: true }
        });
    }

    window.latestScoreData = data;
}

function toggleDetails(id) {
    const el = document.getElementById(id);
    if (el) el.classList.toggle('hidden');
}
