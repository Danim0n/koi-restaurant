/* ============================================================
   KOI · Formulario de reservas
   ============================================================ */
(function () {
    'use strict';

    const form = document.getElementById('reservationForm');
    if (!form) return;

    const dateInput = document.getElementById('date');
    const timeSelect = document.getElementById('time');
    const submitBtn = document.getElementById('submitBtn');
    const formMessage = document.getElementById('formMessage');

    // ---- Fecha mínima = hoy ----
    const hoy = new Date();
    const hoyStr = hoy.toISOString().split('T')[0];
    dateInput.min = hoyStr;
    dateInput.value = hoyStr;

    // ---- Generar franjas horarias (13:00 – 22:30 cada 30 min) ----
    (function generarHoras() {
        for (let h = 13; h <= 22; h++) {
            ['00', '30'].forEach(function (m) {
                const valor = String(h).padStart(2, '0') + ':' + m;
                const opt = document.createElement('option');
                opt.value = valor;
                opt.textContent = valor;
                timeSelect.appendChild(opt);
            });
        }
    })();

    // ---- Validadores ----
    const validadores = {
        customer_name: function (v) {
            if (!v.trim()) return 'El nombre es obligatorio.';
            if (v.trim().length < 2) return 'Introduce un nombre válido.';
            return '';
        },
        customer_phone: function (v) {
            if (!v.trim()) return 'El teléfono es obligatorio.';
            if (!/^[+]?[\d\s()-]{6,20}$/.test(v.trim())) return 'Introduce un teléfono válido.';
            return '';
        },
        customer_email: function (v) {
            if (!v.trim()) return 'El correo es obligatorio.';
            if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v.trim())) return 'Introduce un correo válido.';
            return '';
        },
        date: function (v) {
            if (!v) return 'Selecciona una fecha.';
            if (v < hoyStr) return 'La fecha no puede ser anterior a hoy.';
            return '';
        },
        time: function (v) { return v ? '' : 'Selecciona una hora.'; },
        guests: function (v) { return v ? '' : 'Indica el número de comensales.'; }
    };

    function campoPorNombre(nombre) { return form.querySelector('[name="' + nombre + '"]'); }
    function errorSpan(id) { return form.querySelector('.form-error[data-for="' + id + '"]'); }

    function validarCampo(nombre) {
        const validador = validadores[nombre];
        if (!validador) return true;
        const input = campoPorNombre(nombre);
        const mensaje = validador(input.value);
        const span = errorSpan(input.id);
        if (mensaje) {
            input.classList.add('is-invalid');
            if (span) span.textContent = mensaje;
            return false;
        }
        input.classList.remove('is-invalid');
        if (span) span.textContent = '';
        return true;
    }

    // Validación en tiempo real
    ['customer_name', 'customer_phone', 'customer_email', 'date', 'time', 'guests'].forEach(function (nombre) {
        const input = campoPorNombre(nombre);
        if (!input) return;
        input.addEventListener('blur', function () { validarCampo(nombre); });
        input.addEventListener('input', function () {
            if (input.classList.contains('is-invalid')) validarCampo(nombre);
        });
    });

    function mostrarMensaje(texto, tipo) {
        formMessage.hidden = false;
        formMessage.textContent = texto;
        formMessage.className = 'form-message form-message--' + tipo;
        formMessage.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    // ---- Envío ----
    form.addEventListener('submit', async function (e) {
        e.preventDefault();
        formMessage.hidden = true;

        const nombres = ['customer_name', 'customer_phone', 'customer_email', 'date', 'time', 'guests'];
        const todosValidos = nombres.map(validarCampo).every(Boolean);
        if (!todosValidos) {
            mostrarMensaje('Por favor, corrige los campos marcados en rojo.', 'error');
            return;
        }

        const datos = {
            customer_name: campoPorNombre('customer_name').value.trim(),
            customer_phone: campoPorNombre('customer_phone').value.trim(),
            customer_email: campoPorNombre('customer_email').value.trim(),
            date: campoPorNombre('date').value,
            time: campoPorNombre('time').value,
            guests: parseInt(campoPorNombre('guests').value, 10),
            special_requests: (campoPorNombre('special_requests').value || '').trim() || null
        };

        submitBtn.disabled = true;
        submitBtn.textContent = 'Enviando…';

        try {
            const res = await fetch('/api/reservations', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(datos)
            });

            if (res.ok) {
                const reserva = await res.json();
                mostrarMensaje(
                    '¡Gracias, ' + datos.customer_name + '! Tu reserva para ' + datos.guests +
                    ' comensales el ' + datos.date + ' a las ' + datos.time +
                    ' se ha registrado (nº ' + reserva.id + '). Te confirmaremos en breve.',
                    'success'
                );
                form.reset();
                dateInput.value = hoyStr;
            } else {
                let detalle = 'No se ha podido completar la reserva. Inténtalo de nuevo.';
                try {
                    const err = await res.json();
                    if (err.detail) {
                        detalle = typeof err.detail === 'string' ? err.detail : detalle;
                    }
                } catch (_) { /* respuesta sin JSON */ }
                mostrarMensaje(detalle, 'error');
            }
        } catch (err) {
            mostrarMensaje('Error de conexión. Comprueba tu red e inténtalo de nuevo.', 'error');
            console.error('Error al reservar:', err);
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Confirmar reserva';
        }
    });
})();
