/* ============================================================
   KOI · Menú dinámico + Carrito de compras + Pago con Stripe
   ============================================================ */
(function () {
    'use strict';

    const grid = document.getElementById('menuGrid');
    const tabs = document.getElementById('menuTabs');
    const spinner = document.getElementById('menuSpinner');
    const empty = document.getElementById('menuEmpty');
    const searchInput = document.getElementById('menuSearch');

    if (!grid) return;

    let todosLosItems = [];
    let categoriaActiva = '';
    let terminoBusqueda = '';

    const DELIVERY_FEE = 3.50;      // debe coincidir con settings.DELIVERY_FEE
    const CART_KEY = 'koi_cart';    // clave de localStorage

    // ---------------------------------------------------------------
    // Utilidades
    // ---------------------------------------------------------------
    function formatearPrecio(p) {
        return Number(p).toFixed(2).replace('.', ',') + ' €';
    }

    function escapar(texto) {
        const div = document.createElement('div');
        div.textContent = texto == null ? '' : texto;
        return div.innerHTML;
    }

    // ---------------------------------------------------------------
    // Estado del carrito (persistido en localStorage)
    // ---------------------------------------------------------------
    function leerCarrito() {
        try {
            return JSON.parse(localStorage.getItem(CART_KEY)) || [];
        } catch (e) {
            return [];
        }
    }

    function guardarCarrito(carrito) {
        localStorage.setItem(CART_KEY, JSON.stringify(carrito));
    }

    let carrito = leerCarrito();
    let tipoPedido = 'delivery';

    function totalUnidades() {
        return carrito.reduce(function (acc, l) { return acc + l.quantity; }, 0);
    }

    function calcularSubtotal() {
        return carrito.reduce(function (acc, l) {
            return acc + l.price * l.quantity;
        }, 0);
    }

    function envioActual() {
        return tipoPedido === 'delivery' ? DELIVERY_FEE : 0;
    }

    // ---------------------------------------------------------------
    // Añadir / modificar / eliminar
    // ---------------------------------------------------------------
    function anadirAlCarrito(item) {
        const existente = carrito.find(function (l) { return l.menu_item_id === item.id; });
        if (existente) {
            existente.quantity += 1;
        } else {
            carrito.push({
                menu_item_id: item.id,
                name: item.name,
                price: item.price,
                quantity: 1
            });
        }
        guardarCarrito(carrito);
        renderCarrito();
    }

    function cambiarCantidad(id, delta) {
        const linea = carrito.find(function (l) { return l.menu_item_id === id; });
        if (!linea) return;
        linea.quantity += delta;
        if (linea.quantity <= 0) {
            carrito = carrito.filter(function (l) { return l.menu_item_id !== id; });
        }
        guardarCarrito(carrito);
        renderCarrito();
    }

    function eliminarLinea(id) {
        carrito = carrito.filter(function (l) { return l.menu_item_id !== id; });
        guardarCarrito(carrito);
        renderCarrito();
    }

    // ---------------------------------------------------------------
    // Card de plato
    // ---------------------------------------------------------------
    function crearCard(item, indice) {
        const card = document.createElement('article');
        card.className = 'dish-card' + (item.is_available ? '' : ' is-unavailable');
        card.style.animationDelay = (indice * 0.05) + 's';

        const imgClase = item.image_url ? 'dish-card__img has-img' : 'dish-card__img';
        const estiloImg = item.image_url ? ` style="background-image:url('${escapar(item.image_url)}')"` : '';

        const botonAnadir = item.is_available
            ? `<button class="dish-add-btn" data-id="${item.id}">Añadir</button>`
            : '';

        card.innerHTML =
            `<div class="${imgClase}"${estiloImg}>` +
            (item.is_featured ? '<span class="dish-badge">Destacado</span>' : '') +
            (item.is_available ? '' : '<span class="dish-unavailable-tag">No disponible</span>') +
            `</div>` +
            `<div class="dish-card__body">` +
            `<div class="dish-card__head">` +
            `<h3 class="dish-card__name">${escapar(item.name)}</h3>` +
            `<span class="dish-card__price">${formatearPrecio(item.price)}</span>` +
            `</div>` +
            `<p class="dish-card__desc">${escapar(item.description || '')}</p>` +
            `<div class="dish-card__foot">` +
            (item.category_name ? `<span class="dish-card__cat">${escapar(item.category_name)}</span>` : '<span></span>') +
            botonAnadir +
            `</div>` +
            `</div>`;
        return card;
    }

    // ---------------------------------------------------------------
    // Filtrado y pintado del grid
    // ---------------------------------------------------------------
    function render() {
        const termino = terminoBusqueda.trim().toLowerCase();
        const filtrados = todosLosItems.filter(function (item) {
            const coincideCat = !categoriaActiva || item.category_slug === categoriaActiva;
            const coincideTexto = !termino ||
                item.name.toLowerCase().includes(termino) ||
                (item.description || '').toLowerCase().includes(termino);
            return coincideCat && coincideTexto;
        });

        grid.innerHTML = '';
        if (filtrados.length === 0) {
            empty.hidden = false;
        } else {
            empty.hidden = true;
            filtrados.forEach(function (item, i) { grid.appendChild(crearCard(item, i)); });
        }
    }

    // Delegación de eventos para el botón "Añadir" con ANIMACIONES
    grid.addEventListener('click', function (e) {
        const btn = e.target.closest('.dish-add-btn');
        const fab = document.getElementById('cartFab'); // Obtenemos el FAB flotante

        if (!btn) return;

        // Evitar múltiples clics rápidos mientras dura la animación
        if (btn.classList.contains('is-success')) return;

        const id = parseInt(btn.dataset.id, 10);
        const item = todosLosItems.find(function (i) { return i.id === id; });

        if (item) {
            // 1. Ejecutar la lógica de negocio (añadir a localStorage)
            anadirAlCarrito(item);

            // 2. Feedback visual en el PROPIO BOTÓN
            const textoOriginal = btn.textContent;
            btn.textContent = '✓ Añadido';
            btn.classList.add('is-success'); // Activamos animación CSS

            // 3. Feedback visual en el BOTÓN FLOTANTE (FAB)
            if (fab) {
                // Quitamos la clase por si acaso ya estaba (para reiniciar la animación)
                fab.classList.remove('is-adding');
                // Forzamos un "reflow" para que el navegador reinicie la animación
                void fab.offsetWidth;
                // Añadimos la clase para que vibre
                fab.classList.add('is-adding');
            }

            // 4. Limpieza tras la animación (volver al estado original)
            setTimeout(function () {
                btn.textContent = textoOriginal;
                btn.classList.remove('is-success');
                if (fab) fab.classList.remove('is-adding');
            }, 900); // Duración ligeramente superior a la animación CSS
        }
    });

    // ---------------------------------------------------------------
    // Tabs de categorías
    // ---------------------------------------------------------------
    function pintarTabs(categorias) {
        categorias.forEach(function (cat) {
            const btn = document.createElement('button');
            btn.className = 'menu-tab';
            btn.dataset.slug = cat.slug;
            btn.textContent = cat.name;
            tabs.appendChild(btn);
        });

        tabs.addEventListener('click', function (e) {
            const btn = e.target.closest('.menu-tab');
            if (!btn) return;
            tabs.querySelectorAll('.menu-tab').forEach(function (t) { t.classList.remove('is-active'); });
            btn.classList.add('is-active');
            categoriaActiva = btn.dataset.slug;
            render();
        });
    }

    function debounce(fn, ms) {
        let t;
        return function () {
            clearTimeout(t);
            const args = arguments;
            t = setTimeout(function () { fn.apply(null, args); }, ms);
        };
    }

    if (searchInput) {
        searchInput.addEventListener('input', debounce(function (e) {
            terminoBusqueda = e.target.value;
            render();
        }, 250));
    }

    // ===============================================================
    //  CARRITO — elementos del DOM
    // ===============================================================
    const fab = document.getElementById('cartFab');
    const count = document.getElementById('cartCount');
    const drawer = document.getElementById('cartDrawer');
    const overlay = document.getElementById('cartOverlay');
    const closeBtn = document.getElementById('cartClose');
    const itemsBox = document.getElementById('cartItems');
    const emptyBox = document.getElementById('cartEmpty');
    const summary = document.getElementById('cartSummary');
    const sumSubtotal = document.getElementById('sumSubtotal');
    const sumDelivery = document.getElementById('sumDelivery');
    const sumDeliveryRow = document.getElementById('sumDeliveryRow');
    const sumTotal = document.getElementById('sumTotal');
    const checkoutBtn = document.getElementById('cartCheckoutBtn');
    const cartTypeBox = document.getElementById('cartType');

    function abrirCarrito() {
        drawer.classList.add('is-open');
        overlay.hidden = false;
        drawer.setAttribute('aria-hidden', 'false');
    }

    function cerrarCarrito() {
        drawer.classList.remove('is-open');
        overlay.hidden = true;
        drawer.setAttribute('aria-hidden', 'true');
    }

    function renderCarrito() {
        // Contador del botón flotante
        const unidades = totalUnidades();
        count.textContent = unidades;
        count.classList.toggle('is-visible', unidades > 0);

        // Lista de líneas
        itemsBox.innerHTML = '';
        if (carrito.length === 0) {
            emptyBox.style.display = 'flex';
            summary.hidden = true;
            return;
        }
        emptyBox.style.display = 'none';
        summary.hidden = false;

        carrito.forEach(function (l) {
            const fila = document.createElement('div');
            fila.className = 'cart-line';
            fila.innerHTML =
                `<div class="cart-line__info">` +
                `<span class="cart-line__name">${escapar(l.name)}</span>` +
                `<span class="cart-line__price">${formatearPrecio(l.price)}</span>` +
                `</div>` +
                `<div class="cart-line__qty">` +
                `<button class="qty-btn" data-act="dec" data-id="${l.menu_item_id}">−</button>` +
                `<span>${l.quantity}</span>` +
                `<button class="qty-btn" data-act="inc" data-id="${l.menu_item_id}">+</button>` +
                `</div>` +
                `<span class="cart-line__subtotal">${formatearPrecio(l.price * l.quantity)}</span>` +
                `<button class="cart-line__remove" data-act="del" data-id="${l.menu_item_id}" aria-label="Eliminar">&times;</button>`;
            itemsBox.appendChild(fila);
        });

        // Totales
        const subtotal = calcularSubtotal();
        const envio = envioActual();
        sumSubtotal.textContent = formatearPrecio(subtotal);
        sumDelivery.textContent = formatearPrecio(envio);
        sumDeliveryRow.style.display = tipoPedido === 'delivery' ? 'flex' : 'none';
        sumTotal.textContent = formatearPrecio(subtotal + envio);
    }

    // Eventos de las líneas del carrito
    itemsBox.addEventListener('click', function (e) {
        const btn = e.target.closest('[data-act]');
        if (!btn) return;
        const id = parseInt(btn.dataset.id, 10);
        const act = btn.dataset.act;
        if (act === 'inc') cambiarCantidad(id, 1);
        else if (act === 'dec') cambiarCantidad(id, -1);
        else if (act === 'del') eliminarLinea(id);
    });

    // Selector de tipo de pedido
    cartTypeBox.addEventListener('click', function (e) {
        const btn = e.target.closest('.cart-type__btn');
        if (!btn) return;
        cartTypeBox.querySelectorAll('.cart-type__btn').forEach(function (b) { b.classList.remove('is-active'); });
        btn.classList.add('is-active');
        tipoPedido = btn.dataset.type;
        renderCarrito();
    });

    fab.addEventListener('click', abrirCarrito);
    closeBtn.addEventListener('click', cerrarCarrito);
    overlay.addEventListener('click', cerrarCarrito);

    // ===============================================================
    //  CHECKOUT — modal de datos + pago con Stripe
    // ===============================================================
    const ckOverlay = document.getElementById('checkoutOverlay');
    const ckClose = document.getElementById('checkoutClose');
    const ckForm = document.getElementById('checkoutForm');
    const ckAddressField = document.getElementById('ckAddressField');
    const ckAddress = document.getElementById('ckAddress');
    const ckMessage = document.getElementById('checkoutMessage');
    const ckSubmit = document.getElementById('checkoutSubmit');
    const ckTotal = document.getElementById('checkoutTotal');

    function abrirCheckout() {
        if (carrito.length === 0) return;
        // Mostrar/ocultar dirección según el tipo de pedido
        ckAddressField.style.display = tipoPedido === 'delivery' ? 'flex' : 'none';
        ckAddress.required = tipoPedido === 'delivery';
        ckTotal.textContent = formatearPrecio(calcularSubtotal() + envioActual());
        ckMessage.hidden = true;
        ckOverlay.hidden = false;

        // --- NUEVO: Resetear método de pago al abrir el modal ---
        const onlineRadio = document.querySelector('input[name="payment_method"][value="online"]');
        if (onlineRadio) {
            onlineRadio.checked = true;
            // Forzamos manualmente el evento para actualizar textos y Stripe
            const event = new Event('change', { bubbles: true });
            onlineRadio.dispatchEvent(event);
        }
    }

    function cerrarCheckout() {
        ckOverlay.hidden = true;
    }

    checkoutBtn.addEventListener('click', abrirCheckout);
    ckClose.addEventListener('click', cerrarCheckout);
    ckOverlay.addEventListener('click', function (e) {
        if (e.target === ckOverlay) cerrarCheckout();
    });

    // --- NUEVO: Escuchador para cambiar textos según el método de pago ---
    const ckFormElement = document.getElementById('checkoutForm');
    if (ckFormElement) {
        ckFormElement.addEventListener('change', function (e) {
            const radio = e.target.closest('input[name="payment_method"]');
            if (!radio) return;

            const buttonText = document.getElementById('ckButtonText');
            const secureNotice = document.getElementById('checkoutSecureNotice');

            if (radio.value === 'cash_card') {
                if (buttonText) buttonText.textContent = 'Confirmar pedido';
                if (secureNotice) secureNotice.hidden = true;
            } else {
                if (buttonText) buttonText.textContent = 'Pagar';
                if (secureNotice) secureNotice.hidden = false;
            }
        });
    }

    function mostrarMensaje(texto, esError) {
        ckMessage.hidden = false;
        ckMessage.textContent = texto;
        ckMessage.className = 'checkout-message ' + (esError ? 'is-error' : 'is-ok');
    }

    ckForm.addEventListener('submit', async function (e) {
        e.preventDefault();
        if (carrito.length === 0) return;

        const nombre = ckForm.customer_name.value.trim();
        const telefono = ckForm.customer_phone.value.trim();
        const email = ckForm.customer_email.value.trim();
        const direccion = ckAddress.value.trim();

        // --- NUEVO: Capturar método de pago ---
        const metodoPago = ckForm.payment_method.value;

        // Validación básica en cliente
        if (nombre.length < 2) return mostrarMensaje('Introduce tu nombre completo.', true);
        if (telefono.length < 6) return mostrarMensaje('Introduce un teléfono válido.', true);
        if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) return mostrarMensaje('Introduce un email válido.', true);
        if (tipoPedido === 'delivery' && !direccion) {
            return mostrarMensaje('La dirección es obligatoria para pedidos a domicilio.', true);
        }

        const payload = {
            customer_name: nombre,
            customer_phone: telefono,
            customer_email: email,
            order_type: tipoPedido,
            address: tipoPedido === 'delivery' ? direccion : null,
            notes: ckForm.notes.value.trim() || null,
            payment_method: metodoPago, // --- NUEVO: Enviado al backend ---
            items: carrito.map(function (l) {
                return { menu_item_id: l.menu_item_id, quantity: l.quantity };
            })
        };

        ckSubmit.disabled = true;

        // --- NUEVO: Texto de carga condicional ---
        if (metodoPago === 'cash_card') {
            ckSubmit.innerHTML = 'Procesando pedido…';
        } else {
            ckSubmit.innerHTML = 'Redirigiendo al pago…';
        }

        try {
            const res = await fetch('/api/orders/checkout', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await res.json();

            if (!res.ok) {
                throw new Error(data.detail || 'No se ha podido crear el pedido.');
            }

            // Vaciar el carrito antes de redirigir o ir al éxito
            localStorage.removeItem(CART_KEY);

            // --- NUEVO: Redirección condicional según la respuesta de tu backend ---
            // Si el backend procesa efectivo, te devolverá directamente una página de éxito local
            window.location.href = data.checkout_url || '/orders/success';
        } catch (err) {
            mostrarMensaje(err.message, true);
            ckSubmit.disabled = false;

            // --- NUEVO: Restaurar con el formato estructurado de spans ---
            const textoOriginal = metodoPago === 'cash_card' ? 'Confirmar pedido' : 'Pagar';
            ckSubmit.innerHTML = `<span id="ckButtonText">${textoOriginal}</span> <span id="checkoutTotal">${formatearPrecio(calcularSubtotal() + envioActual())}</span>`;
        }
    });
    // ---------------------------------------------------------------
    // Carga inicial desde la API
    // ---------------------------------------------------------------
    async function cargar() {
        try {
            const [resCats, resItems] = await Promise.all([
                fetch('/api/menu/categories'),
                fetch('/api/menu/items')
            ]);
            if (!resCats.ok || !resItems.ok) throw new Error('Error de red');

            const categorias = await resCats.json();
            todosLosItems = await resItems.json();

            pintarTabs(categorias);
            spinner.style.display = 'none';
            render();
            renderCarrito();
        } catch (err) {
            spinner.innerHTML = '<p>No se ha podido cargar la carta. Inténtalo de nuevo más tarde.</p>';
            console.error('Error cargando el menú:', err);
        }
    }

    cargar();
})();
