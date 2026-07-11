/* ============================================================
   KOI · Panel de administración (JWT + CRUD)
   ============================================================ */
const KoiAdmin = (function () {
    'use strict';

    const TOKEN_KEY = 'koi_admin_token';
    const USER_KEY = 'koi_admin_user';

    // ---------------------------------------------------------
    // Utilidades de sesión / API
    // ---------------------------------------------------------
    function getToken() { return localStorage.getItem(TOKEN_KEY); }
    function setSession(token, user) {
        localStorage.setItem(TOKEN_KEY, token);
        localStorage.setItem(USER_KEY, JSON.stringify(user));
    }
    function clearSession() {
        localStorage.removeItem(TOKEN_KEY);
        localStorage.removeItem(USER_KEY);
    }
    function getUser() {
        try { return JSON.parse(localStorage.getItem(USER_KEY)); }
        catch (_) { return null; }
    }

    async function api(url, options) {
        options = options || {};
        options.headers = Object.assign(
            { 'Content-Type': 'application/json' },
            options.headers || {}
        );
        const token = getToken();
        if (token) options.headers['Authorization'] = 'Bearer ' + token;

        const res = await fetch(url, options);
        if (res.status === 401 || res.status === 403) {
            clearSession();
            if (!location.pathname.endsWith('/admin')) location.href = '/admin';
            throw new Error('No autorizado');
        }
        return res;
    }

    // ---------------------------------------------------------
    // Toasts
    // ---------------------------------------------------------
    function toast(mensaje, tipo) {
        tipo = tipo || 'info';
        let cont = document.getElementById('toastContainer');
        if (!cont) {
            cont = document.createElement('div');
            cont.id = 'toastContainer';
            cont.className = 'toast-container';
            document.body.appendChild(cont);
        }
        const el = document.createElement('div');
        el.className = 'toast toast--' + tipo;
        el.textContent = mensaje;
        cont.appendChild(el);
        setTimeout(function () {
            el.classList.add('is-hiding');
            setTimeout(function () { el.remove(); }, 300);
        }, 3200);
    }

    // ---------------------------------------------------------
    // Helpers de formato
    // ---------------------------------------------------------
    const ESTADOS = {
        pending: 'Pendiente',
        confirmed: 'Confirmada',
        completed: 'Completada',
        cancelled: 'Cancelada'
    };
    function badgeEstado(estado) {
        return '<span class="badge badge--' + estado + '">' + (ESTADOS[estado] || estado) + '</span>';
    }
    function precio(p) { return Number(p).toFixed(2).replace('.', ',') + ' €'; }
    function esc(t) { const d = document.createElement('div'); d.textContent = t == null ? '' : t; return d.innerHTML; }

    // ---------------------------------------------------------
    // Layout admin común (sidebar, logout, usuario, active link)
    // ---------------------------------------------------------
    function initLayout(paginaActiva) {
        // Guard: verificar token
        if (!getToken()) { location.href = '/admin'; return false; }

        // Verificar validez del token contra la API
        api('/api/auth/me').then(function (res) {
            if (res.ok) {
                res.json().then(function (user) {
                    setSession(getToken(), user);
                    const uEl = document.getElementById('adminUser');
                    if (uEl) uEl.textContent = user.name + ' · Admin';
                });
            }
        }).catch(function () { /* api ya redirige */ });

        // Mostrar usuario guardado inmediatamente
        const user = getUser();
        const uEl = document.getElementById('adminUser');
        if (uEl && user) uEl.textContent = user.name + ' · Admin';

        // Marcar link activo
        document.querySelectorAll('.admin-nav-link[data-page]').forEach(function (l) {
            if (l.dataset.page === paginaActiva) l.classList.add('is-active');
        });

        // Logout
        const logout = document.getElementById('logoutBtn');
        if (logout) logout.addEventListener('click', function () {
            clearSession();
            location.href = '/admin';
        });

        // Toggle sidebar móvil
        const toggle = document.getElementById('sidebarToggle');
        const sidebar = document.getElementById('adminSidebar');
        if (toggle && sidebar) toggle.addEventListener('click', function () {
            sidebar.classList.toggle('is-open');
        });

        // Cerrar modales genéricos
        document.querySelectorAll('[data-close]').forEach(function (el) {
            el.addEventListener('click', function () {
                const modal = el.closest('.modal');
                if (modal) modal.hidden = true;
            });
        });

        return true;
    }

    // ---------------------------------------------------------
    // LOGIN
    // ---------------------------------------------------------
    function initLogin() {
        // Si ya hay sesión, ir al dashboard
        if (getToken()) { location.href = '/admin/dashboard'; return; }

        const form = document.getElementById('loginForm');
        const errorBox = document.getElementById('loginError');
        const btn = document.getElementById('loginBtn');
        if (!form) return;

        form.addEventListener('submit', async function (e) {
            e.preventDefault();
            errorBox.hidden = true;
            btn.disabled = true;
            btn.textContent = 'Accediendo…';

            const datos = {
                email: document.getElementById('email').value.trim(),
                password: document.getElementById('password').value
            };

            try {
                const res = await fetch('/api/auth/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(datos)
                });
                if (res.ok) {
                    const data = await res.json();
                    setSession(data.access_token, data.user);
                    location.href = '/admin/dashboard';
                } else {
                    const err = await res.json().catch(function () { return {}; });
                    errorBox.hidden = false;
                    errorBox.textContent = err.detail || 'Credenciales incorrectas.';
                }
            } catch (err) {
                errorBox.hidden = false;
                errorBox.textContent = 'Error de conexión. Inténtalo de nuevo.';
            } finally {
                btn.disabled = false;
                btn.textContent = 'Acceder';
            }
        });
    }

    // ---------------------------------------------------------
    // DASHBOARD
    // ---------------------------------------------------------
    async function initDashboard() {
        if (!initLayout('dashboard')) return;

        try {
            const [stats, hoy, prox] = await Promise.all([
                api('/api/dashboard/stats').then(function (r) { return r.json(); }),
                api('/api/dashboard/reservations/today').then(function (r) { return r.json(); }),
                api('/api/dashboard/reservations/upcoming').then(function (r) { return r.json(); })
            ]);

            document.getElementById('statToday').textContent = stats.reservas_hoy;
            document.getElementById('statWeek').textContent = stats.reservas_semana;
            document.getElementById('statClients').textContent = stats.total_clientes;
            document.getElementById('statOccupancy').textContent = stats.ocupacion + '%';

            pintarTablaHoy(hoy);
            pintarTablaProximas(prox);
        } catch (err) {
            console.error(err);
        }
    }

    function pintarTablaHoy(reservas) {
        const tbody = document.getElementById('todayTable');
        if (!reservas.length) {
            tbody.innerHTML = '<tr><td colspan="5" class="table-empty">No hay reservas para hoy.</td></tr>';
            return;
        }
        tbody.innerHTML = reservas.map(function (r) {
            return '<tr>' +
                '<td class="cell-strong">' + esc(r.time) + '</td>' +
                '<td>' + esc(r.customer_name) + '</td>' +
                '<td>' + r.guests + '</td>' +
                '<td class="cell-muted">' + esc(r.customer_phone) + '</td>' +
                '<td>' + badgeEstado(r.status) + '</td>' +
            '</tr>';
        }).join('');
    }

    function pintarTablaProximas(reservas) {
        const tbody = document.getElementById('upcomingTable');
        if (!reservas.length) {
            tbody.innerHTML = '<tr><td colspan="5" class="table-empty">No hay próximas reservas.</td></tr>';
            return;
        }
        tbody.innerHTML = reservas.map(function (r) {
            return '<tr>' +
                '<td class="cell-strong">' + esc(r.date) + '</td>' +
                '<td>' + esc(r.time) + '</td>' +
                '<td>' + esc(r.customer_name) + '</td>' +
                '<td>' + r.guests + '</td>' +
                '<td>' + badgeEstado(r.status) + '</td>' +
            '</tr>';
        }).join('');
    }

    // ---------------------------------------------------------
    // RESERVAS
    // ---------------------------------------------------------
    let reservasCache = [];

    async function initReservations() {
        if (!initLayout('reservas')) return;

        const statusFilter = document.getElementById('statusFilter');
        const dateFilter = document.getElementById('dateFilter');
        const clearBtn = document.getElementById('clearFilters');

        async function cargar() {
            const params = new URLSearchParams();
            if (statusFilter.value) params.append('status', statusFilter.value);
            if (dateFilter.value) params.append('date', dateFilter.value);
            const url = '/api/reservations' + (params.toString() ? '?' + params.toString() : '');
            try {
                reservasCache = await api(url).then(function (r) { return r.json(); });
                pintarReservas(reservasCache);
            } catch (err) { console.error(err); }
        }

        statusFilter.addEventListener('change', cargar);
        dateFilter.addEventListener('change', cargar);
        clearBtn.addEventListener('click', function () {
            statusFilter.value = ''; dateFilter.value = ''; cargar();
        });

        // Delegación de eventos en la tabla
        document.getElementById('reservationsTable').addEventListener('click', function (e) {
            const btn = e.target.closest('[data-action]');
            if (!btn) return;
            const id = parseInt(btn.dataset.id, 10);
            const accion = btn.dataset.action;
            if (accion === 'detail') abrirDetalle(id);
            else cambiarEstado(id, accion, cargar);
        });

        cargar();
    }

    function pintarReservas(reservas) {
        const tbody = document.getElementById('reservationsTable');
        if (!reservas.length) {
            tbody.innerHTML = '<tr><td colspan="7" class="table-empty">No hay reservas que coincidan.</td></tr>';
            return;
        }
        tbody.innerHTML = reservas.map(function (r) {
            return '<tr>' +
                '<td class="cell-strong">' + esc(r.date) + '</td>' +
                '<td>' + esc(r.time) + '</td>' +
                '<td>' + esc(r.customer_name) + '</td>' +
                '<td class="cell-muted">' + esc(r.customer_phone) + '<br>' + esc(r.customer_email) + '</td>' +
                '<td>' + r.guests + '</td>' +
                '<td>' + badgeEstado(r.status) + '</td>' +
                '<td><div class="row-actions">' +
                    '<button class="btn-admin btn-admin--ghost btn-admin--sm" data-action="detail" data-id="' + r.id + '">Ver</button>' +
                    (r.status !== 'confirmed' ? '<button class="btn-admin btn-admin--gold btn-admin--sm" data-action="confirmed" data-id="' + r.id + '">Confirmar</button>' : '') +
                    (r.status !== 'completed' ? '<button class="btn-admin btn-admin--ghost btn-admin--sm" data-action="completed" data-id="' + r.id + '">Completar</button>' : '') +
                    (r.status !== 'cancelled' ? '<button class="btn-admin btn-admin--danger btn-admin--sm" data-action="cancelled" data-id="' + r.id + '">Cancelar</button>' : '') +
                '</div></td>' +
            '</tr>';
        }).join('');
    }

    async function cambiarEstado(id, estado, callback) {
        try {
            const res = await api('/api/reservations/' + id, {
                method: 'PUT',
                body: JSON.stringify({ status: estado })
            });
            if (res.ok) {
                toast('Reserva ' + (ESTADOS[estado] || estado).toLowerCase() + '.', 'success');
                if (callback) callback();
            } else {
                toast('No se pudo actualizar la reserva.', 'error');
            }
        } catch (err) { toast('Error al actualizar.', 'error'); }
    }

    function abrirDetalle(id) {
        const r = reservasCache.find(function (x) { return x.id === id; });
        if (!r) return;
        const cont = document.getElementById('reservationDetail');
        cont.innerHTML =
            fila('Nombre', r.customer_name) +
            fila('Teléfono', r.customer_phone) +
            fila('Email', r.customer_email) +
            fila('Fecha', r.date) +
            fila('Hora', r.time) +
            fila('Comensales', r.guests) +
            fila('Mesa', r.table_id ? ('#' + r.table_id) : 'Por asignar') +
            fila('Estado', ESTADOS[r.status] || r.status) +
            fila('Peticiones', r.special_requests || '—') +
            '<div class="detail-status-actions">' +
                '<button class="btn-admin btn-admin--gold btn-admin--sm" data-detail-action="confirmed" data-id="' + r.id + '">Confirmar</button>' +
                '<button class="btn-admin btn-admin--ghost btn-admin--sm" data-detail-action="completed" data-id="' + r.id + '">Completar</button>' +
                '<button class="btn-admin btn-admin--danger btn-admin--sm" data-detail-action="cancelled" data-id="' + r.id + '">Cancelar</button>' +
            '</div>';

        cont.querySelectorAll('[data-detail-action]').forEach(function (btn) {
            btn.addEventListener('click', function () {
                cambiarEstado(parseInt(btn.dataset.id, 10), btn.dataset.detailAction, function () {
                    document.getElementById('reservationModal').hidden = true;
                    // recargar tabla
                    const sf = document.getElementById('statusFilter');
                    sf.dispatchEvent(new Event('change'));
                });
            });
        });

        document.getElementById('reservationModal').hidden = false;
    }
    function fila(k, v) { return '<div class="detail-row"><span>' + k + '</span><span>' + esc(v) + '</span></div>'; }

    // ---------------------------------------------------------
    // MENÚ
    // ---------------------------------------------------------
    let categoriasCache = [];
    let itemsCache = [];
    let itemABorrar = null;

    async function initMenu() {
        if (!initLayout('menu')) return;

        const catFilter = document.getElementById('categoryFilter');
        const itemSelect = document.getElementById('itemCategory');
        const newBtn = document.getElementById('newItemBtn');
        const form = document.getElementById('itemForm');
        const modal = document.getElementById('itemModal');
        const confirmModal = document.getElementById('confirmModal');
        const fileInput = document.getElementById('itemImageFile');

        // Cargar categorías
        categoriasCache = await api('/api/menu/categories').then(function (r) { return r.json(); });
        catFilter.innerHTML = '<option value="">Todas las categorías</option>' +
            categoriasCache.map(function (c) { return '<option value="' + c.slug + '">' + esc(c.name) + '</option>'; }).join('');
        itemSelect.innerHTML = categoriasCache.map(function (c) {
            return '<option value="' + c.id + '">' + esc(c.name) + '</option>';
        }).join('');

        // Escucha cuando el administrador selecciona un archivo local
        if (fileInput) {
            fileInput.addEventListener('change', function (e) {
                const file = e.target.files[0];
                
                if (file) {
                    const reader = new FileReader();
                    reader.onloadend = function () {
                        document.getElementById('itemImage').value = reader.result;
                    };
                    reader.readAsDataURL(file);
                }
            });
        }

        async function cargar() {
            if (adminSearchInput) adminSearchInput.value = '';
            const slug = catFilter.value;
            const url = '/api/menu/items' + (slug ? '?category_slug=' + encodeURIComponent(slug) : '');
            itemsCache = await api(url).then(function (r) { return r.json(); });
            pintarMenu(itemsCache);
        }

        catFilter.addEventListener('change', cargar);

        // 🔍 Filtrar la tabla dinámicamente con el buscador
        const adminSearchInput = document.getElementById('adminSearchInput');
        if (adminSearchInput) {
            adminSearchInput.addEventListener('input', function (e) {
                const termino = e.target.value.toLowerCase().trim();
                
                // Si no hay término, mostramos todos los ítems de la caché
                if (!termino) {
                    pintarMenu(itemsCache);
                    return;
                }

                // Filtramos sobre los platos cargados actualmente
                const filtrados = itemsCache.filter(function (item) {
                    return item.name.toLowerCase().includes(termino) || 
                        (item.description && item.description.toLowerCase().includes(termino));
                });

                pintarMenu(filtrados);
            });
        }

        // Nuevo plato
        newBtn.addEventListener('click', function () { abrirModalItem(null); });

        // Tabla: editar / borrar
        document.getElementById('menuTable').addEventListener('click', function (e) {
            const btn = e.target.closest('[data-action]');
            if (!btn) return;
            const id = parseInt(btn.dataset.id, 10);
            if (btn.dataset.action === 'edit') abrirModalItem(id);
            else if (btn.dataset.action === 'delete') {
                itemABorrar = id;
                const item = itemsCache.find(function (x) { return x.id === id; });
                document.getElementById('confirmText').textContent =
                    '¿Seguro que quieres eliminar "' + (item ? item.name : 'este plato') + '"?';
                confirmModal.hidden = false;
            }
        });

        // Confirmar borrado
        document.getElementById('confirmDeleteBtn').addEventListener('click', async function () {
            if (itemABorrar == null) return;
            try {
                const res = await api('/api/menu/items/' + itemABorrar, { method: 'DELETE' });
                if (res.ok) { toast('Plato eliminado.', 'success'); cargar(); }
                else toast('No se pudo eliminar.', 'error');
            } catch (err) { toast('Error al eliminar.', 'error'); }
            confirmModal.hidden = true;
            itemABorrar = null;
        });

        // Guardar (crear / editar)
        form.addEventListener('submit', async function (e) {
            e.preventDefault();
            const id = document.getElementById('itemId').value;
            
            // Forzamos la captura del valor del input oculto justo ahora
            const base64Image = document.getElementById('itemImage').value;

            const payload = {
                name: document.getElementById('itemName').value.trim(),
                category_id: parseInt(document.getElementById('itemCategory').value, 10),
                description: document.getElementById('itemDescription').value.trim(),
                price: parseFloat(document.getElementById('itemPrice').value),
                // Si está vacío, mandamos null; si tiene el Base64, mandamos el texto completo
                image_url: base64Image.trim() || null, 
                is_featured: document.getElementById('itemFeatured').checked,
                is_available: document.getElementById('itemAvailable').checked
            };

            try {
                const res = id
                    ? await api('/api/menu/items/' + id, { method: 'PUT', body: JSON.stringify(payload) })
                    : await api('/api/menu/items', { method: 'POST', body: JSON.stringify(payload) });
                if (res.ok) {
                    toast(id ? 'Plato actualizado.' : 'Plato creado.', 'success');
                    modal.hidden = true;
                    cargar();
                } else {
                    toast('No se pudo guardar el plato.', 'error');
                }
            } catch (err) { toast('Error al guardar.', 'error'); }
        });

        function abrirModalItem(id) {
            form.reset();
            if (fileInput) fileInput.value = '';
            document.getElementById('itemId').value = '';
            if (id) {
                const item = itemsCache.find(function (x) { return x.id === id; });
                if (!item) return;
                document.getElementById('itemModalTitle').textContent = 'Editar plato';
                document.getElementById('itemId').value = item.id;
                document.getElementById('itemName').value = item.name;
                document.getElementById('itemCategory').value = item.category_id;
                document.getElementById('itemDescription').value = item.description || '';
                document.getElementById('itemPrice').value = item.price;
                document.getElementById('itemImage').value = item.image_url || '';
                document.getElementById('itemFeatured').checked = item.is_featured;
                document.getElementById('itemAvailable').checked = item.is_available;
            } else {
                document.getElementById('itemModalTitle').textContent = 'Nuevo plato';
                document.getElementById('itemAvailable').checked = true;
            }
            modal.hidden = false;
        }

        cargar();
    }

    function pintarMenu(items) {
        const tbody = document.getElementById('menuTable');
        if (!items.length) {
            tbody.innerHTML = '<tr><td colspan="6" class="table-empty">No hay platos.</td></tr>';
            return;
        }
        tbody.innerHTML = items.map(function (i) {
            return '<tr>' +
                '<td class="cell-strong">' + esc(i.name) + '</td>' +
                '<td class="cell-muted">' + esc(i.category_name || '') + '</td>' +
                '<td>' + precio(i.price) + '</td>' +
                '<td>' + (i.is_featured ? '<span class="badge badge--yes">Sí</span>' : '<span class="badge badge--no">No</span>') + '</td>' +
                '<td>' + (i.is_available ? '<span class="badge badge--yes">Sí</span>' : '<span class="badge badge--no">No</span>') + '</td>' +
                '<td><div class="row-actions">' +
                    '<button class="btn-admin btn-admin--ghost btn-admin--sm" data-action="edit" data-id="' + i.id + '">Editar</button>' +
                    '<button class="btn-admin btn-admin--danger btn-admin--sm" data-action="delete" data-id="' + i.id + '">Eliminar</button>' +
                '</div></td>' +
            '</tr>';
        }).join('');
    }

    // API pública del módulo
    return {
        initLogin: initLogin,
        initDashboard: initDashboard,
        initReservations: initReservations,
        initMenu: initMenu
    };
})();
