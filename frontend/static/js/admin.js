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
        preparing: 'En Preparación',
        ready: 'Listo',
        out_for_delivery: 'En Reparto',
        delivered: 'Entregado',
        cancelled: 'Cancelado',
        completed: 'Completado',
        confirmed: 'Confirmado',
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
        if (!getToken()) { location.href = '/admin'; return false; }

        api('/api/auth/me').then(function (res) {
            if (res.ok) {
                res.json().then(function (user) {
                    setSession(getToken(), user);
                    const uEl = document.getElementById('adminUser');
                    if (uEl) uEl.textContent = user.name + ' · Admin';
                });
            }
        }).catch(function () { });

        const user = getUser();
        const uEl = document.getElementById('adminUser');
        if (uEl && user) uEl.textContent = user.name + ' · Admin';

        document.querySelectorAll('.admin-nav-link[data-page]').forEach(function (l) {
            if (l.dataset.page === paginaActiva) l.classList.add('is-active');
        });

        const logout = document.getElementById('logoutBtn');
        if (logout) logout.addEventListener('click', function () {
            clearSession();
            location.href = '/admin';
        });

        const toggle = document.getElementById('sidebarToggle');
        const sidebar = document.getElementById('adminSidebar');
        if (toggle && sidebar) toggle.addEventListener('click', function () {
            sidebar.classList.toggle('is-open');
        });

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
                '<td class="cell-muted">' + esc(r.customer_phone) + '</td>' +
                '<td>' + r.guests + '</td>' +
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

        // Busca esto dentro de initReservations y déjalo limpio para que cargue reservas:
        async function cargar() {
            try {
                const res = await api('/api/reservations'); // Cambiado a su endpoint correcto si corresponde
                if (res.ok) {
                    reservasCache = await res.json();
                    pintarReservas(reservasCache);
                } else { throw new Error(); }
            } catch (err) {
                document.getElementById('reservationsTable').innerHTML = `
            <tr><td colspan="8" class="table-empty" style="color: var(--color-red-light);">Error al cargar las reservas.</td></tr>
        `;
            }
        }

        statusFilter.addEventListener('change', cargar);
        dateFilter.addEventListener('change', cargar);
        clearBtn.addEventListener('click', function () {
            statusFilter.value = ''; dateFilter.value = ''; cargar();
        });

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
            tbody.innerHTML = '<tr><td colspan="8" class="table-empty">No hay reservas que coincidan.</td></tr>';
            return;
        }
        tbody.innerHTML = reservas.map(function (r) {
            return '<tr>' +
                '<td class="cell-strong">' + esc(r.date) + '</td>' +
                '<td>' + esc(r.time) + '</td>' +
                '<td>' + esc(r.customer_name) + '</td>' +
                '<td class="cell-muted">' + esc(r.customer_phone) + '<br>' + esc(r.customer_email) + '</td>' +
                '<td>' + r.guests + '</td>' +
                '<td>' + esc(r.table_id) + '</td>' +
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
            fila('Mesa', r.table_id ? ('Nº' + r.table_id) : 'Por asignar') +
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
                    const sf = document.getElementById('statusFilter');
                    sf.dispatchEvent(new Event('change'));
                });
            });
        });

        document.getElementById('reservationModal').hidden = false;
    }
    function fila(k, v) { return '<div class="detail-row"><span>' + k + '</span><span>' + esc(v) + '</span></div>'; }

    // ---------------------------------------------------------
    // MENÚ (Categorías + Platos)
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

        const manageCategoriesBtn = document.getElementById('manageCategoriesBtn');
        const manageCategoriesModal = document.getElementById('manageCategoriesModal');
        const quickCategoriesTable = document.getElementById('quickCategoriesTable');
        const addNewCategoryBtn = document.getElementById('addNewCategoryBtn');
        const categoryFormModal = document.getElementById('categoryFormModal');
        const quickCategoryForm = document.getElementById('quickCategoryForm');
        const quickCategoryId = document.getElementById('quickCategoryId');
        const quickCategoryFormTitle = document.getElementById('categoryFormTitle');

        async function cargarYActualizarCategorias() {
            categoriasCache = await api('/api/menu/categories').then(function (r) { return r.json(); });
            const seleccionadaActualmente = itemSelect.value;

            catFilter.innerHTML = '<option value="">Todas las categorías</option>' +
                categoriasCache.map(function (c) { return '<option value="' + c.slug + '">' + esc(c.name) + '</option>'; }).join('');

            itemSelect.innerHTML = categoriasCache.map(function (c) {
                return '<option value="' + c.id + '">' + esc(c.name) + '</option>';
            }).join('');

            if (seleccionadaActualmente) { itemSelect.value = seleccionadaActualmente; }
        }

        await cargarYActualizarCategorias();

        if (manageCategoriesBtn) {
            manageCategoriesBtn.addEventListener('click', function () {
                pintarMiniCategorias();
                if (manageCategoriesModal) manageCategoriesModal.hidden = false;
            });
        }

        function pintarMiniCategorias() {
            categoriasCache.sort((a, b) => a.order_index - b.order_index);
            if (!categoriasCache.length) {
                quickCategoriesTable.innerHTML = '<tr><td colspan="4" class="table-empty">No hay categorías.</td></tr>';
                return;
            }
            quickCategoriesTable.innerHTML = categoriasCache.map(function (c) {
                return '<tr>' +
                    '<td class="cell-strong">' + c.order_index + '</td>' +
                    '<td><strong>' + esc(c.name) + '</strong></td>' +
                    '<td>' + (c.is_active ? '<span class="badge badge--yes" style="padding: 0.1rem 0.4rem; font-size:0.75rem;">Sí</span>' : '<span class="badge badge--no" style="padding: 0.1rem 0.4rem; font-size:0.75rem;">No</span>') + '</td>' +
                    '<td><div class="row-actions" style="gap:0.25rem;">' +
                    '<button type="button" class="btn-admin btn-admin--ghost btn-admin--sm" data-cat-action="edit" data-id="' + c.id + '" style="padding: 0.1rem 0.3rem; font-size: 0.75rem;">Editar</button>' +
                    '<button type="button" class="btn-admin btn-admin--danger btn-admin--sm" data-cat-action="delete" data-id="' + c.id + '" style="padding: 0.1rem 0.3rem; font-size: 0.75rem;">Eliminar</button>' +
                    '</div></td>' +
                    '</tr>';
            }).join('');
        }

        if (quickCategoriesTable) {
            quickCategoriesTable.addEventListener('click', async function (e) {
                const btn = e.target.closest('[data-cat-action]');
                if (!btn) return;
                const id = parseInt(btn.dataset.id, 10);
                const action = btn.dataset.catAction;

                if (action === 'edit') {
                    const cat = categoriasCache.find(x => x.id === id);
                    if (cat) {
                        quickCategoryForm.reset();
                        quickCategoryId.value = cat.id;
                        quickCategoryFormTitle.textContent = 'Editar Categoría';
                        document.getElementById('quickCategoryName').value = cat.name;
                        document.getElementById('quickCategoryDescription').value = cat.description || '';
                        document.getElementById('quickCategoryOrder').value = cat.order_index;
                        document.getElementById('quickCategoryActive').checked = cat.is_active;
                        categoryFormModal.hidden = false;
                    }
                } else if (action === 'delete') {
                    if (confirm('¿Estás seguro de que deseas eliminar esta categoría? Si tiene platos asociados dará error.')) {
                        try {
                            const res = await api('/api/menu/categories/' + id, { method: 'DELETE' });
                            if (res.ok) {
                                toast('Categoría eliminada.', 'success');
                                await cargarYActualizarCategorias();
                                pintarMiniCategorias();
                            } else {
                                toast('No se pudo eliminar (verifica que no tenga platos asociados).', 'error');
                            }
                        } catch (err) { toast('Error al procesar la solicitud.', 'error'); }
                    }
                }
            });
        }

        if (addNewCategoryBtn) {
            addNewCategoryBtn.addEventListener('click', function () {
                quickCategoryForm.reset();
                quickCategoryId.value = '';
                quickCategoryFormTitle.textContent = 'Nueva Categoría';
                document.getElementById('quickCategoryOrder').value = categoriasCache.length;
                document.getElementById('quickCategoryActive').checked = true;
                categoryFormModal.hidden = false;
            });
        }

        if (quickCategoryForm) {
            quickCategoryForm.addEventListener('submit', async function (e) {
                e.preventDefault();
                const id = quickCategoryId.value;
                const nameValue = document.getElementById('quickCategoryName').value.trim();
                const slugValue = nameValue.toLowerCase()
                    .normalize("NFD").replace(/[\u0300-\u036f]/g, "")
                    .replace(/[^a-z0-9\s-]/g, '')
                    .replace(/\s+/g, '-')
                    .replace(/-+/g, '-');

                const payload = {
                    name: nameValue,
                    slug: slugValue,
                    description: document.getElementById('quickCategoryDescription').value.trim(),
                    order_index: parseInt(document.getElementById('quickCategoryOrder').value, 10) || 0,
                    is_active: document.getElementById('quickCategoryActive').checked
                };

                try {
                    const url = id ? '/api/menu/categories/' + id : '/api/menu/categories';
                    const method = id ? 'PUT' : 'POST';
                    const res = await api(url, { method: method, body: JSON.stringify(payload) });
                    if (res.ok) {
                        toast(id ? 'Categoría actualizada.' : 'Categoría creada con éxito.', 'success');
                        categoryFormModal.hidden = true;
                        await cargarYActualizarCategorias();
                        pintarMiniCategorias();
                        if (!id) {
                            const nuevaCat = categoriasCache.find(x => x.slug === slugValue);
                            if (nuevaCat) itemSelect.value = nuevaCat.id;
                        }
                    } else { toast('Error al guardar la categoría.', 'error'); }
                } catch (err) { toast('Error de conexión con el servidor.', 'error'); }
            });
        }

        const closeManageCategories = document.getElementById('closeManageCategories');
        if (closeManageCategories) closeManageCategories.addEventListener('click', () => manageCategoriesModal.hidden = true);
        const closeManageCategoriesBtn = document.getElementById('closeManageCategoriesBtn');
        if (closeManageCategoriesBtn) closeManageCategoriesBtn.addEventListener('click', () => manageCategoriesModal.hidden = true);
        const closeManageModalBtn = document.getElementById('closeManageModalBtn');
        if (closeManageModalBtn) closeManageModalBtn.addEventListener('click', () => manageCategoriesModal.hidden = true);
        const closeCategoryForm = document.getElementById('closeCategoryForm');
        if (closeCategoryForm) closeCategoryForm.addEventListener('click', () => categoryFormModal.hidden = true);
        const closeCategoryFormBtn = document.getElementById('closeCategoryFormBtn');
        if (closeCategoryFormBtn) closeCategoryFormBtn.addEventListener('click', () => categoryFormModal.hidden = true);
        const cancelQuickCategoryBtn = document.getElementById('cancelQuickCategoryBtn');
        if (cancelQuickCategoryBtn) cancelQuickCategoryBtn.addEventListener('click', () => categoryFormModal.hidden = true);

        if (fileInput) {
            fileInput.addEventListener('change', function (e) {
                const file = e.target.files[0];
                if (file) {
                    const reader = new FileReader();
                    reader.onloadend = function () { document.getElementById('itemImage').value = reader.result; };
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

        const adminSearchInput = document.getElementById('adminSearchInput');
        if (adminSearchInput) {
            adminSearchInput.addEventListener('input', function (e) {
                const termino = e.target.value.toLowerCase().trim();
                if (!termino) { pintarMenu(itemsCache); return; }
                const filtrados = itemsCache.filter(function (item) {
                    return item.name.toLowerCase().includes(termino) || (item.description && item.description.toLowerCase().includes(termino));
                });
                pintarMenu(filtrados);
            });
        }

        newBtn.addEventListener('click', function () { abrirModalItem(null); });

        document.getElementById('menuTable').addEventListener('click', function (e) {
            const btn = e.target.closest('[data-action]');
            if (!btn) return;
            const id = parseInt(btn.dataset.id, 10);
            if (btn.dataset.action === 'edit') abrirModalItem(id);
            else if (btn.dataset.action === 'delete') {
                itemABorrar = id;
                const item = itemsCache.find(function (x) { return x.id === id; });
                document.getElementById('confirmText').textContent = '¿Seguro que quieres eliminar "' + (item ? item.name : 'este plato') + '"?';
                confirmModal.hidden = false;
            }
        });

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

        form.addEventListener('submit', async function (e) {
            e.preventDefault();
            const id = document.getElementById('itemId').value;
            const base64Image = document.getElementById('itemImage').value;

            const payload = {
                name: document.getElementById('itemName').value.trim(),
                category_id: parseInt(document.getElementById('itemCategory').value, 10),
                description: document.getElementById('itemDescription').value.trim(),
                price: parseFloat(document.getElementById('itemPrice').value),
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
                } else { toast('No se pudo guardar el plato.', 'error'); }
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

    // ---------------------------------------------------------
    // GESTIÓN DE PEDIDOS (Take Away & Delivery)
    // ---------------------------------------------------------
    let pedidosCache = [];
    let ordersPollInterval = null; // <- Guardamos la referencia del intervalo

    async function initOrders() {
        if (!initLayout('pedidos')) return;

        const orderSearchInput = document.getElementById('orderSearchInput');
        const typeFilter = document.getElementById('typeFilter');
        const statusFilter = document.getElementById('statusFilter');

        async function cargar() {
            try {
                const res = await api('/api/orders');
                if (res.ok) {
                    pedidosCache = await res.json();
                    aplicarFiltros();

                    // === 1. EFECTO WHATSAPP: Limpiar el badge lateral inmediatamente ===
                    if (pedidosCache.length > 0) {
                        const maxId = Math.max(...pedidosCache.map(p => p.id));
                        localStorage.setItem('koi_last_seen_order_id', maxId);

                        const badgeLateral = document.getElementById('order-badge');
                        if (badgeLateral) badgeLateral.hidden = true;
                    }

                    // === 2. CONTADOR INTERNO: Calcular carga de trabajo en cocina ===
                    const workloadCounter = document.getElementById('ordersWorkloadCounter');
                    if (workloadCounter) {
                        // Contamos los pedidos que requieren acción (Pendientes o En preparación)
                        const activos = pedidosCache.filter(p => p.status === 'pending' || p.status === 'preparing').length;

                        if (activos > 0) {
                            workloadCounter.textContent = `${activos} PEDIDOS PENDIENTES`;
                            workloadCounter.style.display = 'inline-block';
                        } else {
                            workloadCounter.style.display = 'none';
                        }
                    }

                } else { throw new Error(); }
            } catch (err) {
                document.getElementById('ordersTable').innerHTML = `
                    <tr><td colspan="7" class="table-empty" style="color: var(--color-red-light);">Error al cargar los pedidos.</td></tr>
                `;
            }
        }

        function aplicarFiltros() {
            const texto = orderSearchInput.value.toLowerCase().trim();
            const tipo = typeFilter.value;
            const estado = statusFilter.value;

            const filtrados = pedidosCache.filter(p => {
                const cumpleTexto = p.customer_name.toLowerCase().includes(texto) ||
                    p.customer_email.toLowerCase().includes(texto) ||
                    p.customer_phone.includes(texto) ||
                    String(p.id).includes(texto);
                const cumpleTipo = !tipo || p.order_type === tipo;
                const cumpleEstado = !estado || p.status === estado;

                return cumpleTexto && cumpleTipo && cumpleEstado;
            });

            pintarPedidos(filtrados);
        }

        orderSearchInput.addEventListener('input', aplicarFiltros);
        typeFilter.addEventListener('change', aplicarFiltros);
        statusFilter.addEventListener('change', aplicarFiltros);

        document.getElementById('ordersTable').addEventListener('click', function (e) {
            const btn = e.target.closest('[data-id]');
            if (!btn) return;
            const id = parseInt(btn.dataset.id, 10);
            verDetallePedido(id);
        });

        document.getElementById('orderUpdateForm').addEventListener('submit', async function (e) {
            e.preventDefault();
            const id = document.getElementById('updateOrderId').value;
            const status = document.getElementById('updateStatus').value;
            const payment_status = document.getElementById('updatePaymentStatus').value;

            try {
                const response = await api(`/api/orders/${id}`, {
                    method: 'PUT',
                    body: JSON.stringify({ status, payment_status })
                });

                if (response.ok) {
                    toast('Pedido actualizado con éxito.', 'success');
                    document.getElementById('orderDetailModal').hidden = true;
                    cargar();
                } else { throw new Error(); }
            } catch (error) { toast('Error al guardar los cambios del pedido.', 'error'); }
        });

        const cerrarModal = () => { document.getElementById('orderDetailModal').hidden = true; };
        document.getElementById('closeDetailBtn').addEventListener('click', cerrarModal);
        document.getElementById('closeDetailBackdrop').addEventListener('click', cerrarModal);

        // Carga inicial obligatoria al abrir la vista
        cargar();
        actualizarBadgePedidos();

        // --- NUEVO: SHORT POLLING ---
        // Limpiamos cualquier intervalo previo activo por seguridad
        if (ordersPollInterval) clearInterval(ordersPollInterval);

        // Configuramos la actualización automática cada 15 segundos (15000 ms)
        ordersPollInterval = setInterval(function () {
            // Solo hacemos la petición si el modal de edición no está visible,
            // evitando que la lista se refresque e interrumpa al administrador si está editando.
            const modalDetalle = document.getElementById('orderDetailModal');
            if (!modalDetalle || modalDetalle.hidden) {
                cargar();
            }
        }, 15000);
    }

    // ---------------------------------------------------------
    // CONTADOR DE NOTIFICACIONES GLOBAL (BADGE)
    // ---------------------------------------------------------

    async function actualizarBadgePedidos() {
        const badge = document.getElementById('order-badge');
        if (!badge) return;

        try {
            const res = await api('/api/orders');
            if (res.ok) {
                const pedidos = await res.json();

                // Si la API no devuelve ningún pedido en absoluto, ocultamos y salimos
                if (pedidos.length === 0) {
                    badge.hidden = true;
                    badge.style.display = 'none'; // Aseguramos por CSS que se oculte
                    return;
                }

                // Conseguimos el ID del pedido más nuevo que existe en el servidor
                const maxId = Math.max(...pedidos.map(p => p.id));

                // COMPROBACIÓN: ¿El administrador está actualmente dentro de la pantalla de Pedidos?
                const enPantallaPedidos = document.getElementById('ordersTable') !== null;

                if (enPantallaPedidos) {
                    // Si ya está dentro, marcamos automáticamente el último ID como "visto"
                    localStorage.setItem('koi_last_seen_order_id', maxId);
                    badge.hidden = true;
                    badge.style.display = 'none'; // Ocultar círculo rojo del menú lateral
                } else {
                    // Si está en otra pantalla (ej. Reservas), leemos el último ID que llegó a ver
                    const lastSeenId = parseInt(localStorage.getItem('koi_last_seen_order_id') || '0', 10);

                    // Contamos cuántos pedidos nuevos hay con un ID mayor al guardado
                    const pedidosNuevos = pedidos.filter(p => p.id > lastSeenId).length;

                    // CORRECCIÓN AQUÍ: Solo se muestra si estrictamente hay más de 0 novedades
                    if (pedidosNuevos > 0) {
                        badge.textContent = pedidosNuevos;
                        badge.hidden = false;
                        badge.style.display = 'inline-flex'; // O el display que uses en tu CSS para el círculo
                    } else {
                        // Si el resultado es 0, lo fulminamos de la vista
                        badge.hidden = true;
                        badge.style.display = 'none';
                    }
                }
            }
        } catch (err) {
            console.error("Error en el badge de notificaciones:", err);
        }
    }

    // Iniciar el polling global del badge cuando cargue el panel de administración
    document.addEventListener('DOMContentLoaded', () => {
        // Primera carga inmediata
        actualizarBadgePedidos();

        // Comprobar cada 15 segundos si hay pedidos nuevos
        setInterval(actualizarBadgePedidos, 15000);
    });

    function pintarPedidos(pedidos) {
        const tbody = document.getElementById('ordersTable');
        if (pedidos.length === 0) {
            tbody.innerHTML = `<tr><td colspan="8" class="table-empty">No hay pedidos registrados</td></tr>`;
            return;
        }

        tbody.innerHTML = pedidos.map(p => {
            const badgePagoMap = {
                'unpaid': 'badge--cancelled', // Rojo
                'paid': 'badge--confirmed',   // Verde
                'refunded': 'badge--refunded'  // Gris oscuro
            };
            const badgePago = badgePagoMap[p.payment_status] || 'badge--pending';

            const badgeStatusMap = {
                'pending': 'badge--pending',
                'preparing': 'badge--preparing',
                'ready': 'badge--ready',
                'out_for_delivery': 'badge--out_for_delivery',
                'delivered': 'badge--confirmed',
                'cancelled': 'badge--cancelled'
            };
            const badgeStatus = badgeStatusMap[p.status] || 'badge--info';

            const textosTraducciones = {
                'pending': 'PENDIENTE',
                'preparing': 'EN COCINA',
                'ready': 'LISTO',
                'out_for_delivery': 'EN REPARTO',
                'delivered': 'ENTREGADO',
                'cancelled': 'CANCELADO',
                'unpaid': 'NO PAGADO',
                'paid': 'PAGADO',
                'refunded': 'REEMBOLSADO',
            };

            // --- NUEVO: Estilos y textos para el método de pago ---
            // --- CORRECCIÓN: Comprobación robusta del método de pago ---
            // Validamos si viene como 'online', o si se procesó a través de Stripe (session_id)
            const esOnline = p.payment_method === 'online' ||
                p.payment_type === 'online' ||
                (p.stripe_session_id && p.stripe_session_id !== '');

            const textoMetodo = esOnline ? 'PAGO ONLINE' : 'PAGO EN MANO';
            const estiloMetodo = esOnline
                ? 'background-color: #635bff65; color: #ffffff;' // Morado Stripe
                : 'background-color: #2e7d329d; color: #ffffff;' // Verde Efectivo

            return `
                <tr>
                    <td class="cell-strong">#${p.id}</td>
                    <td style="text-align: left;">
                        <div class="cell-strong">${esc(p.customer_name)}</div>
                        <div class="cell-muted">${esc(p.customer_phone)}</div>
                    </td>
                    <td>
                        <span class="badge ${p.order_type === 'takeaway' ? 'badge--completed' : 'badge--info'}" style="background-color: ${p.order_type === 'takeaway' ? '#1c223a' : '#143d24'}">
                            ${p.order_type === 'takeaway' ? 'Para Recoger' : 'A Domicilio'}
                        </span>
                    </td>
                    <td class="cell-strong">${precio(p.total)}</td>
                    <!-- --- NUEVO: Columna del método empleado --- -->
                    <td>
                        <span class="badge" style="font-size: 0.75rem; padding: 0.2rem 0.5rem; ${estiloMetodo}">
                            ${textoMetodo}
                        </span>
                    </td>
                    <td><span class="badge ${badgePago}">${textosTraducciones[p.payment_status] || p.payment_status.toUpperCase()}</span></td>
                    <td><span class="badge ${badgeStatus}">${textosTraducciones[p.status] || p.status.toUpperCase()}</span></td>
                    <td>
                        <div class="row-actions">
                            <button class="btn-admin btn-admin--gold btn-admin--sm" data-id="${p.id}">Detalle</button>
                        </div>
                    </td>
                </tr>
            `;
        }).join('');
    }

    function verDetallePedido(id) {
        const p = pedidosCache.find(item => item.id === id);
        if (!p) return;

        const textosTipos = { 'takeaway': 'Para Recoger (Take Away)', 'delivery': 'A Domicilio' };

        const textosMetodos = { 'online': 'Tarjeta de Crédito (Online - Stripe)', 'cash_card': 'Pago en mano (Efectivo / Tarjeta al repartidor o local)' };

        document.getElementById('detId').textContent = p.id;
        document.getElementById('detName').textContent = p.customer_name;
        document.getElementById('detPhone').textContent = p.customer_phone;
        document.getElementById('detEmail').textContent = p.customer_email;
        document.getElementById('detType').textContent = textosTipos[p.order_type] || p.order_type;

        // --- Si tienes un elemento 'detPaymentMethod' en tu HTML, lo rellenamos: ---
        const detMetodoEl = document.getElementById('detPaymentMethod');
        if (detMetodoEl) {
            detMetodoEl.textContent = textosMetodos[p.payment_method] || p.payment_method;
        }

        document.getElementById('detNotes').textContent = p.notes || 'Sin comentarios adicionales.';

        const addressRow = document.getElementById('detAddressRow');
        if (p.order_type === 'delivery') {
            addressRow.style.display = 'block';
            document.getElementById('detAddress').textContent = p.address || 'No especificada';
        } else {
            addressRow.style.display = 'none';
        }

        const itemsTbody = document.getElementById('detItemsTable');
        itemsTbody.innerHTML = p.items.map(it => `
            <tr>
                <td style="text-align: left;" class="cell-strong">${esc(it.name)}</td>
                <td>${precio(it.unit_price)}</td>
                <td>${it.quantity}</td>
                <td class="cell-strong">${precio(it.unit_price * it.quantity)}</td>
            </tr>
        `).join('');

        document.getElementById('updateOrderId').value = p.id;
        document.getElementById('updateStatus').value = p.status;
        document.getElementById('updatePaymentStatus').value = p.payment_status;

        document.getElementById('orderDetailModal').hidden = false;
    }

    return {
        initLogin: initLogin,
        initDashboard: initDashboard,
        initReservations: initReservations,
        initMenu: initMenu,
        initOrders: initOrders
    };
})();