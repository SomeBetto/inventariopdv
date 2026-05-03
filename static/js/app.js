let allProducts = [];
let currentEditingCode = null;
let html5QrCode = null;
let currentTab = 'inventory';

function changeTab(tab) {
    currentTab = tab;
    document.getElementById('tab-inventory').classList.toggle('active', tab === 'inventory');
    document.getElementById('tab-prices').classList.toggle('active', tab === 'prices');
    document.getElementById('tab-catalog').classList.toggle('active', tab === 'catalog');
    document.getElementById('tab-sales').classList.toggle('active', tab === 'sales');

    // Toggle specific UI options if needed
    document.getElementById('filterStock').style.display = tab === 'inventory' ? 'block' : 'none';
    
    document.getElementById('searchControls').style.display = tab === 'sales' ? 'none' : 'flex';
    document.getElementById('filterControls').style.display = tab === 'sales' ? 'none' : 'grid';
    document.getElementById('salesFilters').style.display = tab === 'sales' ? 'grid' : 'none';

    document.getElementById('masterSearch').value = '';
    document.getElementById('productsBody').innerHTML = ''; // Limpiar temporalmente
    loadData();
}

async function loadData() {
    try {
        if (currentTab === 'sales') {
            const timeRange = document.getElementById('filterTime').value;
            const groupBy = document.getElementById('filterGroup').value;
            const depto = document.getElementById('filterDeptSales').value;
            
            document.getElementById('productsBody').innerHTML = '<div style="text-align: center; color: var(--text-dim); padding: 2rem;">Cargando ventas...</div>';
            
            const res = await fetch('/api/sales/report', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ time_range: timeRange, group_by: groupBy, department: depto })
            });
            const report = await res.json();
            renderSalesCards(report, groupBy);
            return;
        }

        let endpoint = '/api/inventory';
        if (currentTab === 'prices') endpoint = '/api/prices';
        if (currentTab === 'catalog') endpoint = '/api/catalog';

        const res = await fetch(endpoint);
        allProducts = await res.json();
        updateDepts(allProducts);
        multiFilter(); // instead of renderMobileCards so filters apply immediately
    } catch (err) {
        showToast("Error al conectar ❌", "error");
    }
}

function updateDepts(products) {
    const depts = [...new Set(products.map(p => p.departamento))].sort();
    const select = document.getElementById('filterDept');
    const selectSales = document.getElementById('filterDeptSales');
    
    select.innerHTML = '<option value="">Todo el Local</option>';
    selectSales.innerHTML = '<option value="">Todos los Deptos</option>';
    
    depts.forEach(d => {
        const opt = document.createElement('option');
        opt.value = d; opt.textContent = d; select.appendChild(opt);
        
        const optSales = document.createElement('option');
        optSales.value = d; optSales.textContent = d; selectSales.appendChild(optSales);
    });
}

