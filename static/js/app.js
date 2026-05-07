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
    document.getElementById('tab-clients').classList.toggle('active', tab === 'clients');

    // Toggle specific UI options if needed
    document.getElementById('filterStock').style.display = tab === 'inventory' ? 'block' : 'none';
    
    document.getElementById('searchControls').style.display = tab === 'sales' ? 'none' : 'flex';
    document.getElementById('filterControls').style.display = (tab === 'sales' || tab === 'clients') ? 'none' : 'grid';
    document.getElementById('salesFilters').style.display = tab === 'sales' ? 'grid' : 'none';
    const clientF = document.getElementById('clientFilters');
    if(clientF) clientF.style.display = tab === 'clients' ? 'grid' : 'none';

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
        if (currentTab === 'clients') endpoint = '/api/clients';

        const res = await fetch(endpoint);
        if (res.status === 401) {
            document.getElementById('loginOverlay').style.display = 'flex';
            return;
        }
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

        const safeDesc = (p.descripcion || p.nombre || '').replace(/'/g, "\\'");

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
                } else if (currentTab === 'clients') {
            statsHtml = `
                <div class="stat-group">
                    <div class="label">Teléfono</div>
                    <div class="val">${p.telefono || '-'}</div>
                </div>
                <div class="stat-group" style="text-align: right;">
                    <div class="label">Saldo Actual</div>
                    <div class="val" style="color: ${p.saldo_actual > 0 ? 'var(--error)' : 'var(--success)'};">$${p.saldo_actual.toFixed(2)}</div>
                </div>
            `;
            card.onclick = () => openClientModal(p.numero, safeDesc, p.direccion, p.telefono, p.limite_credito);
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
                <span class="tag-dept">${p.departamento || 'Cliente'}</span>
                <div class="card-id">${p.codigo || p.numero}</div>
            </div>
            <div class="card-name">${p.descripcion || p.nombre}</div>
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
    if (currentTab === 'clients') endpoint = '/api/clients/search';
    try {
        const res = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: searchQuery })
        });
        if (res.status === 401) {
            document.getElementById('loginOverlay').style.display = 'flex';
            return [];
        }
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
            const pDesc = (p.descripcion || p.nombre || '').toLowerCase();
            const pCode = String(p.codigo || p.numero || '').toLowerCase();
            const searchLower = search.toLowerCase();
            const matchSearch = pDesc.includes(searchLower) ||
                pCode.includes(searchLower) ||
                (pCode.length > 1 && pCode.substring(1).includes(searchLower));
            return matchSearch && matchDept && matchStock;
        }

        return matchDept && matchStock;
    });

    if (currentTab === 'clients') {
        const sortClientObj = document.getElementById('sortClients');
        if (sortClientObj) {
            const sortVal = sortClientObj.value;
            if (sortVal === 'id') {
                filtered.sort((a, b) => a.numero - b.numero);
            } else if (sortVal === 'debt') {
                filtered.sort((a, b) => (b.saldo_actual || 0) - (a.saldo_actual || 0));
            } else if (sortVal === 'limit') {
                filtered.sort((a, b) => (b.limite_credito || 0) - (a.limite_credito || 0));
            } else {
                filtered.sort((a, b) => (a.nombre || '').localeCompare(b.nombre || ''));
            }
        }
    }
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


function openClientModal(numero, nombre, direccion, telefono, limite_credito) {
    currentEditingCode = numero;
    document.getElementById('clientModalName').textContent = "Editar: " + nombre;
    document.getElementById('clientModalId').textContent = "ID: " + numero;
    
    document.getElementById('editClientName').value = nombre;
    document.getElementById('editClientAddress').value = direccion || '';
    document.getElementById('editClientPhone').value = telefono || '';
    document.getElementById('editClientLimit').value = (limite_credito || 0).toFixed(2);
    
    document.getElementById('clientModal').style.display = 'flex';
}

function closeClientModal() { document.getElementById('clientModal').style.display = 'none'; }

