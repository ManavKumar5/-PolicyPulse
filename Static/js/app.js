async function fetchJSON(url, opts) {
  try {
    console.log("Fetching:", url, opts || "");
    const res = await fetch(url, opts);
    if (!res.ok) {
      const errText = await res.text();
      console.error("Server error:", res.status, errText);
      throw new Error(`HTTP ${res.status}: ${errText}`);
    }
    return res.json();
  } catch (err) {
    console.error("Network/Fetch error:", err);
    throw err;
  }
}

async function loadScans() {
  try {
    const tbody = document.querySelector("#scansTable tbody");
    tbody.innerHTML = "";
    const scans = await fetchJSON("/scans");
    scans.forEach(s => {
      const tr = document.createElement("tr");
      const d = new Date(s.timestamp * 1000);
      tr.innerHTML = `
        <td><a href="#" data-id="${s.id}" class="view-link">${s.id.slice(0, 8)}…</a></td>
        <td><span class="badge">${s.flags}</span></td>
        <td>${d.toLocaleString()}</td>
      `;
      tbody.appendChild(tr);
    });

    document.querySelectorAll(".view-link").forEach(a => {
      a.addEventListener("click", async e => {
        e.preventDefault();
        const id = a.getAttribute("data-id");
        try {
          const rep = await fetchJSON(`/reports/${id}`);
          showReport(rep);
        } catch (err) {
          alert("Failed to load report: " + err.message);
        }
      });
    });
  } catch (err) {
    console.error("Failed to load scans:", err);
    document.querySelector("#scansTable tbody").innerHTML =
      `<tr><td colspan="3" style="color:red;">Error loading scans: ${err.message}</td></tr>`;
  }
}

function showReport(rep) {
  document.getElementById("reportSection").hidden = false;
  document.getElementById("reportJson").textContent = JSON.stringify(rep, null, 2);
  const out = document.getElementById("highlighted");
  out.innerHTML = "";
  (rep.flags || []).forEach(f => {
    const div = document.createElement("div");
    div.className = "highlight";
    const matches = (f.matches || []).map(m =>
      `<span class="match">${m.rule_id}: ${m.description}</span>`
    ).join(" ");
    div.innerHTML = `<div>${matches}</div><div>${f.sentence}</div>`;
    out.appendChild(div);
  });
}

async function runScan() {
  const text = document.getElementById("scanText").value;
  const url = document.getElementById("scanUrl").value;
  const inbox = document.getElementById("scanInbox").value;
  const resEl = document.getElementById("scanResult");

  resEl.textContent = "Scanning…";
  console.log("Scan request payload:", { text, url, inbox });

  try {
    const payload = {};
    if (text) payload.text = text;
    if (url) payload.url = url;
    if (inbox) payload.inbox = inbox;

    const res = await fetchJSON("/scan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    console.log("Scan response:", res);
    resEl.textContent = `Scan ${res.scanId} completed. Flags found: ${res.flags_found}`;
    await loadScans();
  } catch (err) {
    console.error("Scan failed:", err);
    resEl.textContent = `Error: ${err.message}`;
    alert("Scan failed: " + err.message);
  }
}

document.getElementById("scanBtn").addEventListener("click", runScan);
loadScans().catch(console.error);