function renderMobileCards(products) {
    const container = document.getElementById('productsBody');
    container.innerHTML = '';
    products.forEach(p => {
        const card = document.createElement('div');
        card.className = 'product-card';

        const safeDesc = p.descripcion.replace(/'/g, "\\'");

        let statsHtml = '';

        if (currentTab === 'inventory') {
            statsHtml = `
                <div class="stat-group">
                    <div class="label">Stock Actual</div>
                    <div class="val stock">${p.inventario}</div>
                </div>
            `;
            card.onclick = () => openModal(p.codigo, safeDesc, p.inventario);
        } else if (currentTab === 'prices') {
            let ganancia = 0;
            if (p.p_costo > 0) { ganancia = ((p.precio - p.p_costo) / p.p_costo) * 100; }
            else if (p.precio > 0) { ganancia = 100; }

            statsHtml = `
                <div class="stat-group">
                    <div class="label">Precio V.</div>
                    <div class="val price">$${p.precio.toFixed(2)}</div>
                </div>
                <div class="stat-group" style="text-align: center;">
                    <div class="label">Ganancia</div>
                    <div class="val" style="color: #a78bfa;">${ganancia.toFixed(1)}%</div>
                </div>
            `;
            card.onclick = () => openPriceModal(p.codigo, safeDesc, p.precio, p.p_costo);
        } else if (currentTab === 'catalog') {
            statsHtml = `
                <div class="stat-group" style="width: 100%;">
                    <div class="label">Descripción</div>
                    <div class="val" style="font-size: 1rem; white-space: normal;">${p.descripcion}</div>
                </div>
            `;
            card.onclick = () => openDescModal(p.codigo, safeDesc);
        }

        card.innerHTML = `
            <div class="card-glow"></div>
            <div class="card-header">
                <span class="tag-dept">${p.departamento}</span>
                <div class="card-id">${p.codigo}</div>
            </div>
            <div class="card-name">${p.descripcion}</div>
            <div class="card-stats">
                ${statsHtml}
            </div>
        `;
        container.appendChild(card);
    });
}

function renderSalesCards(report, groupBy) {
    const container = document.getElementById('productsBody');
    container.innerHTML = '';
    
    if (report.length === 0) {
        container.innerHTML = '<div style="text-align: center; color: var(--text-dim); padding: 2rem;">No hay ventas en este periodo.</div>';
        return;
    }
    
    let totalGeneral = 0;
    
    report.forEach(item => {
        totalGeneral += item.ingreso;
        const card = document.createElement('div');
        card.className = 'product-card';
        card.style.cursor = 'default';
        
        if (groupBy === 'department') {
            card.innerHTML = `
                <div class="card-header">
                    <span class="tag-dept" style="font-size: 0.9rem;">${item.nombre}</span>
                </div>
                <div class="card-stats" style="margin-top: 1rem;">
                    <div class="stat-group">
                        <div class="label">Cant. Vendida</div>
                        <div class="val">${item.cantidad}</div>
                    </div>
                    <div class="stat-group" style="text-align: right;">
                        <div class="label">Ingreso Total</div>
                        <div class="val" style="color: var(--success);">$${item.ingreso.toFixed(2)}</div>
                    </div>
                </div>
            `;
        } else {
            card.innerHTML = `
                <div class="card-header">
                    <span class="tag-dept">${item.departamento}</span>
                    <div class="card-id">${item.codigo}</div>
                </div>
                <div class="card-name">${item.nombre}</div>
                <div class="card-stats">
                    <div class="stat-group">
                        <div class="label">Cant. Vendida</div>
                        <div class="val">${item.cantidad}</div>
                    </div>
                    <div class="stat-group" style="text-align: right;">
                        <div class="label">Ingreso Total</div>
                        <div class="val" style="color: var(--success);">$${item.ingreso.toFixed(2)}</div>
                    </div>
                </div>
            `;
        }
        container.appendChild(card);
    });
    
    // Render Total General Card at the top
    const summaryCard = document.createElement('div');
    summaryCard.className = 'product-card';
    summaryCard.style.background = 'rgba(16, 185, 129, 0.15)';
    summaryCard.style.border = '1px solid var(--success)';
    summaryCard.innerHTML = `
        <div style="text-align: center; color: var(--success); font-weight: 700;">
            <div style="font-size: 0.8rem; text-transform: uppercase;">Total Vendido en el Periodo</div>
            <div style="font-size: 2rem;">$${totalGeneral.toFixed(2)}</div>
        </div>
    `;
    container.insertBefore(summaryCard, container.firstChild);
}

let searchTimeout = null;

async function fetchBackendSearch(searchQuery) {
    let endpoint = '/api/inventory/search';
    if (currentTab === 'prices') endpoint = '/api/prices/search';
    if (currentTab === 'catalog') endpoint = '/api/catalog/search';
    try {
        const res = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: searchQuery })
        });
        return await res.json();
    } catch (err) {
        console.error("Error backend search:", err);
        return [];
    }
}

async function doFilter() {
    const search = document.getElementById('masterSearch').value.trim();
    const dept = document.getElementById('filterDept').value;
    const stock = document.getElementById('filterStock').value;

    let dataToFilter = allProducts;
    if (search.length > 0) {
        document.getElementById('productsBody').innerHTML = '<div style="text-align: center; color: var(--text-dim); padding: 2rem;">Buscando...</div>';
        dataToFilter = await fetchBackendSearch(search);
    }

    const filtered = dataToFilter.filter(p => {
        const matchDept = !dept || p.departamento === dept;
        let matchStock = true;
        if (currentTab === 'inventory') {
            if (stock === 'zero') matchStock = p.inventario <= 0;
            if (stock === 'low') matchStock = p.inventario > 0 && p.inventario < 10;
        }

        if (search.length === 0) {
            const pDesc = p.descripcion.toLowerCase();
            const pCode = p.codigo.toLowerCase();
            const searchLower = search.toLowerCase();
            const matchSearch = pDesc.includes(searchLower) ||
                pCode.includes(searchLower) ||
                (pCode.length > 1 && pCode.substring(1).includes(searchLower));
            return matchSearch && matchDept && matchStock;
        }

        return matchDept && matchStock;
    });
    renderMobileCards(filtered);
}

function multiFilter(event) {
    if (event && event.key === 'Enter') {
        if (searchTimeout) clearTimeout(searchTimeout);
        doFilter();
        return;
    }
    if (searchTimeout) clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
        doFilter();
    }, 400);
}