async function saveClient() {
    const nombre = document.getElementById('editClientName').value.trim();
    const direccion = document.getElementById('editClientAddress').value.trim();
    const telefono = document.getElementById('editClientPhone').value.trim();
    const limite = parseFloat(document.getElementById('editClientLimit').value) || 0;
    
    if (!nombre) {
        showToast("El nombre es requerido", "error");
        return;
    }
    try {
        const res = await fetch('/api/clients/update', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                numero: currentEditingCode, 
                nombre: nombre,
                direccion: direccion,
                telefono: telefono,
                limite_credito: limite
            })
        });
        if (res.ok) {
            showToast("Cliente Actualizado ✅", "success");
            closeClientModal();
            loadData();
        } else {
            const data = await res.json();
            showToast(data.error || "Error al actualizar ❌", "error");
        }
    } catch (err) { showToast("Error de red ❌", "error"); }
}


// Clock Logic
function updateDateTime() {
    const now = new Date();
    const dateOpts = { weekday: 'short', day: '2-digit', month: 'short' };
    const dateEl = document.getElementById('currentDate');
    const timeEl = document.getElementById('currentTime');
    if (dateEl && timeEl) {
        dateEl.textContent = now.toLocaleDateString('es-MX', dateOpts);
        timeEl.textContent = now.toLocaleTimeString('es-MX', { hour: '2-digit', minute: '2-digit' });
    }
}
setInterval(updateDateTime, 1000);
updateDateTime();

// Auth Logic
async function login() {
    const user = document.getElementById('loginUser').value;
    const pass = document.getElementById('loginPass').value;
    const errorEl = document.getElementById('loginError');
    
    if (!user || !pass) {
        errorEl.textContent = "Ingresa usuario y contraseña";
        errorEl.style.display = 'block';
        return;
    }
    
    try {
        const res = await fetch('/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: user, password: pass })
        });
        
        const data = await res.json();
        if (res.ok) {
            document.getElementById('loginOverlay').style.display = 'none';
            document.getElementById('adminSettingsBtn').style.display = data.user.is_admin ? 'block' : 'none';
            document.getElementById('loginPass').value = '';
            errorEl.style.display = 'none';
            showToast("Bienvenido ✅", "success");
            loadData();
        } else {
            errorEl.textContent = data.message || "Error de autenticación";
            errorEl.style.display = 'block';
        }
    } catch (err) {
        errorEl.textContent = "Error de conexión";
        errorEl.style.display = 'block';
    }
}

async function logout() {
    try {
        await fetch('/api/auth/logout', { method: 'POST' });
        location.reload();
    } catch (err) {
        location.reload();
    }
}

async function checkAuth() {
    try {
        const res = await fetch('/api/auth/check');
        const data = await res.json();
        if (res.ok && data.logged_in) {
            document.getElementById('loginOverlay').style.display = 'none';
            document.getElementById('adminSettingsBtn').style.display = data.is_admin ? 'block' : 'none';
            loadData();
        } else {
            document.getElementById('loginOverlay').style.display = 'flex';
        }
    } catch (err) {
        document.getElementById('loginOverlay').style.display = 'flex';
    }
}

window.onload = checkAuth;

// Admin User Management Logic
function openSettingsModal() {
    document.getElementById('settingsModal').style.display = 'flex';
    loadUsers();
}

function closeSettingsModal() {
    document.getElementById('settingsModal').style.display = 'none';
    hideUserForm();
}

