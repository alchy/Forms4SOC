/**
 * Forms4SOC – hlavní JavaScript modul
 *
 * Pomocné utility pro REST API volání.
 * Specifická logika jednotlivých stránek je inline ve Jinja2 šablonách.
 */

/**
 * Provede authenticated fetch request.
 * Cookie se posílá automaticky (same-origin credentials).
 *
 * @param {string} url
 * @param {RequestInit} options
 * @returns {Promise<Response>}
 */
async function apiFetch(url, options = {}) {
    const defaults = {
        credentials: 'same-origin',
        headers: {
            'Content-Type': 'application/json',
            ...options.headers,
        },
    };
    const response = await fetch(url, {...defaults, ...options});

    // Automatické přesměrování na login při vypršení session
    if (response.status === 401) {
        window.location.href = '/login';
        return response;
    }

    return response;
}

/**
 * Vrátí CSS třídu pro badge dle severity.
 * @param {string} severity
 * @returns {string}
 */
function severityBadgeClass(severity) {
    const map = {
        critical: 'severity-critical',
        high: 'severity-high',
        medium: 'severity-medium',
        low: 'severity-low',
    };
    return map[severity] ?? 'bg-secondary';
}