// Scanner Logic
document.getElementById('startScanner').onclick = async () => {
    if (!window.isSecureContext && location.hostname !== "localhost" && location.hostname !== "127.0.0.1") {
        showToast("Error: La cámara requiere conexión segura (HTTPS) en celulares. 🔒", "error");
        return;
    }

    document.getElementById('scannerOverlay').style.display = 'flex';
    html5QrCode = new Html5Qrcode("reader");
    const config = { fps: 15, qrbox: { width: 250, height: 250 } };

    try {
        await html5QrCode.start({ facingMode: "environment" }, config, (decodedText) => {
            document.getElementById('masterSearch').value = decodedText;
            multiFilter();
            stopScanning();
            showToast("¡Código Escaneado! ✅", "success");
        });
    } catch (err) {
        let errorMsg = "Error al activar cámara ❌";
        if (err.name === "NotAllowedError") errorMsg = "Permiso de cámara denegado 🚫";
        else if (err.name === "NotFoundError") errorMsg = "No se encontró cámara 📷";

        showToast(errorMsg, "error");
        console.error("Camera Error:", err);
        stopScanning();
    }
};

function stopScanning() {
    if (html5QrCode) {
        html5QrCode.stop().then(() => {
            document.getElementById('scannerOverlay').style.display = 'none';
            html5QrCode = null;
        }).catch(() => {
            document.getElementById('scannerOverlay').style.display = 'none';
        });
    } else {
        document.getElementById('scannerOverlay').style.display = 'none';
    }
}

function openModal(id, name, stock) {
    currentEditingCode = id;
    document.getElementById('modalProdName').textContent = name;
    document.getElementById('modalProdId').textContent = id;
    document.getElementById('editStock').value = stock;
    document.getElementById('editModal').style.display = 'flex';
    document.getElementById('editStock').focus();
}

function closeModal() { document.getElementById('editModal').style.display = 'none'; }

function changeQty(delta) {
    const input = document.getElementById('editStock');
    let val = parseFloat(input.value) || 0;
    val += delta;
    input.value = val;
}

async function saveInventory() {
    const val = parseFloat(document.getElementById('editStock').value);
    try {
        const res = await fetch('/api/inventory/update', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ codigo: currentEditingCode, cantidad: val })
        });
        if (res.ok) {
            showToast("Actualizado ✅", "success");
            closeModal();
            loadData();
        }
    } catch (err) { showToast("Error de red ❌", "error"); }
}

function openPriceModal(id, name, p_venta, p_costo) {
    currentEditingCode = id;
    document.getElementById('priceModalProdName').textContent = name;
    document.getElementById('editVenta').value = p_venta.toFixed(2);
    document.getElementById('editCosto').value = (p_costo || 0).toFixed(2);
    calcProfitPreview();
    document.getElementById('priceModal').style.display = 'flex';
}

function closePriceModal() { document.getElementById('priceModal').style.display = 'none'; }

function calcProfitPreview() {
    const v = parseFloat(document.getElementById('editVenta').value) || 0;
    const c = parseFloat(document.getElementById('editCosto').value) || 0;
    let profit = 0;
    if (c > 0) {
        profit = ((v - c) / c) * 100;
    } else if (v > 0) {
        profit = 100;
    }
    document.getElementById('profitPreview').textContent = profit.toFixed(1) + '%';
}

async function savePrices() {
    const v = parseFloat(document.getElementById('editVenta').value);
    const c = parseFloat(document.getElementById('editCosto').value);
    try {
        const res = await fetch('/api/prices/update', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ codigo: currentEditingCode, p_venta: v, p_costo: c })
        });
        if (res.ok) {
            showToast("Precios Actualizados ✅", "success");
            closePriceModal();
            loadData();
        } else {
            showToast("Error al actualizar ❌", "error");
        }
    } catch (err) { showToast("Error de red ❌", "error"); }
}

function showToast(msg, type) {
    const t = document.getElementById('toast');
    t.textContent = msg;
    t.style.display = 'block';
    t.style.background = type === 'success' ? '#10b981' : '#ef4444';
    setTimeout(() => t.style.display = 'none', 2500);
}

function openDescModal(id, desc) {
    currentEditingCode = id;
    document.getElementById('descModalProdName').textContent = "Editar: " + id;
    document.getElementById('descModalProdId').textContent = id;
    document.getElementById('editDesc').value = desc;
    document.getElementById('descModal').style.display = 'flex';
}

function closeDescModal() { document.getElementById('descModal').style.display = 'none'; }

async function saveDescription() {
    const desc = document.getElementById('editDesc').value.trim();
    if (!desc) {
        showToast("La descripción no puede estar vacía", "error");
        return;
    }
    try {
        const res = await fetch('/api/catalog/update', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ codigo: currentEditingCode, descripcion: desc })
        });
        if (res.ok) {
            showToast("Descripción Actualizada ✅", "success");
            closeDescModal();
            loadData();
        } else {
            const data = await res.json();
            showToast(data.error || "Error al actualizar ❌", "error");
        }
    } catch (err) { showToast("Error de red ❌", "error"); }
}

window.onload = loadData;