async function loadUsers() {
    const container = document.getElementById('usersTableContainer');
    container.innerHTML = '<div style="padding: 2rem; text-align: center; color: var(--text-dim);">Cargando usuarios...</div>';
    
    try {
        const res = await fetch('/api/admin/users');
        if (!res.ok) throw new Error("No autorizado");
        const users = await res.json();
        
        let html = `
            <table style="width: 100%; border-collapse: collapse; font-size: 0.9rem;">
                <thead>
                    <tr style="background: rgba(255,255,255,0.05); color: var(--text-dim); text-align: left;">
                        <th style="padding: 0.8rem;">Nombre / Usuario</th>
                        <th style="padding: 0.8rem; text-align: center;">Estado</th>
                        <th style="padding: 0.8rem; text-align: right;">Acción</th>
                    </tr>
                </thead>
                <tbody>
        `;
        
        users.forEach(u => {
            html += `
                <tr style="border-bottom: 1px solid var(--border);">
                    <td style="padding: 1rem;">
                        <div style="font-weight: 700;">${u.nombre}</div>
                        <div style="font-size: 0.75rem; color: var(--text-dim);">@${u.usuario}</div>
                    </td>
                    <td style="padding: 1rem; text-align: center;">
                        <span style="color: ${u.activo ? 'var(--success)' : 'var(--error)'}; font-size: 0.7rem; font-weight: 800;">
                            ${u.activo ? 'ACTIVO' : 'INACTIVO'}
                        </span>
                    </td>
                    <td style="padding: 1rem; text-align: right;">
                        <button onclick='editUser(${JSON.stringify(u)})' style="background: var(--surface-accent); border: none; color: white; padding: 0.4rem 0.8rem; border-radius: 8px; font-size: 0.75rem; cursor: pointer;">Editar</button>
                    </td>
                </tr>
            `;
        });
        
        html += '</tbody></table>';
        container.innerHTML = html;
    } catch (err) {
        container.innerHTML = '<div style="padding: 2rem; text-align: center; color: var(--error);">Error al cargar usuarios.</div>';
    }
}

function showUserForm() {
    document.getElementById('usersListSection').style.display = 'none';
    document.getElementById('userFormSection').style.display = 'block';
    document.getElementById('userFormTitle').textContent = "Nuevo Usuario";
    
    // Clear form
    document.getElementById('adminUserId').value = '';
    document.getElementById('adminUserFullname').value = '';
    document.getElementById('adminUsername').value = '';
    document.getElementById('adminUserPass').value = '';
    document.getElementById('adminUserActive').checked = true;
    
    const checks = document.querySelectorAll('#permissionsGrid input[type="checkbox"]');
    checks.forEach(c => c.checked = false);
}

function hideUserForm() {
    document.getElementById('usersListSection').style.display = 'block';
    document.getElementById('userFormSection').style.display = 'none';
}

function editUser(user) {
    showUserForm();
    document.getElementById('userFormTitle').textContent = "Editar Usuario";
    
    document.getElementById('adminUserId').value = user.id;
    document.getElementById('adminUserFullname').value = user.nombre;
    document.getElementById('adminUsername').value = user.usuario;
    document.getElementById('adminUserPass').value = user.clave;
    document.getElementById('adminUserActive').checked = user.activo;
    
    const perms = user.permisos ? user.permisos.split(',') : [];
    const checks = document.querySelectorAll('#permissionsGrid input[type="checkbox"]');
    checks.forEach(c => {
        c.checked = perms.includes(c.value);
    });
}

async function saveAdminUser() {
    const id = document.getElementById('adminUserId').value;
    const nombre = document.getElementById('adminUserFullname').value.trim();
    const usuario = document.getElementById('adminUsername').value.trim();
    const clave = document.getElementById('adminUserPass').value.trim();
    const activo = document.getElementById('adminUserActive').checked;
    
    if (!nombre || !usuario || !clave) {
        showToast("Complete todos los campos ⚠️", "error");
        return;
    }
    
    const checks = document.querySelectorAll('#permissionsGrid input[type="checkbox"]:checked');
    const permisos = Array.from(checks).map(c => c.value).join(',');
    
    const userData = { id, nombre, usuario, clave, activo, permisos };
    
    try {
        const res = await fetch('/api/admin/users/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(userData)
        });
        
        if (res.ok) {
            showToast("Usuario guardado ✅", "success");
            hideUserForm();
            loadUsers();
        } else {
            showToast("Error al guardar ❌", "error");
        }
    } catch (err) {
        showToast("Error de conexión ❌", "error");
    }
}
